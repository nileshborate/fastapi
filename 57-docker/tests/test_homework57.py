# Homework 57: the HEALTHCHECK script, tested against a real tiny HTTP server
import threading
from collections.abc import Callable, Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.healthcheck import check


def serve(status: int) -> HTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(status)
            self.end_headers()

        def log_message(self, *args: object) -> None:  # keep pytest's output clean
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)  # port 0 = any free port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture
def url() -> Iterator[Callable[[int], str]]:
    servers: list[HTTPServer] = []

    def make(status: int) -> str:
        servers.append(serve(status))
        return f"http://127.0.0.1:{servers[-1].server_port}/health/ready"

    yield make
    for server in servers:
        server.shutdown()


def test_ready_means_exit_code_0(url: Callable[[int], str]) -> None:
    assert check(url(200)) == 0


def test_not_ready_means_exit_code_1(url: Callable[[int], str]) -> None:
    assert check(url(503)) == 1


def test_nothing_listening_means_exit_code_1(url: Callable[[int], str]) -> None:
    server = serve(200)
    port = server.server_port
    server.shutdown()
    server.server_close()
    assert check(f"http://127.0.0.1:{port}/health/ready", timeout=0.5) == 1
