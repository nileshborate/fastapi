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
    assert "set -euo pipefail" in script
    assert "docker compose -f compose.yaml up -d --build --wait" in script
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
