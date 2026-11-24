-- Video 66 - 2,000 courses: the test needs a real-sized table. On STAGING - never production!
--   docker compose exec -T db psql -U coursehub coursehub < loadtest/seed.sql
INSERT INTO courses (name, description, level)
SELECT 'Course ' || g,
       repeat('Learn FastAPI step by step. ', 10),
       (ARRAY['beginner', 'intermediate', 'advanced'])[1 + g % 3]
FROM generate_series(1, 2000) AS g;
