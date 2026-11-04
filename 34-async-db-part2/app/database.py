# Async engine + AsyncSession - now with the pool settings
from collections.abc import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.pool_size,           # 5 connections stay open
    max_overflow=settings.max_overflow,     # + up to 10 more when it's busy
    pool_timeout=settings.pool_timeout,     # nothing free after 30 s -> TimeoutError
    pool_pre_ping=True,                     # test a connection before we use it
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,     # after commit: keep the values - reading them needs NO query
)

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# AsyncAttrs: lets us write  await obj.awaitable_attrs.<relationship>
class Base(AsyncAttrs, DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as db:        # closed for us when the request ends
        yield db
