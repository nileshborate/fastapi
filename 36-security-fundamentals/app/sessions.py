# The session store: session id -> username. The SERVER remembers who is logged in.
# (in memory here - in production: Redis or a database table)
SESSIONS: dict[str, str] = {}
