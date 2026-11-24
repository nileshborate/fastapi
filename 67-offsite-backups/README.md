# 67 – Off-site backups, secrets – and the production checklist (the last technical video)

**Video 67** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

Since Video 62 the nightly `pg_dump` lands on the SAME server as the database. The server dies – the backup dies
with it. Today the backup leaves the server: **restic** – encrypted on the server, deduplicated – to a second box
at another provider, which runs **rest-server in append-only mode**: the app server can ADD backups, but never
delete them. Then: where are our secrets, and who can read them? **gitleaks** over every commit. And at the end:
the **production checklist** for everything we built in this course.

Course Hub **1.16.0** (Video 66 + its homework):
```
the app server (coursehub-1)                            the backup box (another provider)
  cron: deploy/backup.sh                                  rest-server --append-only --private-repos --tls
    pg_dump -Fc -> ~/backups (7 days)                       /srv/restic/coursehub-1   <- only encrypted chunks
    restic backup ──── https + a password per server ───▶   the server: ADD yes · DELETE: 403
                                                            YOU (laptop): ssh/sftp as the owner -> prune
the restic PASSWORD: your password manager + ~/restic-password (600) - lose it = lose every backup
```

## Set it up
```bash
# 1. the BACKUP BOX (a small VM at ANOTHER provider) - as root:
BOX_DOMAIN=backup.example.net ./deploy/backup-box-setup.sh coursehub-1   # rest-server + a user per server
# 2. the APP SERVER - restic (server-setup.sh step 7 does it, with a checksum)
# 3. YOUR LAPTOP: a long password -> your password manager, then to the server (mode 600):
openssl rand -hex 24 > restic-password
scp restic-password restic.env deploy@coursehub.example.com:   # then: chmod 600 both
#   restic.env:  RESTIC_REPOSITORY=rest:https://coursehub-1:BOX-PASSWORD@backup.example.net:8000/coursehub-1/
#                RESTIC_PASSWORD_FILE=/home/deploy/restic-password
ssh deploy@coursehub.example.com 'set -a; . ~/restic.env; restic init'
```
From now on `deploy/backup.sh` (cron, every night) sends each dump off-site too. Once a week:
```bash
deploy/restore-offsite.sh              # the newest off-site snapshot -> a TEST database: is it any good?
deploy/restore-offsite.sh --live       # a disaster: -> the LIVE database (api stops, restore, api starts)
deploy/prune-offsite.sh                # from YOUR laptop, as the box's owner: 7 daily · 4 weekly · 6 monthly
deploy/secrets-check.sh                # exit 1 if any secret file can be read by every user
```

## On your laptop
```bash
cd 67-offsite-backups
cp .env.example .env && ./scripts/make-certs.sh
docker compose up -d --build --wait
pip install -r requirements-dev.txt
pytest --cov                               # 84 passed · coverage 98.97 %
```

## Project – what's new
```
deploy/backup.sh            + restic backup --tag coursehub --host coursehub-1 (only if ~/restic.env exists)
deploy/restore-offsite.sh   newest snapshot of THIS server -> restore-test.sh, or --live into the live database
deploy/backup-box-setup.sh  the box: rest-server (checksum), a system user, htpasswd, systemd, append-only
deploy/prune-offsite.sh     the OWNER deletes old snapshots - over SSH, not through rest-server
deploy/secrets-check.sh     .env, slack_url, pager_url, restic.env, restic-password: readable by "others"? -> !!!
deploy/server-setup.sh      slack_url / pager_url: mode 640, group 65534 (was 644) · step 7: restic 0.18.1
.github/workflows/ci-67.yml + gitleaks over EVERY commit (fetch-depth: 0) - checksum-checked download
tests/                      84 tests: + backups, restore, secrets-check, the workflow
```

## Honest note – how I ran it
A simplified stand-in lab: the "server" is Docker on my machine (`/home/deploy/coursehub`, user deploy), the backup
box is a container at 10.62.0.11 (restic 0.18.1, rest-server 0.14.0, both checksum-checked). Docker Hub is blocked
in my lab, so the images are built from Ubuntu 24.04 – PostgreSQL 16, Python 3.12, nginx 1.28.0 compiled from its
release tarball. The box's certificate is self-signed (yours: certbot). Every output below is real.

## What the runs showed – real numbers
| step | result |
|---|---|
| rest-server starts | `Append only mode enabled` · `Private repositories enabled` · `TLS enabled` |
| `restic init` | `Losing your password means that your data is irrecoverably lost.` |
| night 1: 2,000 courses | dump 16,373 bytes · `Added to the repository: 17.461 KiB (7.994 KiB stored)` |
| night 2: + 50 courses | dump 17,075 bytes · `Added … 18.146 KiB (10.301 KiB stored)` |
| on the box: `grep 'New course'` | **0 files** – only encrypted chunks |
| the attacker (on the server): `restic forget --prune` | `Remove(<snapshot/…>) failed: unexpected HTTP response (403)` |
| the attacker: `rm -rf ~/backups` | the local backups: gone |
| the disaster: `down -v` → an EMPTY database | `courses: 0` |
| `restore-offsite.sh --live` | `courses: 2050 - back` in **12.4 s** · the api: `New course 46 … 50` |
| `restore-offsite.sh` (the weekly test) | `courses: live 2050, restored 2050 · alembic revision 0005` |
| the wrong password | `Fatal: wrong password or no key found` |
| the owner, from the laptop: prune + `restic check` | `keep 2 snapshots` · `no errors were found` |

### Finding 1 – "latest" means the newest of ANYTHING in the repo
My first restore restored the wrong file: I had made test snapshots in the same repository, `restore latest`
took the newest – an experiment, not Course Hub – and the script died: `stat: cannot statx ''`. Now
`restore-offsite.sh` says WHICH latest: `--host coursehub-1 --tag coursehub`.

### Finding 2 – a compressed dump doesn't deduplicate
A bigger test database (300,000 courses), two nights, 1,000 new courses between them:

| | `pg_dump -Fc` (compressed) | `pg_dump -Fp` (plain SQL) |
|---|---|---|
| size | 13.8 MB | 35.2 MB |
| night 1 – stored | 12.598 MiB | 11.532 MiB (restic compresses it) |
| night 2 – stored | **12.640 MiB – everything again** | **3.635 MiB** |

Compression scrambles every byte after the first change – restic finds no equal chunks. Plain SQL: the unchanged
rows are the same chunks. With a 16 kB database it doesn't matter; with 10 GB and 180 snapshots it does.
(`-Fc` stays for the LOCAL copy – pg_restore can restore single tables from it.)

### Finding 3 – the append-only box stops the attacker – not a full disk
The server can't delete, so old snapshots stay forever – until YOU prune them from your laptop, over SSH, as the
box's owner. No prune job = the box fills up. The app server never gets that SSH key.

### Finding 4 – two secret files were readable by EVERY user
`secrets-check.sh` on the server as Videos 65 + its homework left it:
```
ok  /home/deploy/coursehub/.env  600  deploy:deploy
!!! /home/deploy/slack_url  644  deploy:deploy - EVERY user on this server can read it
!!! /home/deploy/pager_url  644  deploy:deploy - EVERY user on this server can read it
exit=1
```
Alertmanager runs as `nobody` (65534), so 600 would lock it out. Now: `640`, group `65534` → `exit=0`. In the
container: user 65534 reads the URL, user 1002: `Permission denied`.

### Finding 5 – gitleaks with `fetch-depth: 1` missed a leak
I committed a real-looking Slack URL, then "fixed" it: `git rm` + a new commit.
```
gitleaks git (the full history)          WRN leaks found: 1    exit=1   <- the old commit still has it
gitleaks git (git clone --depth 1)       INF no leaks found    exit=0   <- actions/checkout's default!
```
That's why `ci-67.yml` checks out with `fetch-depth: 0`. A leaked secret is fixed by **revoking it** (a new Slack
URL) – deleting the file fixes nothing. Then the old finding goes into `.gitleaksignore` by its fingerprint.

## The production checklist – everything from this course
Before real users come, every line should be a yes:

**The code (Videos 1 – 58)**
- [ ] Every input is validated by Pydantic – limits on lengths and numbers, `extra="forbid"` where it matters
- [ ] Errors: one JSON format, no stack traces to the client, the right status codes (400 / 401 / 403 / 404 / 422)
- [ ] Auth: hashed passwords, short-lived tokens, permissions checked on the server – never trust the client
- [ ] Tests run on every push; coverage gate in CI (ours: 90 %, we're at 98.97 %)
- [ ] Structured JSON logs with a request ID – and no passwords or tokens in them
- [ ] `/health/live` and `/health/ready` – ready checks the database and the migration revision

**The server (Videos 59 – 64)**
- [ ] PostgreSQL in Compose with a named volume and a health check; the password only in `.env` (600)
- [ ] Migrations run once, by a one-shot service, with a lock – never by every api container
- [ ] nginx in front: HTTPS only, HSTS + security headers, body + rate limits, real client IPs
- [ ] SSH: keys only, no root login, a deploy user · firewall: only 22, 80, 443 (and Docker's ports checked)
- [ ] Certificates renew themselves (certbot + webroot + a deploy hook) – and you've tested the renewal
- [ ] Deploys: CI builds ONE image per commit, the server only pulls it; a rollback is one command

**Running it (Videos 65 – 67)**
- [ ] Prometheus + alerts that reach a human (Slack, a pager for critical) – and tested alert rules
- [ ] A load test at the load you expect – on staging – and it can FAIL (`exit 1`)
- [ ] Backups every night, **off-site**, encrypted, append-only – and a **restore test** every week
- [ ] The restic password is in your password manager, not only on the server
- [ ] `secrets-check.sh` is green · gitleaks scans every commit · leaked = revoked

## Interview questions
1. **What is the 3-2-1 backup rule – and why isn't a backup on the same server enough?** 3 copies, on 2 kinds of
   storage, 1 off-site. A backup on the same server dies with it: a broken disk, a deleted VM, ransomware – or an
   attacker with your server's keys. That's why the off-site box is append-only.
2. **How do you know a backup works?** You restore it. A backup nobody has restored is a hope. Ours: every week the
   newest off-site snapshot goes into a test database and the row counts are compared.
3. **A secret was pushed to GitHub. What do you do?** Revoke it FIRST – a new key, a new URL. Then remove it from
   the code. Deleting the file or the commit doesn't help: forks, clones and caches still have it. Then scan the
   whole history (gitleaks, `fetch-depth: 0`) so it doesn't happen again.

## No homework
This was the last technical video. Next – Video 68: thank you, and what to learn next.
