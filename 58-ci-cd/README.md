# 58 – CI/CD with GitHub Actions: lint, test on two Pythons, build, smoke-test and publish

**Video 58** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

The Course Hub app from Video 57 (version 1.6.0, now with a title rule: 3–80 characters) – and a
**GitHub Actions workflow** that checks every push and every pull request:

```
lint (ruff)  ──►  test: Python 3.12 + 3.13 (pytest + coverage ≥ 90 %)  ──►  docker: build · smoke test · publish
```

The workflow is **not** in this folder: GitHub only reads workflows from the repository root –
[`.github/workflows/ci-58.yml`](../.github/workflows/ci-58.yml). It only runs when something in
`58-ci-cd/` (or the workflow itself) changes, and works inside this folder (`working-directory`).

## Run it (the same checks as CI, on your laptop)
```bash
cd 58-ci-cd
pip install -r requirements-dev.txt
ruff check .                  # All checks passed!
pytest --cov                  # 13 passed · coverage 98.77 % (needs 90 %)
docker build -t coursehub:ci . && docker run -d --name api -p 8000:8000 coursehub:ci
docker ps                     # ... (healthy)
```
Then push – and open the **Actions** tab on GitHub.

## Project
```
app/  config.py · db.py (connections now really closed) · healthcheck.py (check() - 503 closed too)
      main.py (CourseIn.title: Field(min_length=3, max_length=80))
tests/  test_app.py (7 incl. the title rule) · test_healthcheck.py (3, a real tiny HTTP server)
        test_homework58.py (3 - the CI files are code too)
pyproject.toml     ruff rules · pytest (warnings = errors) · coverage (fail_under = 90) - one place
requirements*.txt  everything pinned - starlette too (see below)
Dockerfile         from Video 57, with the smaller venv from homework 57
../.github/workflows/ci-58.yml   the pipeline
```

## The workflow, piece by piece
| Part | What it does |
|---|---|
| `on: push / pull_request` + `paths` | runs for changes in `58-ci-cd/**` only; `workflow_dispatch` adds a "Run workflow" button |
| `permissions: contents: read` | the automatic `GITHUB_TOKEN` can only read – least privilege |
| `concurrency` + `cancel-in-progress` | a new push to the same branch cancels the old, now useless run |
| `defaults.run.working-directory` | every `run:` step starts in `58-ci-cd/` |
| `needs:` | lint → test → docker; a red job stops the ones after it |
| `strategy.matrix` | the test job runs twice: Python `"3.12"` and `"3.13"` (in quotes – YAML reads `3.10` as `3.1`!) |
| `setup-python` `cache: pip` | keeps pip's downloads between runs, keyed on `requirements-dev.txt` |
| `ruff check --output-format=github` | errors appear as annotations on the line in the pull request |
| docker job | build, run, wait until Docker says `(healthy)`, curl `/health/ready` |
| publish step | only on a push to `main`: `docker login ghcr.io` with `GITHUB_TOKEN` (`packages: write` for this job only) |

## What the runs showed – real numbers
Every `run:` step was executed on my machine the way a runner does it (fresh copy, fresh venv per job).
Docker Hub is blocked there, so the image used my local base (as in Video 57). GitHub's own runners will show different times.

| | |
|---|---|
| `actionlint ci-58.yml` | no problems (a typo `matrix.python` → *property "python" is not defined*; `needs: tests` → *job "tests" does not exist*) |
| lint job | `pip install ruff` 0.94 s · `ruff check` 0.01 s · job 4.34 s |
| test (3.12) | install 7.88 s · `pytest --cov` 3.09 s – 10 passed, 98.77 % |
| test (3.13) | install 5.90 s · `pytest --cov` 2.94 s – 10 passed, 98.77 % |
| docker job | build 13.77 s (cold) · smoke test 5.51 s – `(healthy)` after 6 s · publish skipped (not a push to main) |
| pip cache | install with an empty cache 8.28 s · with a warm cache 5.17 s (22 MB cached) |

**What CI caught before the first green run – real failures:**
1. **A warning that becomes an error.** With `filterwarnings = ["error"]`, Python 3.13's
   `ResourceWarning: unclosed database` failed the tests: `with sqlite3.connect(...)` commits, but does **not**
   close. Fix: `db.connect()` is a `@contextmanager` that closes in `finally`.
2. **A leak in the health check.** A 503 comes back from `urlopen` as an `HTTPError` that still holds the connection
   → `unclosed <socket.socket ...>`. Fix: `exc.close()`.
3. **"Works on my machine".** On my laptop: starlette 1.7.0. In the clean CI venv: **starlette 1.10.0** – whose
   TestClient warns *"Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead"* →
   `1 error during collection`. Fix: pin `starlette==1.10.0` and use `httpx2==2.16.0`. Laptop and CI now install the
   same versions.

**And the failures you will see when you make a mistake:**
- an unused `import json` → `F401 'json' imported but unused` (`app/main.py:3:8`) – the lint job is red, nothing else runs
- `min_length=2` instead of 3 → `test_title_must_be_3_to_80_characters[Go]`: `assert 201 == 422` – 1 failed, 9 passed
- `tests/test_healthcheck.py` deleted → `FAIL Required test coverage of 90.0% not reached. Total coverage: 81.48%`

## CI vs CD
- **CI** (continuous integration): every push is linted, tested and built – a red ✗ on the commit or the PR.
- **Continuous delivery:** every green `main` produces a ready image – here `ghcr.io/<owner>/coursehub:<sha>` and `:latest`.
- **Continuous deployment:** that image is also rolled out automatically – the server pulls it (later in the course).
- Protect `main`: Settings → Branches → require the `lint`, `test` and `docker` checks before merging.

## Interview questions
1. **What is the difference between CI and CD?** CI checks every change automatically (lint, tests, build). Continuous
   delivery makes every green build releasable (an image in a registry); continuous deployment also releases it.
2. **How do you keep secrets out of a workflow?** Repository secrets via `${{ secrets.NAME }}` (masked in logs), the
   automatic `GITHUB_TOKEN` with the least `permissions` – never in the YAML or the code. Pull requests from forks get
   no secrets.
3. **Why pin dependencies if CI already tests?** Without pins, CI tests the newest versions and your laptop tests
   old ones – here starlette 1.10.0 vs 1.7.0. Pins make laptop, CI and production identical; upgrades become a
   deliberate change that CI tests.

## Homework
1. **Dependabot:** add `.github/dependabot.yml` for `pip` in `/58-ci-cd` and for `github-actions` – weekly. Every
   upgrade arrives as a pull request, and our workflow tests it.
2. **A coverage report you can download:** `pytest --cov --cov-report=xml`, then `actions/upload-artifact` – and write
   the total to the job summary (`$GITHUB_STEP_SUMMARY`).
3. **A better smoke test:** after `(healthy)`, `POST /courses` and read the course back with `GET /courses`.

Answer at the start of Video 59 (PostgreSQL in Compose).

## Homework answer (shown at the start of Video 59)
**1. Dependabot** – [`.github/dependabot.yml`](../.github/dependabot.yml) (repo root, next to `workflows/`):
`pip` in `/58-ci-cd` and `github-actions` in `/`, weekly; the dev tools are **grouped** into one pull request.
Checked with `check-jsonschema --builtin-schema vendor.dependabot` → *ok*. What it would propose today (real):

| | pinned | newest |
|---|---|---|
| `fastapi` | 0.156.0 | 0.162.7 |
| `pydantic-settings` | 2.16.1 | 2.16.3 |
| `pytest` | 9.1.1 | 9.2.0 |
| `actions/checkout` · `setup-python` · `upload-artifact` | v4 · v5 · v4 | v7 · v7 · v7 |

Every one of them arrives as a pull request – and `ci-58` tests it before anyone merges.

**2. A coverage report you can download** – in the test job:
```yaml
- run: pytest --cov --cov-report=term --cov-report=xml
- name: Coverage in the job summary
  run: coverage report --format=markdown >> "$GITHUB_STEP_SUMMARY"
- uses: actions/upload-artifact@v4
  with:
    name: coverage-${{ matrix.python-version }}   # unique - the matrix runs twice
    path: 58-ci-cd/coverage.xml                     # uses: ignores working-directory!
```
The trap: `defaults.run.working-directory` is only for `run:` steps. `coverage.xml` is written in `58-ci-cd/`, but
`upload-artifact` looks from the repo root – `path: coverage.xml` finds nothing. Local run: `coverage.xml` 4,236 bytes,
the summary is a Markdown table (`**TOTAL** 81 · 1 · **99%**`).

**3. A better smoke test** – after `(healthy)`, a second step:
```bash
curl -fsS -X POST localhost:8000/courses -H "Content-Type: application/json" -d '{"title": "Smoke test"}'
curl -fsS localhost:8000/courses | grep '"Smoke test"'
```
Output: `{"id":1,"title":"Smoke test"}` then `[{"id":1,"title":"Smoke test"}]` – the image can **write** to its
database, not only start. `curl -f` turns any 4xx/5xx into a failed step; `grep` fails when the course is missing.

**And a test for the CI files** – `tests/test_homework58.py` (needs `pyyaml==6.0.3`): Dependabot points at a folder
that has `requirements.txt`, the artifact path starts with `58-ci-cd/`, the smoke test POSTs and reads back.

Whole workflow, run locally: lint ✓ · test 3.12 ✓ (13 passed) · test 3.13 ✓ (13 passed) · docker ✓ – build,
`(healthy)`, smoke test 0.02 s. `actionlint` and `check-jsonschema --builtin-schema vendor.github-workflows`: no problems.

