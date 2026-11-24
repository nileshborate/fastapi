# 64 – Build once: the image goes to GitHub Container Registry, the server only pulls

**Video 64** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

Until Video 63 every server **built** its own image from the code: the image the tests ran against was never
the image production ran. Now CI builds it **once**, tags it with the commit, pushes it to GitHub Container Registry
(GHCR) – and the server only **pulls** that exact image. No Python base image, no build tools, no build cache on
the server.

Course Hub **1.13.0** (Video 63 + its homework):
```
git push ─▶ lint ─▶ test ─▶ image: docker build -t ghcr.io/nileshborate/coursehub:<commit> ─▶ docker push
                                                                                   │
            deploy ──ssh (CI key)──▶ "deploy <commit>" ─▶ rollout.sh: docker compose pull ◀┘
                                                          (the SAME digest CI pushed) → migrate → new api …
```

## Set it up once
1. **Nothing to create for the push:** the image job logs in with the run's own `GITHUB_TOKEN` – the job has
   `permissions: packages: write`. The Dockerfile's `LABEL org.opencontainers.image.source=…` links the package
   to this repo.
2. **The server pulls with its own token** – a classic personal access token with **only `read:packages`**
   (GitHub → Settings → Developer settings → Personal access tokens):
   ```bash
   ssh deploy@api.example.com 'docker login ghcr.io -u nileshborate --password-stdin' < ghcr-read-token.txt
   ```
   (Or make the package public: Packages → coursehub → Package settings → Change visibility – then no login.)
3. **The server's `.env`** gets `IMAGE=ghcr.io/nileshborate/coursehub` – `deploy/server-setup.sh` writes it.
   Use YOUR GitHub name, all **lowercase** – Docker refuses uppercase image names.

## On your laptop (still builds)
```bash
cd 64-ghcr
cp .env.example .env && ./scripts/make-certs.sh
docker compose up -d --build --wait        # compose.override.yaml adds build: - only here
pip install -r requirements-dev.txt
pytest --cov                               # 61 passed · coverage 98.73 % (58 + homework 64)
```

## Project – what's new
```
.github/workflows/ci-64.yml  lint → test → image (build, tag = the commit, push - never for a PR) → deploy
                             image: the ONLY job with packages: write · env IMAGE: lowercase, never :latest
compose.yaml              api + migrate: image: ${IMAGE}:${GIT_SHA} - NO build: section
compose.override.yaml     the laptop adds build: (with the same args as before)
deploy/rollout.sh         pull FIRST (nothing is touched if it fails) · prints the pull time ·
                          keeps the 5 newest images · removes the stopped migrate container first
deploy/server-setup.sh    IMAGE=... in .env · reminds you to docker login with a read-only token
Dockerfile                LABEL org.opencontainers.image.source - GHCR links the package to the repo
tests/                    58 tests: + "production never builds", "pull before migrate", the image job
```

## Honest note – how I ran it
The stand-in lab from Videos 62/63 (an Ubuntu container as the server, a test DNS, Pebble, a git server, my
runner script for the workflow). New today: instead of **ghcr.io**, Docker's own open-source registry
(*distribution* v3.0.0, built from source) on the lab at `10.62.0.40`, with TLS and two users. My runner swaps
`ghcr.io` for that address. Two things that differ from GHCR: the push token is a fixed password (GHCR: the
run's `GITHUB_TOKEN`), and my registry can't make a token read-only (GHCR: `read:packages`).
The registry is on the same machine – so push and pull times here are LAN times, not internet times.

## What the runs showed – real numbers
A GET every 0.1 s to `https://coursehub.example.com/health/ready` during every run:

| run | jobs | pull | deploy step | GETs |
|---|---|---|---|---|
| the first push (1.13.0) | all ✓ · 58 passed · push 2.6 s · 51.8 s | **5 s** (every layer) | 25.9 s | – (the first start) |
| 1.13.1 | all ✓ · 52.5 s | 1 s | 28.0 s | 335 × 200 |
| a pull request | lint ✓ test ✓ image ✓ – **push skipped, no deploy** · 19.6 s | – | – | 131 × 200 |
| 1.13.2 – the server's token is gone | image ✓ · **deploy ✗** in 0.6 s | ✗ | 0.6 s | 165 × 200 – still 1.13.1 |
| 1.13.3 … 1.13.6 | all ✓ · 48.7 – 51.9 s | 0 – 1 s | 27.1 – 27.6 s | 324 – 337 × 200 each |
| `ssh … rollback` → 1.13.5 | – | (on the server) | 27.7 s | 188 × 200 |
| `ssh … deploy <1.13.0>` – its image was pruned | – | pulled again | 27.8 s | 189 × 200 |

**Not one failed request** (after the first start). And the deploy step is NOT faster than Video 63's (26–27 s): it was never the build
– the server's build was cached too. The time goes to "wait until healthy" and the 11 s for nginx. The win is
somewhere else: ↓

### Finding 1 – the server runs the exact bytes CI built
CI's push printed `coursehub@sha256:cd1617fc5725…` – and on the server:
```
$ docker image inspect --format '{{index .RepoDigests 0}}' .../coursehub:b4edbbbcdd8a…
10.62.0.40/nileshborate/coursehub@sha256:cd1617fc57259a3de0b9b89700d12e899f7d90fc9bf78d8f38ad1ddfc63a7afb
$ docker system df
Build Cache     0         0         0B        0B
```
Same digest. The image that passed the tests is the image that serves users – not "the same code, built again".

### Finding 2 – a new commit is ~22 kB, not 182 MB
The first pull took **5 s**: every layer. After that 0 – 1 s: the layers are shared, only `COPY app` (10.5 kB),
`COPY migrations` (11 kB) and `alembic.ini` (721 B) change. Removing one image and pulling it again: 0.6 s.
(`docker history` shows it: the venv layer, 48.9 MB, is the same for every commit.)

### Finding 3 – the token is gone: red in 0.6 s, the users notice nothing
```
==> pull the image of 8e83c3a3a61d (built once, by CI)
Error response from daemon: Head "https://10.62.0.40/v2/nileshborate/coursehub/manifests/8e83c3a3…":
no basic auth credentials
```
rollout.sh pulls **first** – nothing was stopped, migrated or reloaded. 165 of 165 GETs: 200 from 1.13.1.
(On GHCR an expired token says `denied` or `unauthorized` – same place, same result.)

### Finding 4 – a successful deploy that came back red (`grep -m1` + `pipefail`)
My first prune line was `image=$($DC config --images | grep -m1 ":$GIT_SHA$")`. The rollout finished, the new
version served – and the job was red: `rc=255`. `grep -m1` stops reading after the first match; compose writes
the second line into a closed pipe → SIGPIPE → exit 255 → `pipefail` + `set -e` → "failed". Not every time:
**3 of 20** in a loop on the server. Now `grep … | sort -u` reads everything: **0 of 40**. Same for `head`.

### Finding 5 – "keep the 5 newest images" kept 6
`docker rmi` refuses an image that a **stopped** container still uses – and the very first deploy's
`coursehub-migrate-1` (exited) held 1.13.0's image. `|| true` hid it. Now rollout.sh removes the stopped
migrate container first, and after 1.13.6 exactly 5 images were left; 1.13.0's image was gone and its
re-deploy pulled it again.

## Interview questions
1. **Why build the image once in CI instead of on each server?** The tested image IS the deployed image
   (same digest) · no compilers, base images or build cache on servers · a failed build never reaches a server ·
   a rollback is "pull an older tag".
2. **Why tag with the commit and not `:latest`?** `:latest` changes under you: two servers, or a rollback, can't
   say WHICH image they mean. A commit tag never changes – the deploy log, `/health/ready` and the image agree.
3. **How does CI push to GHCR without a stored password?** The run's own `GITHUB_TOKEN`, with
   `permissions: packages: write` on the image job only. The server gets a separate token with `read:packages`.

## Homework
1. **Check the path through nginx:** homework 63 showed a typo in nginx gets through rollout.sh. Before the old
   api stops, curl `/health/ready` THROUGH nginx (on the server) – and if it fails: restore the old config and
   keep the old api.
2. **An image size budget:** the image job fails if the image is bigger than 300 MB (`docker image inspect
   --format '{{.Size}}'`).
3. **A version tag too:** push `:1.13.1` (from `app/config.py`) next to the commit tag, and show both in the
   deploy summary.

Answer at the start of Video 65.

## Homework answer (shown at the start of Video 65)
**1. Check the path through nginx** – `deploy/rollout.sh`, right after an nginx reload, while the old api
still runs:
```bash
sleep 2                    # "nginx -s reload" returns BEFORE the new workers take requests
for _ in 1 2 3 4 5; do curl -fsSk -o /dev/null https://localhost/health/ready && ok=$((ok + 1)); sleep 0.5; done
if [ "$ok" -lt 5 ]; then   # back to ~/.nginx-good (the last config that worked), reload, remove the new api
```
**2. An image size budget** – a step between build and push in `ci-64.yml`: over 300 MB → red, nothing pushed.
**3. A version tag too** – the push step also pushes `:1.13.7` (from `app/config.py`) – but only if that tag
doesn't exist yet: `docker manifest inspect` first. An existing version tag is **never moved**. Both tags and
the digest go into the run page's summary. 3 new tests: **61 passed**.

**The runs** (the same stand-in lab, a GET every 0.1 s):

| push | what happened | GETs |
|---|---|---|
| 1.13.7 | `image: 275 MB - budget: 300 MB` · tags `e490a8394d2c 1.13.7` · deployed | 356 × 200 |
| a comment changed, no version bump | `::warning::…coursehub:1.13.7 exists already - bump the version` → tags `e0a00193b56a (1.13.7: not moved)` | 368 × 200 |
| 1.13.8: nginx `server api:8080` | `0 of 5 through nginx - back to the last good nginx config, old api stays` – deploy red in 19.7 s | 247 × 200 · **33 × 502 for 4.5 s** |
| 1.13.9: a 60 MB file in `app/` | `::error::the image is 395 MB - over budget` – nothing pushed, no deploy | 142 × 200 |

The registry afterwards: `1.13.0 1.13.7 1.13.8` + the commit tags – no 1.13.9, and 1.13.7 still points at its
first commit.

**Finding – my first check passed WITH the typo.** It ran `curl` right after `nginx -s reload` – and got a 200:
the reload only *signals* nginx; the old workers still answer for a moment with the OLD config. The deploy went
through, the check step of homework 63 caught it and rolled back – **233 × 502 for 33.4 s**. With `sleep 2` and
"5 of 5 must answer": **33 × 502 for 4.5 s**, and the server never even got to the rollback.
