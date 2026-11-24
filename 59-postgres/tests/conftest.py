# The tests talk to a REAL PostgreSQL:  docker compose up -d db
# Always the TEST database (made by db/init) - the tests empty the table before every test.
import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://coursehub:coursehub-dev@127.0.0.1:5432/coursehub_test")
