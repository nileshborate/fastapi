# Video 62: the production files are code too - compose.yaml, the override, the deploy scripts
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy"


def compose(name: str) -> dict:
    return yaml.safe_load((ROOT / name).read_text())["services"]


def test_production_publishes_only_80_and_443() -> None:
    services = compose("compose.yaml")
    published = {name: s["ports"] for name, s in services.items() if "ports" in s}
    assert published == {"nginx": ["80:80", "443:443"]}   # a db port would go AROUND ufw


def test_every_container_rotates_its_logs() -> None:
    for name, service in compose("compose.yaml").items():
        options = service["logging"]["options"]
        assert options == {"max-size": "10m", "max-file": "3"}, name


def test_the_server_gives_nginx_the_real_certificate() -> None:
    volumes = compose("compose.yaml")["nginx"]["volumes"]
    assert "/etc/letsencrypt:/etc/letsencrypt:ro" in volumes   # ALL of it: live/ = symlinks
    assert "/var/www/certbot:/var/www/certbot:ro" in volumes


def test_the_laptop_override_replaces_the_certificates() -> None:
    override = compose("compose.override.yaml")
    assert override["db"]["ports"] == ["127.0.0.1:5432:5432"]   # only on the laptop
    targets = [v.split(":")[1] for v in override["nginx"]["volumes"]]
    assert targets == ["/etc/letsencrypt", "/var/www/certbot"]   # same targets: replaced


def test_deploy_uses_only_the_production_file() -> None:
    script = (DEPLOY / "deploy.sh").read_text()
    assert "set -euo pipefail" in script and "coursehub/deploy/rollout.sh" in script
    assert 'DC="docker compose -f compose.yaml"' in (DEPLOY / "rollout.sh").read_text()
    excluded = (DEPLOY / "rsync-exclude").read_text().split()
    assert {".env", "compose.override.yaml", "certs/", ".git"} <= set(excluded)


def test_server_setup_allows_ssh_before_the_firewall_starts() -> None:
    lines = (DEPLOY / "server-setup.sh").read_text().splitlines()
    first = {key: next(i for i, line in enumerate(lines) if line.startswith(key))
             for key in ("ufw allow OpenSSH", "ufw --force enable", "sshd -t")}
    assert first["ufw allow OpenSSH"] < first["ufw --force enable"]   # or: locked out
    setup = "\n".join(lines)
    for setting in ("PasswordAuthentication no", "PermitRootLogin no"):
        assert setting in setup


def test_the_certificate_name_matches_nginx() -> None:
    script = (DEPLOY / "certificate.sh").read_text()
    assert script.count("--cert-name coursehub") == 3    # first, reconfigure, certificates
    assert "--webroot-path /var/www/certbot" in script
    assert "nginx -s reload" in script                      # a renewed cert needs a reload


def test_rollout_starts_the_new_api_before_it_stops_the_old_one() -> None:   # homework 62.2
    lines = (DEPLOY / "rollout.sh").read_text().splitlines()

    def first(text: str) -> int:
        return next(i for i, line in enumerate(lines) if text in line)

    assert first("run --rm migrate") < first("--scale api=2") < first("State.Health.Status")
    assert first("State.Health.Status") < first('docker stop "$old"')
    assert first('docker rm -f "$new"') < first('docker stop "$old"')   # unhealthy: old stays


def test_nginx_tries_the_other_api() -> None:
    conf = (ROOT / "nginx" / "default.conf").read_text()
    assert "proxy_next_upstream error timeout http_502 http_503;" in conf


def test_backups_every_night_and_only_seven() -> None:   # Video 62 homework 1
    backup = (DEPLOY / "backup.sh").read_text()
    assert "pg_dump" in backup and "-Fc" in backup and "umask 077" in backup
    assert "KEEP=${BACKUP_KEEP:-7}" in backup
    assert "17 3 * * * deploy $JOB" in (DEPLOY / "server-setup.sh").read_text()
    restore = (DEPLOY / "restore-test.sh").read_text()
    assert "pg_restore" in restore and "dropdb" in restore


def test_the_ci_key_can_only_deploy_a_commit() -> None:   # Video 62 homework 3
    script = (DEPLOY / "ci-command.sh").read_text()
    assert "SSH_ORIGINAL_COMMAND" in script
    assert "^[0-9a-f]{40}$" in script                     # a full commit id - nothing else
    assert '"$HOME/coursehub/deploy/rollout.sh"' in script


# ------------------------------------------------------------- Video 64: the server only pulls
def test_production_never_builds() -> None:
    for name in ("api", "migrate"):
        service = compose("compose.yaml")[name]
        assert "build" not in service                         # compose.yaml: image only
        assert service["image"] == "${IMAGE:-ghcr.io/nileshborate/coursehub}:${GIT_SHA:-dev}"
        assert "build" in compose("compose.override.yaml")[name]   # the laptop builds


def test_rollout_pulls_before_it_changes_anything() -> None:
    lines = (DEPLOY / "rollout.sh").read_text().splitlines()
    pull = next(i for i, line in enumerate(lines) if line.startswith("$DC pull"))
    migrate = next(i for i, line in enumerate(lines) if "run --rm migrate" in line)
    assert pull < migrate                                     # a failed pull: nothing touched
    assert not any(" build" in line for line in lines if line.startswith("$DC"))
    assert any(line.startswith(': "${GIT_SHA:?') for line in lines)   # no commit: stop


def test_homework_64_checks_through_nginx_before_the_old_api_stops() -> None:
    script = (DEPLOY / "rollout.sh").read_text()
    check = script.index("https://localhost/health/ready")
    assert check < script.index('docker stop "$old"')          # the old api still runs
    assert 'cp "$GOOD"/*.conf nginx/' in script                  # back to the last good config
