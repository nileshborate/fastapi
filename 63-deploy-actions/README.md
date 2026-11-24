# 63 – Deploy from GitHub Actions: push to main → tests → the server, with secrets and a rollback

**Video 63** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

Video 62 deployed from the laptop: `./deploy/deploy.sh`. Today nobody runs that any more – a push to `main` runs
the tests, builds the image, and **only if all of it is green** a GitHub runner tells the server: deploy THIS
commit. The runner gets one SSH key that can do nothing else. And `/health/ready` now says which commit runs.

Course Hub **1.12.0** (Video 62 + its homework, head **0005**):
```
git push ─▶ GitHub Actions: lint ─▶ test ┐
                                  image ─┴▶ deploy ──ssh (CI key)──▶ "deploy <commit>"
                                                                          │ ci-command.sh: git fetch + checkout
                                                                          ▼ rollout.sh (zero downtime, Video 62)
        curl https://DOMAIN/health/ready ◀── "commit":"<the first 12 characters>" ── is OUR commit running?
```

## Set it up once
```bash
# 1. a key for GitHub - no passphrase (a runner can't type one), only for this
ssh-keygen -t ed25519 -N '' -C github-actions -f ~/.ssh/ci_deploy
# 2. the server: the public key, locked to ci-command.sh (homework 62)
echo "restrict,command=\"/home/deploy/coursehub/deploy/ci-command.sh\" $(cat ~/.ssh/ci_deploy.pub)" \
  | ssh deploy@api.example.com 'cat >> .ssh/authorized_keys'
# 3. the server's host key - compare the fingerprint with your provider's console first
ssh-keyscan -t ed25519 api.example.com
```
**GitHub → Settings → Environments → New environment `production`:**

| | name | value |
|---|---|---|
| secret | `DEPLOY_SSH_KEY` | the whole **private** key `~/.ssh/ci_deploy` – with its last line break |
| secret | `DEPLOY_KNOWN_HOSTS` | the `ssh-keyscan` line |
| variable | `DEPLOY_HOST` | `deploy@api.example.com` |
| variable | `DOMAIN` | `api.example.com` |

Or with the GitHub CLI:
```bash
gh secret set DEPLOY_SSH_KEY --env production < ~/.ssh/ci_deploy
ssh-keyscan -t ed25519 api.example.com | gh secret set DEPLOY_KNOWN_HOSTS --env production
gh variable set DEPLOY_HOST --env production --body deploy@api.example.com
gh variable set DOMAIN --env production --body api.example.com
```
Optional: **Required reviewers** on the environment – then every deploy waits for a click.
After that: `git push` – that's the deploy. A rollback: Actions → ci-63 → **Run workflow** → `commit` = an older
commit, or `ssh -i ~/.ssh/ci_deploy deploy@api.example.com rollback`.

## On your laptop (unchanged)
```bash
cd 63-deploy-actions
cp .env.example .env && ./scripts/make-certs.sh
docker compose up -d --build --wait
pip install -r requirements-dev.txt
pytest --cov                           # 55 passed · coverage 98.73 % (53 + homework 63)
```

## Project – what's new
```
.github/workflows/ci-63.yml  lint (ruff + shellcheck) → test (postgres service) + image (docker build) → deploy
                             deploy: only on main, never for a PR · environment production · one at a time,
                             never cancelled half-way · secrets only through env · no checkout on the runner
                             the workflow's own concurrency cancels older runs only for PRs (see Finding 5)
deploy/ci-command.sh      the CI key's ONLY commands: deploy <40-character commit> | rollback | status
deploy/deploy.sh          the laptop deploy passes the commit too (GIT_SHA)
Dockerfile                ARG GIT_SHA + ENV GIT_SHA: the image knows its commit
app/config.py, main.py    1.12.0 · /health/ready: "commit": the first 12 characters (laptop: "dev")
tests/test_workflow.py    5 tests read ci-63.yml: needs, if, concurrency, secrets via env, the ci-command cases
```

## Honest note – how I ran it
Same stand-in lab as Video 62 (an Ubuntu container as the VM, Pebble instead of Let's Encrypt, a test DNS).
New stand-ins for today:

| real world | my stand-in |
|---|---|
| github.com | a local git server (`git daemon`) – the server clones from it (`~/ci-command.env` sets `REPO_URL`) |
| a GitHub runner | `ci63.py` reads **ci-63.yml** and runs its `run:` steps with GitHub's shell (`bash -e`): lint, test, image on my machine (a fresh checkout of the commit, the postgres service), deploy in a **fresh** container on the lab's internet, with the job's env, secrets and variables |
| `uses:` steps (checkout, setup-python) | a `git archive` of the commit · a Python 3.13 venv |
| the image job | `--build-arg BASE=` my local Python image (no Docker Hub here) – with cache, so 0.3 s instead of a minute |

## What the runs showed – real numbers
A GET every 0.1 s to `https://coursehub.example.com/health/ready` during every run:

| push | jobs | deploy step | GETs | who answers after it |
|---|---|---|---|---|
| the first one (1.12.0) | lint ✓ test ✓ **53 passed** image ✓ deploy ✓ · **56.2 s** | 36.9 s | **375 × 200** | `"commit":"a52be60512a3"` |
| a comment after `ENV` in the Dockerfile | image ✗ – no deploy · 18.0 s | – | 125 × 200 | still a52be60512a3 |
| 1.12.1 | all ✓ · 46.2 s | 26.7 s | **312 × 200** | `"version":"1.12.1"` |
| 1.12.2: `app.mian` – a typo in the Dockerfile's CMD | lint ✓ test ✓ image ✓ **deploy ✗** · 85.0 s | 66.0 s | **570 × 200** | still **1.12.1** |
| 1.12.3 – the fix | all ✓ · 46.3 s | 26.1 s | 312 × 200 | 1.12.3 |
| Run workflow, `commit` = 1.12.1's | all ✓ · 47.3 s | 27.1 s | 313 × 200 | **1.12.1** |
| `ssh … rollback` | – | 26.9 s | 188 × 200 | 1.12.3 again |

Not one failed request in seven runs. `ssh … status` at the end – only successful deploys are written down:
```
2026-11-17T13:27:28+00:00 a52be60512a3ef90b66d437b39299c9b45fd55a8   1.12.0 (the first push)
2026-11-17T13:28:42+00:00 96cef73e80f7bd9a742f0b92346ca23aa63d621b   1.12.1
2026-11-17T13:31:01+00:00 026fcf60e10fcfd4bdaa238e6930cf29e4549aa3   1.12.3 (1.12.2 never got a line)
2026-11-17T13:31:52+00:00 96cef73e80f7bd9a742f0b92346ca23aa63d621b   Run workflow -> 1.12.1
2026-11-17T13:32:22+00:00 026fcf60e10fcfd4bdaa238e6930cf29e4549aa3   ssh rollback -> 1.12.3
```
`rollback` = undo the LAST deploy (the line before the current one) – run it twice and you're back.

### Finding 1 – green tests, a broken image
My first version of the Dockerfile had `ENV GIT_SHA=${GIT_SHA}    # /health/ready shows it`. All 53 tests
passed – they never build the Dockerfile – and the deploy failed on the server:
```
Dockerfile:27
  27 | >>> ENV GIT_SHA=${GIT_SHA}    # /health/ready shows it
ERROR: failed to build: failed to solve: Syntax error - can't find = in "#". Must be of the form: name=value
```
In a Dockerfile `#` starts a comment only at the beginning of a line. So the workflow has an **image** job: it
builds the image, and `deploy` needs `[test, image]`. The same mistake now: image ✗ in 18 s, the server is never
touched. (rollout.sh would have saved the server anyway – but the CI is the right place to stop it.)

### Finding 2 – the tests can't see everything: a typo in CMD
1.12.2 starts `app.mian:app`. Lint ✓, 53 tests ✓, the image builds ✓ (CMD only runs when a container starts).
On the server the new api never got healthy:
```
!!! the new api is 'unhealthy' - removing it, the old one keeps serving
ERROR:    Error loading ASGI app. Could not import module "app.mian".
```
The deploy job is **red**, GitHub mails you – and the users noticed nothing: **570 of 570** GETs were 200 from
1.12.1. That's homework 62's `rollout.sh` doing its job. The fix was one more push.

### Finding 3 – two classic mistakes with the secrets
| mistake | what the runner shows |
|---|---|
| `DEPLOY_KNOWN_HOSTS` empty (or `StrictHostKeyChecking=no` left out) | `Host key verification failed.` – exit 255 |
| the private key without its **last** newline (`echo -n`, `printf '%s'`, a copy-paste) | `Load key "…": error in libcrypto` then `Permission denied (publickey)` |

Never "fix" the first with `-o StrictHostKeyChecking=no`: then the runner sends the deploy to whoever answers on
that address. `ssh-keyscan` once, compare the fingerprint with the console (`256 SHA256:DjOWATI1… (ED25519)`), store it.
The workflow writes the key with `printf '%s\n'` – the newline is always there.

### Finding 4 – a rollback is a deploy of an older commit
`Run workflow` with `commit` = 1.12.1's id: the same jobs, the same `rollout.sh`, 0 failed requests, and
`/health/ready` shows the old commit. No special code path – that's why it works when you need it. The server
keeps the git checkout (`~/src`), so it only fetches what's new.

### Finding 5 – two `concurrency` blocks, and the wrong one can kill a deploy
The deploy job has `cancel-in-progress: false`. But my first workflow also had, at the top,
`concurrency: ci-63-${{ github.ref }}` with `cancel-in-progress: true` – nice for PRs, fatal for `main`: a second
push cancels the **whole** older run, the running deploy job included, and the job-level setting doesn't stop
that. Now: `cancel-in-progress: ${{ github.event_name == 'pull_request' }}` – on `main` a newer run waits.
(Found reading the docs, not in a run – my local runner has no concurrency; a test checks the expression.)

## Interview questions
1. **How do you deploy from CI without giving CI the keys to your server?** A separate SSH key just for CI, stored
   as a secret in a protected environment, and on the server `restrict,command="…"` in `authorized_keys`: that key
   can run one script, which accepts only `deploy <commit>` / `rollback` / `status`. No shell, no tunnels.
2. **Why `needs`, `if` and `concurrency` on the deploy job?** `needs`: deploy only after the tests and the image
   build are green. `if`: only for `main`, never for a pull request (PRs from forks get no secrets anyway).
   `concurrency` with `cancel-in-progress: false`: two pushes never deploy at the same time, and a running deploy
   is never killed half-way.
3. **The tests passed, the deploy failed. What protects the users?** The rollout: the new version starts next to
   the old one and only takes traffic when its health check is green; otherwise it's removed and the old one keeps
   serving. And `/health/ready` reports the commit, so the pipeline checks that its commit is really live.

## Homework
1. **Roll back automatically:** if the "is OUR commit running?" step fails, the workflow runs `rollback` itself
   (`if: failure()`) – and the job stays red.
2. **A deploy summary:** write the commit, the version and the deploy time into `$GITHUB_STEP_SUMMARY` – the run
   page shows it.
3. **Tell somebody:** when the deploy job fails, POST a short message to a webhook (Slack, Discord, Teams) – the
   URL is a secret too.

Answer at the start of Video 64 (build once: the image goes to GitHub Container Registry, the server only pulls).

## Homework answer (shown at the start of Video 64)
All three are new steps at the end of the deploy job in `.github/workflows/ci-63.yml` – 2 new tests in
`tests/test_workflow.py` (**55 passed**, 98.73 %).

```yaml
      - name: Check it the way a user does - is OUR commit running?
        id: check                           # 1. the rollback asks for THIS step's outcome
      - name: Roll back by itself - the job stays red
        id: rollback
        if: failure() && steps.check.outcome == 'failure'
        run: ssh -i ~/.ssh/deploy_key -o BatchMode=yes "$DEPLOY_HOST" rollback
      - name: Deploy summary                # 2. Markdown -> $GITHUB_STEP_SUMMARY, the run page
        if: always()
      - name: Tell somebody                 # 3. a webhook - the URL is the secret DEPLOY_WEBHOOK_URL
        if: failure()
```
Why `steps.check.outcome == 'failure'` and not just `failure()`: when the **deploy** step fails, rollout.sh
already kept the old version – there's nothing to roll back. Only "deployed, but our commit doesn't answer" needs it.
The deploy step writes `DEPLOY_SECONDS` into `$GITHUB_ENV`, so later steps can read it.

**The runs** (the same stand-in lab; a webhook receiver plays Slack; a GET every 0.1 s):

| push | what happened | GETs | the run page's summary |
|---|---|---|---|
| 1.12.4 | all green · deploy 27 s | 318 × 200 | `success · 1.12.4 · 27 s · rollback skipped` |
| 1.12.5: nginx `server api:8080` (a typo) | the api is healthy, `nginx -t` passes, rollout.sh finishes ✓ – then the check: `502` four times → **rollback by itself** (26.8 s) → the job is red | 336 × 200 · **223 × 502** – for 34.1 s | `failure · 27 s · rollback success` |
| 1.12.6: `app.mian` | the deploy step fails (unhealthy, removed) – no rollback needed | **611 × 200** | `failure · rollback skipped` |

What the webhook got:
```
POST /services/T000/B000/coursehub  {"text":"Deploy of 3b599ed91a53 FAILED (automatic rollback: success) - https://github.com/nileshborate/fastapi/actions/runs/11873400003"}
POST /services/T000/B000/coursehub  {"text":"Deploy of 19142ab0deb3 FAILED (automatic rollback: skipped) - https://github.com/nileshborate/fastapi/actions/runs/11873400004"}
```
**Finding:** the nginx typo got through everything on the server – rollout.sh checks the api's own health, not
the path through nginx. Without the automatic rollback that's an outage until somebody notices; with it, 34 s.
(The run links point at run ids of my stand-in runner.)
