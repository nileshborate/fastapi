-- runs ONCE: only when the pgdata volume is still empty (/docker-entrypoint-initdb.d)
CREATE DATABASE coursehub_test;        -- pytest uses this one - never the real data
