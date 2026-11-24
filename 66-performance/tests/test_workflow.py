# Video 63-65: the deploy workflow is code too - a wrong "if" deploys every pull request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT.parent / ".github" / "workflows" / "ci-66.yml"


def jobs() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())["jobs"]


def test_deploy_only_after_the_tests_and_only_from_main() -> None:
    deploy = jobs()["deploy"]
    assert deploy["needs"] == "image" and jobs()["image"]["needs"] == "test"
    assert jobs()["test"]["needs"] == "lint"
    only_main = "github.ref == 'refs/heads/main' && github.event_name != 'pull_request'"
    assert deploy["if"] == only_main


def test_one_deploy_at_a_time_never_cancelled() -> None:
    deploy = jobs()["deploy"]
    assert deploy["concurrency"] == {"group": "deploy-production", "cancel-in-progress": False}
    assert deploy["environment"]["name"] == "production"
    # the WORKFLOW may cancel only pull requests - on main it would kill a running deploy
    on_main = yaml.safe_load(WORKFLOW.read_text())["concurrency"]["cancel-in-progress"]
    assert on_main == "${{ github.event_name == 'pull_request' }}"


def test_secrets_only_through_env() -> None:
    for step in jobs()["deploy"]["steps"]:
        assert "secrets." not in step["run"]        # ${{ }} inside run: script injection
    key_step = jobs()["deploy"]["steps"][0]
    assert set(key_step["env"]) == {"DEPLOY_SSH_KEY", "DEPLOY_KNOWN_HOSTS"}
    assert "printf '%s\\n' \"$DEPLOY_SSH_KEY\"" in key_step["run"]   # + the last newline


def test_the_deploy_job_checks_its_own_commit() -> None:
    steps = jobs()["deploy"]["steps"]
    assert not any("uses" in step for step in steps)          # no checkout: the server fetches
    assert jobs()["deploy"]["env"]["COMMIT"] == "${{ inputs.commit || github.sha }}"
    run = "\n".join(step["run"] for step in steps)
    assert '"deploy $COMMIT"' in run and "${COMMIT:0:12}" in run
    assert steps[-1]["if"] == "always()" and "rm -f ~/.ssh/deploy_key" in steps[-1]["run"]


def test_the_server_side_only_knows_three_commands() -> None:
    script = (ROOT / "deploy" / "ci-command.sh").read_text()
    for case in ("deploy:)", "rollback:)", "status:)", "*)"):
        assert f"    {case}" in script
    assert "^[0-9a-f]{40}$" in script
    assert 'GIT_SHA=$1 "$HOME/coursehub/deploy/rollout.sh"' in script


# ---------------------------------------------------------------- homework 63
def step(name: str) -> dict:
    return next(s for s in jobs()["deploy"]["steps"] if s["name"].startswith(name))


def test_homework_63_rolls_back_only_when_the_check_failed() -> None:
    check, rollback = step("Check it the way"), step("Roll back by itself")
    assert check["id"] == "check"
    # a failed DEPLOY step: rollout.sh already kept the old version - nothing to roll back
    assert rollback["if"] == "failure() && steps.check.outcome == 'failure'"
    assert rollback["run"].endswith('"$DEPLOY_HOST" rollback')


def test_homework_63_summary_and_webhook() -> None:
    summary, tell = step("Deploy summary"), step("Tell somebody")
    assert summary["if"] == "always()" and '>> "$GITHUB_STEP_SUMMARY"' in summary["run"]
    assert 'DEPLOY_SECONDS=' in step("Deploy this commit")["run"]
    assert tell["if"] == "failure()"
    assert tell["env"]["WEBHOOK_URL"] == "${{ secrets.DEPLOY_WEBHOOK_URL }}"
    assert "exit 0" in tell["run"]                 # no webhook secret: skip, don't fail


# ---------------------------------------------------------------- Video 64: build once
def test_the_image_is_built_once_tagged_with_the_commit_and_pushed() -> None:
    image = jobs()["image"]
    assert image["permissions"] == {"contents": "read", "packages": "write"}   # this job only
    build, push = image["steps"][1], image["steps"][-1]
    assert '-t "$IMAGE:$GITHUB_SHA"' in build["run"]         # one tag per commit
    assert push["if"] == "github.event_name != 'pull_request'"   # a PR builds, never pushes
    assert push["env"]["TOKEN"] == "${{ secrets.GITHUB_TOKEN }}"
    assert "--password-stdin" in push["run"] and ":latest" not in str(image)
    env = yaml.safe_load(WORKFLOW.read_text())["env"]
    assert env["IMAGE"] == env["IMAGE"].lower() and env["IMAGE"].startswith("ghcr.io/")


# ---------------------------------------------------------------- homework 64
def test_homework_64_size_budget_before_the_push() -> None:
    steps = jobs()["image"]["steps"]
    names = [s.get("name", "") for s in steps]
    budget = names.index("Image size budget - 300 MB")
    assert budget < names.index(steps[-1]["name"])        # the push is the last step
    assert '[ "$mb" -le 300 ]' in steps[budget]["run"]


def test_homework_64_version_tag_is_never_moved() -> None:
    push = jobs()["image"]["steps"][-1]["run"]
    assert 'docker manifest inspect "$IMAGE:$version"' in push   # exists already?
    assert push.index("manifest inspect") < push.index('docker push --quiet "$IMAGE:$version"')


# ---------------------------------------------------------------- Video 65
def test_the_alert_rules_are_tested_before_any_deploy() -> None:
    lint = " ".join(step.get("run", "") for step in jobs()["lint"]["steps"])
    assert "promtool test rules rules_test.yml" in lint and "check-config" in lint
