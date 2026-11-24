#!/usr/bin/env bash
# ONCE, on a fresh Ubuntu 24.04 server - as root, from your laptop:
#   ssh ubuntu@SERVER_IP 'sudo bash -s' < deploy/server-setup.sh
set -euo pipefail

echo "==> 1. packages: Docker + Compose, certbot, the firewall, automatic security updates"
apt-get update -q
DEBIAN_FRONTEND=noninteractive apt-get install -y -q \
    docker.io docker-compose-v2 certbot ufw unattended-upgrades git cron >/dev/null

echo "==> 2. a deploy user: logs in with YOUR key, runs docker - no password, no sudo"
id deploy >/dev/null 2>&1 || adduser --disabled-password --gecos "" deploy >/dev/null
usermod -aG docker deploy                 # the docker group is root-equivalent: guard this key
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
install -m 600 -o deploy -g deploy /home/ubuntu/.ssh/authorized_keys /home/deploy/.ssh/

echo "==> 3. SSH: keys only, no root login"
cat > /etc/ssh/sshd_config.d/99-coursehub.conf <<'CONF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
CONF
sshd -t                                   # a broken sshd config = locked out: test first
systemctl reload ssh 2>/dev/null || kill -HUP "$(cat /run/sshd.pid)"   # no systemd: my stand-in

echo "==> 4. the firewall: SSH FIRST - then 80 + 443 - then enable"
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null
ufw allow OpenSSH >/dev/null
ufw allow 80/tcp >/dev/null               # HTTP: Let's Encrypt's check + the redirect
ufw allow 443/tcp >/dev/null
ufw --force enable

echo "==> 5. the app folder, the challenge folder and .env with a random password"
install -d -o deploy -g deploy /home/deploy/coursehub
install -d /var/www/certbot
if [ ! -f /home/deploy/coursehub/.env ]; then
    umask 077
    printf 'POSTGRES_USER=coursehub\nPOSTGRES_PASSWORD=%s\nPOSTGRES_DB=coursehub\n' \
        "$(openssl rand -hex 24)" > /home/deploy/coursehub/.env
    # Video 64: the image the server pulls - YOUR GitHub name, all lowercase
    echo "IMAGE=${IMAGE:-ghcr.io/nileshborate/coursehub}" >> /home/deploy/coursehub/.env
    # Video 65: the Slack webhook URL for alertmanager - paste yours into this file
    echo "SLACK_URL_FILE=/home/deploy/slack_url" >> /home/deploy/coursehub/.env
    install -m 644 -o deploy -g deploy /dev/null /home/deploy/slack_url   # read by: nobody
    chown deploy:deploy /home/deploy/coursehub/.env
fi
echo "==> 6. a backup every night at 03:17 - deploy/restore-test.sh proves it can be restored"
install -d -m 700 -o deploy -g deploy /home/deploy/backups
JOB="/home/deploy/coursehub/deploy/backup.sh >> /home/deploy/backups/backup.log 2>&1"
echo "17 3 * * * deploy $JOB" > /etc/cron.d/coursehub-backup   # min hour day month weekday
ufw status verbose | head -4
echo "done: ssh deploy@$(hostname -I | cut -d' ' -f1)"
echo "next: docker login ghcr.io as deploy - a token with read:packages ONLY (Video 64)"
