# Homework 53: idempotent emails (SET NX) and a nightly cleanup
import fakeredis
from celery.schedules import crontab
from fastapi.testclient import TestClient

from app import email_server
from app.celery_app import celery_app
from app.tasks import cleanup


def test_second_email_is_skipped(client: TestClient, notes: fakeredis.FakeRedis) -> None:
    first = client.post("/emails", json={"to": "asha@example.com"})
    assert client.get(first.headers["location"]).json()["result"]["attempts"] == 3
    second = client.post("/emails", json={"to": "asha@example.com"})
    assert client.get(second.headers["location"]).json()["result"] == {
        "to": "asha@example.com", "skipped": True}
    assert email_server.attempts["asha@example.com"] == 3        # not a 4th time
    assert 3500 < notes.ttl("sent:asha@example.com") <= 3600


def test_a_failed_email_frees_the_key(client: TestClient, notes: fakeredis.FakeRedis) -> None:
    response = client.post("/emails", json={"to": "down@example.com"})
    assert client.get(response.headers["location"]).json()["state"] == "FAILURE"
    assert notes.exists("sent:down@example.com") == 0             # it was never sent


def test_cleanup(notes: fakeredis.FakeRedis) -> None:
    notes.rpush("heartbeats", "02:00:00", "02:00:05")
    assert cleanup.delay().get() == 2
    assert notes.exists("heartbeats") == 0
    entry = celery_app.conf.beat_schedule["cleanup-2-am"]
    assert entry["task"] == "app.tasks.cleanup"
    assert entry["schedule"] == crontab(hour=2, minute=0)
