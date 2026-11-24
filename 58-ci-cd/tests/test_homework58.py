# Homework 58 - the CI files are code too: these tests catch the mistakes that are easy to make
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]          # the repository root
HERE = Path(__file__).resolve().parents[1]          # 58-ci-cd
WORKFLOW = yaml.safe_load((ROOT / ".github/workflows/ci-58.yml").read_text())
DEPENDABOT = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text())


def steps(job: str) -> list[dict]:
    return WORKFLOW["jobs"][job]["steps"]


def test_dependabot_watches_our_requirements_and_actions() -> None:
    by_type = {u["package-ecosystem"]: u for u in DEPENDABOT["updates"]}
    assert (ROOT / by_type["pip"]["directory"].lstrip("/") / "requirements.txt").exists()
    assert by_type["github-actions"]["directory"] == "/"


def test_artifact_path_starts_at_the_repo_root() -> None:
    upload = next(s for s in steps("test") if "upload-artifact" in s.get("uses", ""))
    # uses: steps ignore working-directory - the path must include the folder
    assert upload["with"]["path"] == f"{HERE.name}/coverage.xml"
    assert "matrix.python-version" in upload["with"]["name"]       # unique name per Python


def test_smoke_test_writes_and_reads_a_course() -> None:
    script = "\n".join(s.get("run", "") for s in steps("docker"))
    assert "-X POST localhost:8000/courses" in script
    assert "curl -fsS localhost:8000/courses | grep" in script
