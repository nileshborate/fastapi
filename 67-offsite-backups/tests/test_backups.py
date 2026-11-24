# Video 67: the backups leave the server - encrypted, append-only - and no secret in git
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy"


def test_every_backup_also_goes_off_site() -> None:
    backup = (DEPLOY / "backup.sh").read_text()
    restic = backup.index("restic backup")
    assert backup.index('mv "$file.tmp" "$file"') < restic        # only a COMPLETE dump leaves
    assert 'if [ -f "$HOME/restic.env" ]' in backup               # no box yet: still runs


def test_the_backup_box_is_append_only() -> None:
    box = (DEPLOY / "backup-box-setup.sh").read_text()
    assert "--append-only" in box and "--private-repos" in box and "--tls" in box
    assert "sha256sum -c -" in box                                 # a checked download


def test_only_the_owner_deletes_old_snapshots() -> None:
    prune = (DEPLOY / "prune-offsite.sh").read_text()
    assert "sftp:restic@" in prune and "forget --keep-daily 7" in prune and "--prune" in prune
    assert "restic check" in prune


def test_the_restore_never_leaves_a_plain_dump_behind() -> None:
    restore = (DEPLOY / "restore-offsite.sh").read_text()
    assert "trap 'rm -rf \"$tmp\"' EXIT" in restore
    assert 'exec deploy/restore-test.sh "$dump"' in restore        # default: a TEST database
    assert "--clean --if-exists" in restore                        # --live: a new server


def test_secret_files_are_not_world_readable() -> None:
    setup = (DEPLOY / "server-setup.sh").read_text()
    assert "install -m 644" not in setup
    assert setup.count("install -m 640 -o deploy -g 65534 /dev/null") == 2   # slack + pager
    assert "(( 8#$mode & 8#004 ))" in (DEPLOY / "secrets-check.sh").read_text()


def test_ci_scans_the_whole_history_for_secrets() -> None:
    ci = yaml.safe_load((ROOT.parent / ".github" / "workflows" / "ci-67.yml").read_text())
    steps = ci["jobs"]["lint"]["steps"]
    assert steps[0]["with"]["fetch-depth"] == 0                   # depth 1: the history is gone
    scan = steps[1]["run"]
    assert "sha256sum -c -" in scan and "gitleaks git" in scan and "--exit-code 1" in scan
