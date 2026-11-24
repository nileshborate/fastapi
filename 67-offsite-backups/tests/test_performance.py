# Video 66: two workers must not break /metrics - and the load test is never rate-limited
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from app import main

ROOT = Path(__file__).resolve().parents[1]


def test_two_workers_share_their_metrics(tmp_path: Path, monkeypatch) -> None:
    api = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]["api"]
    assert api["environment"]["WEB_CONCURRENCY"] == "${WEB_CONCURRENCY:-2}"
    assert api["environment"]["PROMETHEUS_MULTIPROC_DIR"] == "/tmp/prometheus"
    assert api["tmpfs"] == ["/tmp/prometheus:uid=10001"]       # empty at every start
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", str(tmp_path))
    with TestClient(main.app) as client:                         # the multiprocess path runs
        assert client.get("/metrics").status_code == 200


def test_only_the_load_test_machine_skips_the_rate_limit() -> None:
    conf = (ROOT / "nginx" / "default.conf").read_text()
    assert "limit_req_zone $perip_key zone=visitors" in conf
    geo = conf.split("geo $loadtest {")[1].split("}")[0]
    assert "default        0;" in geo and len(geo.strip().splitlines()) == 2   # ONE ip only
    assert "    0 $binary_remote_addr;\n    1 \"\";" in conf


def test_the_locustfile_only_reads() -> None:          # a load test must not fill the database
    text = (ROOT / "loadtest" / "locustfile.py").read_text()
    assert "self.client.get(" in text and "self.client.post(" not in text


def test_rollout_reads_nginx_s_log_after_a_reload() -> None:     # finding 2
    roll = (ROOT / "deploy" / "rollout.sh").read_text()
    i = roll.index("nginx -s reload")
    assert 'logs --since "$since" nginx' in roll[i:] and '"[emerg]"' in roll[i:]


def test_homework_66_only_the_course_list_is_cached_for_5_s() -> None:
    conf = (ROOT / "nginx" / "default.conf").read_text()
    courses = conf.split("location = /courses {")[1].split("}")[0]
    assert "proxy_cache courses;" in courses and "proxy_cache_valid 200 5s;" in courses
    assert "proxy_cache_lock on;" in courses
    assert conf.count("proxy_cache courses;") == 1            # /courses/{id}: never cached


def test_homework_66_steps_and_a_load_test_that_can_fail() -> None:
    steps = (ROOT / "loadtest" / "steps.py").read_text()
    assert "users = [100, 200, 400, 800]" in steps and "seconds = 30" in steps
    locustfile = (ROOT / "loadtest" / "locustfile.py").read_text()
    assert "environment.process_exit_code = 1" in locustfile and "p95 > 500" in locustfile
