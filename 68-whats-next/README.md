# 68 – Thank You + What's Next (series finale)

**Video 68** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg · 🌐 www.nileshtechnology.in

No code in this folder – this is the map of everything we built, and where to go from here.

## The road – 69 videos, 67 project folders
| part | videos | what you can do now |
|---|---|---|
| 1. The basics | 0 – 15 | HTTP and REST, type hints, async/await, path + query parameters, Pydantic models and validators, response models, errors, headers, cookies, forms, files |
| 2. A real project | 16 – 35 | APIRouter, dependency injection, settings, middleware, background tasks, SQLAlchemy, CRUD, relationships, Alembic, advanced queries, transactions, async database, clean architecture |
| 3. Security | 36 – 45 | Argon2 passwords, JWT, the OAuth2 password flow, protected routes, refresh tokens, roles, scopes, email verification + password reset, rate limits and the OWASP API Top 10 |
| 4. Real-time and scale | 46 – 56 | WebSockets and chat rooms, the event loop and the threadpool, streaming + SSE, Redis caching, Celery jobs, API versioning, structured logging, health checks + metrics |
| 5. Production | 57 – 67 | Docker, CI/CD with GitHub Actions, PostgreSQL, migrations in production, Nginx + HTTPS, a cloud VM, deploys from CI, GitHub Container Registry, monitoring + alerts, load testing, off-site backups + secrets |

**The final Course Hub (1.16.0):** 84 tests · 98.97 % coverage · lint + tests + migrations + a smoke test + a secret scan
on every push · one image per commit · Nginx + HTTPS · Prometheus + alerts · a load test that can fail · encrypted,
append-only off-site backups with a weekly restore test.

## How to use this repository
- **Every folder runs on its own** – `cd 23-fastapi-database`, read its README, run it, run its tests.
- **Every video's homework answer** is in that video's folder: `## Homework answer (shown at the start of Video N)`.
- **About 200 interview questions** – 3 at the end of almost every README. Read them before an interview.
- **Compare two folders** to see exactly what a video changed: `diff -r 65-monitoring 66-performance`.
- **Before you go live:** the production checklist in [67-offsite-backups](../67-offsite-backups#the-production-checklist--everything-from-this-course).

## What to learn next
1. **Build your own project** – one idea from start to deployment, with every step from this course.
2. **A managed cloud** – managed PostgreSQL, a container service, a load balancer – instead of one VM.
3. **Kubernetes basics** – when one server is not enough: Deployments, Services, Ingress, probes.
4. **Tracing** – OpenTelemetry: follow one request through the API, the database and Redis.
5. **Messaging** – RabbitMQ or Kafka between services; events instead of direct calls.
6. **System design** – caching, queues, replicas and trade-offs – the interview topic for senior roles.
7. **AI apps with FastAPI** – an LLM behind your API: streaming answers (Video 49), background jobs (Video 52),
   rate limits (Video 45) – you already know the hard parts.

## Coming next on the channel: complete projects, from scratch to deployment
Each project goes the whole way, the same way as this course: the requirement → the design → the database → the API
→ login and roles → tests → Docker → CI/CD → deployment → monitoring and backups.

Ideas – tell me in the comments which one first:
- a **job portal** API – companies, jobs, applications, résumé uploads, email notifications
- an **e-commerce** backend – products, cart, orders, stock, payments
- a **real-time chat** app – WebSockets, rooms, online users, message history
- an **AI assistant** API – an LLM behind FastAPI, streaming answers, usage limits per user

## Thank you
Thank you for watching, coding along, asking questions in the comments, and doing the homework.
🔔 Subscribe to Nilesh Technology – Learn • Code • Build Projects
