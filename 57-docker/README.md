# 57 – FastAPI in Docker: a small, safe image, a health check, a volume and Compose

**Video 57** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project: the same kind of FastAPI app as before – put into a Docker image. First the
Dockerfile most people write (`Dockerfile.naive`) and what is wrong with it, measured; then a good one:
cached dependency layer, multi-stage build, `.dockerignore`, a non-root user, exec-form `CMD`,
a `HEALTHCHECK`, the database on a **volume**, and `compose.yaml`.

## Run it
```bash
cd 57-docker
docker build -t coursehub:1.5.0 .
docker run -d --name api -p 8000:8000 -v coursehub-data:/data coursehub:1.5.0
docker ps                                   # ... (healthy)
curl localhost:8000/health/ready            # {"status":"ready","version":"1.5.0"}
curl localhost:8000/whoami                  # user "app", uid 10001 - not root
docker stop api && docker rm api

docker compose up -d                        # the same, from compose.yaml
docker compose ps
docker compose down

pip install -r requirements-dev.txt && pytest     # the app itself: 4 passed
```

## Project
```
app/  config.py (VERSION, DB_PATH from env) · db.py (SQLite) · main.py (health · whoami · courses)
      healthcheck.py  - what Docker's HEALTHCHECK runs inside the container
Dockerfile        multi-stage · venv · non-root · HEALTHCHECK · exec-form CMD
Dockerfile.naive  the first Dockerfile everybody writes - for comparison
.dockerignore     .git · .venv · __pycache__ · *.db · .env · tests ...
compose.yaml      one service, a port, an env var, a named volume, restart: unless-stopped
requirements.txt  pinned: fastapi 0.156.0 · uvicorn 0.54.0 · pydantic-settings 2.16.1
```

## Naive vs good – measured
These numbers come from my recording machine. Docker Hub was not reachable there, so both images were
built `FROM` a **local base image** (Ubuntu 24.04 minimal + Python 3.12, 208 MB) with
`--build-arg BASE=local/python:3.12-noble`. With the default `python:3.13-slim` your sizes and times will be
different – the *differences* are what matter.

| | `Dockerfile.naive` | `Dockerfile` |
|---|---|---|
| build context sent | **42.71 MB** (no `.dockerignore`: `.venv`, `.git` ...) | **3.36 kB** |
| first build | 14.89 s | 12.62 s |
| rebuild after changing ONE line of code | **12.71 s** (pip install again) | **0.38 s** (deps CACHED) |
| image size | **331.8 MB** | **253.8 MB** |
| files in `/app` | `.git .venv Dockerfile* app compose.yaml coursehub.db tests ...` | `app` |
| runs as | `root`, uid 0 | `app`, uid 10001 |
| PID 1 | `/bin/sh -c ...` (shell form) | `uvicorn` (exec form) |
| `docker stop` | **10.21 s** – SIGTERM ignored, killed (exit 137) | **0.40 s** – graceful |
| health | – | `(health: starting)` → `(healthy)` after ~10 s |

Volume: `POST /courses` → `docker rm api` → a **new** container with `-v coursehub-data:/data` →
`GET /courses` still returns `[{"id":1,"title":"Docker 101"}]`.
A broken `DB_PATH` → the app fails at startup → `Exited (3)` and the reason in `docker logs`.
Compose names things after the project: container `coursehub-api-1`, volume `coursehub_coursehub-data`.

## Rules
- Copy `requirements.txt` and install **before** copying the code – the slow layer stays cached.
- Multi-stage: build in one stage, copy only the virtual environment into the final image.
- A `.dockerignore` – never send `.git`, `.venv`, databases or `.env` secrets into the image.
- Never run as root: `useradd` + `USER app`.
- Exec-form `CMD ["uvicorn", ...]` – the app is PID 1 and gets SIGTERM; shell form waits 10 s and is killed.
- Data that must survive goes on a **volume**; the container itself is disposable.
- Configuration through environment variables; secrets never in the image.
- `HEALTHCHECK` with Python (slim images have no curl), against `/health/ready`.
- Pin your dependency versions, and the base image tag.

## Interview questions
1. **Why copy requirements.txt before the code?** Docker caches every layer. Installing the dependencies from a layer that only depends on `requirements.txt` means a code change only rebuilds the small `COPY app` layer – here 0.38 s instead of 12.71 s.
2. **What is a multi-stage build?** Several `FROM`s in one Dockerfile: a builder stage installs or compiles things, and the final stage copies only the result (here `/opt/venv`), leaving build tools and caches behind – smaller and safer images.
3. **Why should a container not run as root, and why exec-form CMD?** If the app is compromised, root inside the container is much closer to root on the host. Exec form makes your process PID 1, so it receives SIGTERM and shuts down gracefully; with shell form `/bin/sh` gets the signal, ignores it, and Docker kills the app after 10 seconds.

## Homework
1. **A smaller image:** check `docker history`, then add `PIP_NO_COMPILE=1` or remove `__pycache__` – measure the size before and after.
2. **Config via compose:** add `env_file: .env` to `compose.yaml` with `VERSION=1.5.1`, and show that `/health/ready` reports it – without rebuilding the image.
3. A test that `app.healthcheck` exits 0 when the app is ready and 1 when it is not.

Answer at the start of Video 58 (CI/CD with GitHub Actions).
