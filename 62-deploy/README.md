# 62 – Deploy to a cloud VM: SSH, a firewall, a domain and Let's Encrypt

**Video 62** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

Videos 57–61 built the stack: the api in Docker, PostgreSQL, Alembic, Nginx with HTTPS. Today it leaves the
laptop: a fresh Ubuntu 24.04 server, SSH with keys, a firewall, a domain, a **real** certificate from
Let's Encrypt that renews itself – and a deploy script.

Course Hub **1.11.0** (Video 61 + its homework, head **0005**):
```
laptop ──ssh (key)──▶ deploy@server           a deploy: rsync + docker compose up --build --wait
browser ──HTTPS──▶ api.example.com ─▶ ufw: 22, 80, 443 ─▶ nginx ─▶ api ─▶ db
Let's Encrypt ──http :80──▶ /.well-known/acme-challenge/  (certbot proves the domain is yours)
```

## The order – once per server
```bash
# 0. create an Ubuntu 24.04 VM with YOUR public key (ssh-keygen -t ed25519) · DNS: an A record -> its IP
ssh ubuntu@SERVER_IP 'sudo bash -s' < deploy/server-setup.sh          # Docker, certbot, deploy user, sshd, ufw
ssh ubuntu@SERVER_IP "sudo DOMAIN=api.example.com EMAIL=you@example.com bash -s first" < deploy/certificate.sh
DEPLOY_HOST=deploy@api.example.com DOMAIN=api.example.com ./deploy/deploy.sh   # the first deploy
ssh ubuntu@SERVER_IP "sudo bash -s renewals" < deploy/certificate.sh  # renewals while nginx runs
```
After that, every release is one line: `DEPLOY_HOST=deploy@api.example.com DOMAIN=api.example.com ./deploy/deploy.sh`.
**Start with Let's Encrypt's staging server** (`ACME_SERVER=https://acme-staging-v02.api.letsencrypt.org/directory`):
no rate limits while you experiment – then run `first` again without it.

## On your laptop (unchanged from Video 61)
```bash
cd 62-deploy
cp .env.example .env
./scripts/make-certs.sh                # dev certificates in certbot's layout: certs/live/coursehub/
docker compose up -d --build --wait    # + compose.override.yaml, automatically: dev certs, psql on 5432
pip install -r requirements-dev.txt
pytest --cov                           # 43 passed · coverage 98.73 %
```

## Project – what's new
```
deploy/server-setup.sh    once, as root: docker.io + docker-compose-v2 + certbot + ufw + unattended-upgrades,
                          a deploy user (your key, docker group, no sudo), sshd: keys only + no root, ufw
                          (SSH FIRST, then 80 + 443), a .env with a random password
deploy/certificate.sh     first: certbot --standalone (nginx isn't running yet) · renewals: certbot
                          reconfigure --webroot + a deploy hook that reloads nginx
deploy/deploy.sh          from the laptop: rsync (deploy/rsync-exclude) + docker compose -f compose.yaml
                          up -d --build --wait + a curl through the domain
deploy/rsync-exclude      never copied: .env, certs/, compose.override.yaml, .git, tests/
compose.yaml              PRODUCTION: only nginx publishes ports · /etc/letsencrypt + /var/www/certbot
                          mounted · logs rotated (10 MB × 3) · build arg BASE
compose.override.yaml     LAPTOP only (Compose reads it automatically): dev certs, psql on 127.0.0.1:5432
nginx/default.conf        port 80: /.well-known/acme-challenge/ from /var/www/certbot, the rest -> 301 ·
                          the certificate: /etc/letsencrypt/live/coursehub/ · server_name _
scripts/make-certs.sh     dev certificates in the same layout as certbot
tests/test_deploy.py      7 tests: ports, log rotation, the override, deploy.sh, ufw order, cert name
.github/workflows/ci-62.yml  lint + shellcheck · tests · the stack with dev certificates
```

## Honest note – how I ran it
My recording machine has **no cloud account, no public domain and no Docker Hub**. So the server is a
**local stand-in lab** – everything the scripts do is the same, the surroundings are stand-ins:

| real world | my stand-in |
|---|---|
| a cloud VM | an Ubuntu 24.04 container with its own network, sshd, ufw (iptables) and its own Docker engine – no systemd |
| a domain at a DNS provider | `coursehub.example.com` in a test DNS server (`pebble-challtestsrv`) |
| Let's Encrypt | **Pebble** v2.9.0 – Let's Encrypt's own ACME test server, the same protocol, a test CA (built from source) |
| Docker Hub images on the VM | my local images, loaded with `docker save \| docker load` (PostgreSQL 16.15, nginx 1.28.0, Python 3.12) |
| the VM's internet | PyPI through my machine's proxy (a `~/.docker/config.json` for the deploy user) |

On a real VM you need none of these: `docker compose` pulls the images, certbot talks to Let's Encrypt.

## What the runs showed – real numbers
| | |
|---|---|
| `ssh-keygen -t ed25519` | `~/.ssh/id_ed25519` (private, `-rw-------`) + `id_ed25519.pub`: `ssh-ed25519 AAAAC3Nza… nilesh@laptop` |
| the first `ssh` | `The authenticity of host … can't be established. ED25519 key fingerprint is SHA256:…` – compare it with the provider's console **before** you type yes |
| before the setup | `ssh` without the key: `Permission denied (publickey,password)` – passwords were still allowed |
| `server-setup.sh` | **32.6 s** (apt update + install) · after it: `Permission denied (publickey)` for passwords and for `root@` · `deploy` is in `docker`, `sudo -n true` → `a password is required` |
| `ufw status verbose` | `Default: deny (incoming), allow (outgoing)` · 22/tcp (OpenSSH), 80/tcp, 443/tcp |
| on the server | Docker 24.0.7 · Docker Compose **2.24.6** (Ubuntu's packages) · certbot 2.9.0 |
| `certificate.sh first` | **3.55 s**: `Successfully received certificate.` · `Expiry Date: 2027-02-15 (VALID: 89 days)` |
| the first `deploy.sh` | **26.2 s**: rsync, build on the server, db → migrate → api → nginx healthy, then `{"status":"ready","version":"1.11.0","revision":"0005"}` through the domain |
| `curl -v https://coursehub.example.com` | `TLSv1.3` · `issuer: CN=Pebble Intermediate CA …` · `expire date: Feb 15 2027` · `HTTP/2 200` |
| ports from the internet | 22, 80, 443 **open** · 5432, 8000 **closed** |
| `POST /courses` | `201` · `location: https://coursehub.example.com/courses/1` (FORWARDED_ALLOW_IPS from Video 61) |

### Finding 1 – Docker goes around ufw
`docker run -d -p 8081:80 …` on the server, `ufw status` has **no** rule for 8081 – and from the internet:
`curl http://coursehub.example.com:8081` → **200**. Docker writes its own iptables rule
(`-A DOCKER ! -i docker0 -p tcp --dport 8081 -j DNAT --to-destination 172.30.0.2:80`) in the nat table –
the packet is sent on to the container, and ufw's rules for incoming traffic never see it. With `-p 127.0.0.1:8081:80`: from the
internet a timeout (curl exit 28), on the server itself 200. That's why production `compose.yaml` publishes
**only** nginx's 80 and 443 – and the db has no `ports:` at all (a test checks it).

### Finding 2 – ufw without the SSH rule locks you out
On a second fresh VM: `sudo ufw default deny incoming; sudo ufw --force enable` – no `ufw allow OpenSSH`.
`Firewall is active` … and the next `ssh`: `Connection timed out` after 10 s. The only way back in is the
provider's web console: `ufw allow OpenSSH` → `back in`. `server-setup.sh` allows SSH **first**; a test checks the
order.

### Finding 3 – the first certificate works, the first renewal wouldn't
`certbot certonly --standalone` is right for the first certificate: nginx isn't running, certbot answers
Let's Encrypt on port 80 itself. But it **remembers** that: `/etc/letsencrypt/renewal/coursehub.conf` says
`authenticator = standalone`, and with nginx running:
```
$ sudo certbot renew --dry-run
Failed to renew certificate coursehub with error: Could not bind TCP port 80 because it is already in use
by another process on this system (such as a web server).
```
From day 60 every renewal would have failed – and on day 90 the certificate expires. `certificate.sh renewals` runs `certbot reconfigure
--webroot --webroot-path /var/www/certbot --deploy-hook "… nginx -s reload"` – now `authenticator = webroot`,
the dry run: `Congratulations, all simulated renewals succeeded`. A **real** renewal (`--force-renewal`):
the serial nginx sends changed from `29DEBE2C29818B5F` to `04AB9625DFC0B8B2`, `notBefore` 08:00:03 → 08:03:58 –
nginx was only **reloaded**. ("Hook 'deploy-hook' ran with error output" is nginx's `signal process started`
notice on stderr.) Certbot's timer runs `certbot renew` twice a day; it renews 30 days before expiry. Run by
hand without a terminal, certbot first waits a random delay – I saw `random delay of 243.29 seconds` –
`--no-random-sleep-on-renew` skips it.

### Finding 4 – `live/` is only symlinks
```
'fullchain.pem' -> '../../archive/coursehub/fullchain1.pem'
'privkey.pem' -> '../../archive/coursehub/privkey1.pem'
```
Mount only `/etc/letsencrypt/live/coursehub` into a container: `head: cannot open '/c/fullchain.pem' … No such
file or directory` – the links point into `archive/`, which isn't there. So compose mounts all of
`/etc/letsencrypt` (read-only), and nginx reads `live/coursehub/…`. After a renewal the links point to
`fullchain2.pem` – the path in nginx never changes.

### Finding 5 – every redeploy hurt, and the Compose version decided how much
A new release (1.11.1), `curl /health/ready` every 0.1 s during `deploy.sh`:

| Compose on the server | nginx | failed requests |
|---|---|---|
| **2.24.6** (Ubuntu's `docker-compose-v2`) | **recreated** too | **122 of 144** – 119 × `000` (connection refused), 3 × 502 · deploy 17.1 s |
| **5.6.0** (Docker's own, `~/.docker/cli-plugins` of the deploy user) | kept running | **17 of 124** – all 502, about 2 s while the new api started |

With 2.24.6 Compose recreated nginx because the api it depends on was recreated: nobody could even connect.
With 5.6.0 only the api restarted – nginx answered 502 until it was healthy, then `resolve` found the new
address. (The **first** deploy with 5.6.0 recreated nginx once more: the containers were made by 2.24.6.)
Docker's own apt repository (https://docs.docker.com/engine/install/ubuntu/) gives you the current engine and
Compose – my stand-in VM couldn't reach it, so `server-setup.sh` uses Ubuntu's packages, the ones I tested.
Zero failed requests: homework.

**CI (`.github/workflows/ci-62.yml`)**, run the way a runner does: lint ✓ + shellcheck 0.11.0 ✓ · test:
**43 passed** (98.73 %) · stack: `compose -f compose.yaml config` ✓ · `nginx -t` ✓ · `up -d --build --wait` 12.03 s ·
port 80 serves `/.well-known/acme-challenge/ci` ✓ · everything else `301` ✓ · HTTPS `"revision":"0005"` ✓.
(My run used the stand-in images.) `actionlint` + the JSON schema check: ok.

## Interview questions
1. **You get a fresh Linux server. What do you do before you deploy anything?** SSH keys only (no passwords, no
   root login), a separate deploy user, a firewall that allows SSH **first** and then only 80/443, automatic
   security updates – and check the host key fingerprint the first time you connect.
2. **ufw denies port 8081, but a container published on 8081 is reachable from the internet. Why?** Docker
   publishes ports with its own iptables NAT rules; the packet is redirected before ufw's input rules see it.
   Publish only what must be public (nginx), bind the rest to `127.0.0.1` or don't publish it.
3. **How does Let's Encrypt know the domain is yours – and how do renewals work while nginx runs?** HTTP-01:
   certbot puts a token under `/.well-known/acme-challenge/` and Let's Encrypt fetches it on port 80 of the
   domain. With `--webroot`, nginx serves that folder, so renewals need no downtime; a deploy hook reloads nginx
   to pick up the new certificate.

## Homework
1. **Nightly backups:** a cron job on the server runs `pg_dump` into one file per day, keeps 7 days – and you
   **test a restore** into a fresh database.
2. **Zero failed requests during a redeploy:** get "17 of 124" to **0** with the same curl loop – e.g. start the
   new api before the old one stops, and let nginx retry (`proxy_next_upstream`).
3. **A key that can only deploy:** a second SSH key for the deploy user with `restrict,command="…"` in
   `authorized_keys` – it can run the deploy and nothing else. You'll need it in the next video.

Answer at the start of Video 63 (deploy from GitHub Actions).
