# Alembic's entry point - production rules: our URL, one migrator at a time, short lock waits
import logging
import time
from logging.config import fileConfig

import sqlalchemy as sa
from alembic import context

from app.config import get_settings
from app.tables import metadata

config = context.config
if config.config_file_name and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)
log = logging.getLogger("alembic.env")

settings = get_settings()
# the same DATABASE_URL as the api - SQLAlchemy only needs the driver name: +psycopg
URL = settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
LOCK_KEY = 60_000            # any number - the same for every copy of THIS app's migrator
target_metadata = metadata   # what `alembic check` compares with the database


def run_migrations_offline() -> None:
    """alembic upgrade --sql: print the SQL for a review - nothing is run"""
    context.configure(url=URL, target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = sa.create_engine(URL, poolclass=sa.pool.NullPool)
    with engine.connect() as conn:
        # 1. one migrator at a time: a 2nd copy waits here, then finds nothing to do.
        #    TRY + sleep, never a blocking pg_advisory_lock(): a migrator waiting inside a
        #    transaction deadlocks with CREATE INDEX CONCURRENTLY (it waits for them all)
        try_lock = sa.text("SELECT pg_try_advisory_lock(:k)")
        while not conn.execute(try_lock, {"k": LOCK_KEY}).scalar():
            conn.rollback()                                # hold nothing while we wait
            log.info("another migrator is running - waiting")
            time.sleep(1)
        log.info("got the migration lock")
        # 2. never wait long for a table lock - a waiting ALTER blocks every query behind it
        conn.execute(sa.text("SELECT set_config('lock_timeout', :t, false)"),
                     {"t": settings.migration_lock_timeout})
        conn.commit()
        try:
            context.configure(connection=conn, target_metadata=target_metadata)
            with context.begin_transaction():              # PostgreSQL: DDL is transactional
                context.run_migrations()
        finally:
            conn.rollback()
            conn.execute(sa.text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})
            conn.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
