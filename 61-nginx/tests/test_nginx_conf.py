# nginx/default.conf and compose.yaml are code too: parse them, check the rules of the video
from pathlib import Path

import crossplane
import yaml

ROOT = Path(__file__).resolve().parents[1]


def parsed() -> list[dict]:
    # a conf.d file: it has no http { } around it - so don't check the context
    result = crossplane.parse(str(ROOT / "nginx" / "default.conf"), single=True,
                              comments=False, check_ctx=False, check_args=False)
    assert result["status"] == "ok", result["errors"]
    return result["config"][0]["parsed"]


def find(block: list[dict], name: str) -> list[dict]:
    return [d for d in block if d["directive"] == name]


def servers() -> dict[str, list[dict]]:
    return {find(s["block"], "listen")[0]["args"][0]: s["block"]
            for s in find(parsed(), "server")}


def args(block: list[dict], name: str) -> list[list[str]]:
    return [d["args"] for d in find(block, name)]


def test_port_80_only_redirects_to_https() -> None:
    assert args(servers()["80"], "return") == [["301", "https://$host$request_uri"]]


def test_https_with_modern_tls_and_http2() -> None:
    https = servers()["443"]
    assert args(https, "http2") == [["on"]]
    assert args(https, "ssl_protocols") == [["TLSv1.2", "TLSv1.3"]]
    assert args(https, "server_tokens") == [["off"]]


def test_security_headers_only_on_the_server() -> None:
    https = servers()["443"]
    names = {a[0] for a in args(https, "add_header")}
    assert {"Strict-Transport-Security", "X-Content-Type-Options", "X-Frame-Options"} <= names
    assert all(a[-1] == "always" for a in args(https, "add_header"))
    for location in find(https, "location"):         # one add_header here would drop them all
        assert not find(location["block"], "add_header")


def test_the_proxy_passes_the_client_on() -> None:
    https = servers()["443"]
    headers = dict(args(https, "proxy_set_header"))     # on the server: for every location
    assert headers["X-Forwarded-Proto"] == "$scheme"
    assert headers["X-Forwarded-For"] == "$proxy_add_x_forwarded_for"
    assert headers["X-Request-ID"] == "$request_id"     # homework 61: the same id in both logs
    for location in find(https, "location"):         # one here would drop all the others
        assert not find(location["block"], "proxy_set_header")
        if location["args"] != ["/docs-site/"]:
            assert args(location["block"], "proxy_pass") == [["http://api"]]


def test_limits_and_compression() -> None:
    https = servers()["443"]
    assert args(https, "client_max_body_size") == [["1m"]]
    assert args(https, "limit_req_status") == [["429"]]
    assert "application/json" in args(https, "gzip_types")[0]


def test_only_nginx_is_published() -> None:
    services = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]
    assert "ports" not in services["api"]
    assert services["api"]["environment"]["FORWARDED_ALLOW_IPS"] == "*"
    assert services["nginx"]["ports"] == ["80:80", "443:443"]


def test_writes_have_their_own_limit() -> None:                     # homework 61.1
    assert ["$write_key", "zone=writes:10m", "rate=2r/s"] in args(parsed(), "limit_req_zone")
    key = find(parsed(), "map")[0]
    assert key["args"] == ["$request_method", "$write_key"]
    assert {d["directive"]: d["args"] for d in key["block"]} == {
        "POST": ["$binary_remote_addr"], "default": [""]}   # an empty key is never counted
    courses = [loc for loc in find(servers()["443"], "location")
               if loc["args"] == ["=", "/courses"]]
    # a limit_req in a location REPLACES the server's one - so perip is listed again
    assert args(courses[0]["block"], "limit_req") == [
        ["zone=perip", "burst=20", "nodelay"], ["zone=writes", "burst=4", "nodelay"]]


def test_a_json_access_log_with_the_request_id() -> None:            # homework 61.2
    log_format = find(parsed(), "log_format")[0]["args"]
    assert log_format[:2] == ["json_access", "escape=json"]
    line = "".join(log_format[2:])
    for variable in ("$request_id", "$request_time", "$upstream_response_time", "$status"):
        assert variable in line
    https = servers()["443"]
    assert args(https, "access_log") == [["/var/log/nginx/access.log", "json_access"]]
    assert ["X-Request-ID", "$request_id", "always"] in args(https, "add_header")


def test_static_files_come_from_nginx() -> None:                     # homework 61.3
    docs = [loc for loc in find(servers()["443"], "location") if loc["args"] == ["/docs-site/"]]
    block = docs[0]["block"]
    assert args(block, "root") == [["/srv"]] and args(block, "expires") == [["1h"]]
    assert not find(block, "proxy_pass") and not find(block, "add_header")
    assert (ROOT / "docs-site" / "index.html").is_file()
    nginx = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]["nginx"]
    volumes = nginx["volumes"]
    assert "./docs-site:/srv/docs-site:ro" in volumes
