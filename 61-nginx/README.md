# 61 – Nginx + HTTPS in front of FastAPI

**Video 61** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

Uvicorn is an application server. In front of it, production puts a **reverse proxy**: one door for every request,
HTTPS, HTTP/2, compression, size and rate limits, security headers – and the app hides behind it.

Course Hub 1.10.0 (the code and the migrations from Video 60 + its homework, head **0005**):
```
browser / curl ──HTTPS──▶ nginx :443 ──HTTP──▶ api :8000 ──▶ db :5432
                http :80 ─▶ 301 https://...       (no published port)
```

## Run it
```bash
cd 61-nginx
cp .env.example .env                  # Windows: copy .env.example .env
./scripts/make-certs.sh               # our own dev CA + a certificate for localhost (Windows: Git Bash)
docker compose up -d --build --wait   # db -> migrate -> api -> nginx
curl --cacert certs/ca.crt https://localhost/health/ready
curl -I http://localhost/courses      # 301 -> https://localhost/courses

pip install -r requirements-dev.txt   # the tests need the db service: docker compose up -d db
pytest --cov                          # 35 passed · coverage 98.73 % (with the homework)
```
Ports 80 and 443 must be free on your machine. Browsers: import `certs/ca.crt` as a trusted authority – or
accept the warning. **Production:** a certificate from a real CA such as Let's Encrypt (Video 62).

## Project
```
nginx/default.conf       the server blocks: 80 -> 301 · 443: TLS, http2, headers, gzip, limits, proxy_pass
scripts/make-certs.sh    openssl: ca.key + ca.crt, server.key + server.crt (subjectAltName localhost, 127.0.0.1)
compose.yaml             + nginx (ports 80, 443) · the api: NO ports, FORWARDED_ALLOW_IPS: "*"
app/main.py              + GET /courses/{id} · POST sets Location (url_for) · GET /whoami
tests/test_proxy.py      4 tests: uvicorn's ProxyHeadersMiddleware - trusted vs untrusted, Location, the redirect
tests/test_nginx_conf.py 6 tests: default.conf parsed with crossplane + compose.yaml
.gitignore               + certs/ - a private key is never committed
```

## nginx/default.conf, the important lines
| | |
|---|---|
| `listen 80;` `return 301 https://$host$request_uri;` | port 80 only sends you to HTTPS |
| `listen 443 ssl;` `http2 on;` | TLS + HTTP/2 (since nginx 1.25.1: `http2 on;` – `listen … http2` is deprecated) |
| `ssl_protocols TLSv1.2 TLSv1.3;` | nothing older |
| `add_header … always;` (server level only) | HSTS, nosniff, `X-Frame-Options: DENY`, `Referrer-Policy` – **one `add_header` in a `location` would drop all of these there** |
| `server_tokens off;` | `server: nginx` instead of `server: nginx/1.28.0` |
| `gzip on; gzip_types application/json; gzip_min_length 1000;` | JSON is compressed; small answers are not |
| `client_max_body_size 1m;` | bigger bodies: 413 from nginx – the api never sees them |
| `limit_req zone=perip burst=20 nodelay;` `limit_req_status 429;` | 10 requests/s per IP, bursts of 20 |
| `proxy_set_header X-Forwarded-For / -Proto / Host / X-Real-IP` | tells the app who really asked, and how |
| `upstream api { zone …; server api:8000 resolve; }` + `resolver 127.0.0.11` | nginx looks the name up **again** when the container's address changes |
| compose: `./nginx:/etc/nginx/conf.d:ro` | the **folder**, not the file – see the findings |

## What the runs showed – real numbers
My machine can't reach Docker Hub, so two **local stand-ins** ran: PostgreSQL 16.15 (Videos 59–60) and
**nginx 1.28.0** – Ubuntu's package with the official image's `nginx.conf`, `conf.d` and logs to stdout
(`NGINX_IMAGE` in my `.env`). `compose.yaml` uses the official `nginx:1.28` for everyone else.

| | |
|---|---|
| `./scripts/make-certs.sh` | 0.31 s · `subject=CN = localhost` · `issuer=CN = Course Hub dev CA` · `DNS:localhost, IP Address:127.0.0.1` · 90 days |
| `docker compose up -d --wait` | 11.02 s · `docker compose ps`: api `8000/tcp` (not published) · nginx `0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp` |
| `curl -I http://localhost/courses` | `HTTP/1.1 301 Moved Permanently` · `Location: https://localhost/courses` |
| `curl https://localhost/...` without the CA | `curl: (60) SSL certificate problem: unable to get local issuer certificate` |
| a name that's not in the certificate | `curl: (60) SSL: no alternative certificate subject name matches target host name '127.0.0.2'` |
| `curl --cacert certs/ca.crt -v` | `SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384` · `ALPN: server accepted h2` · `HTTP/2 200` |
| `curl localhost:8000` (the api itself) | exit 7 – connection refused: nginx is the only way in |
| **without** `FORWARDED_ALLOW_IPS` | `/whoami`: `"client":"172.18.0.4"` (that's **nginx**), `"scheme":"http"` · `POST` → `location: http://localhost/courses/1` · `GET /courses/` → 307 `location: http://localhost/courses` – http links on an https site |
| **with** `FORWARDED_ALLOW_IPS: "*"` | `"client":"172.18.0.1"` (my curl, through Docker's gateway), `"scheme":"https"` · `location: https://localhost/courses/2` · 307 → `https://localhost/courses` |
| gzip, `GET /courses` (1,002 courses) | **98,831 bytes → 9,034 bytes** with `Accept-Encoding: gzip`; `/courses/1` (small): not compressed |
| `POST` with a 2 MB body | **413** – the api's log has no new `POST /courses` |
| 60 requests at once | **23 × 200, 37 × 429**; 3 s later: 200 again |
| `docker compose stop api` | **504 after 5.02 s** – `upstream timed out (110: Connection timed out) while connecting` (`proxy_connect_timeout 5s`) |
| `nginx -t` + `nginx -s reload` | `syntax is ok` · `test is successful` – a new config with no dropped connections |

**Finding 1 – uvicorn ignores the proxy headers by default.** It trusts `X-Forwarded-*` only from
`127.0.0.1` (`FORWARDED_ALLOW_IPS`). Nginx is another container, `172.18.0.4` – so `request.url` said `http`
and `url_for` built `http://` links. `FORWARDED_ALLOW_IPS: "*"` is safe **only** because the api has no
published port; a CIDR like `172.18.0.0/16` works too.

**Finding 2 – a single-file bind mount + `sed -i`.** I mounted `./nginx/default.conf` as a file, edited it with
`sed -i`, reloaded – and nothing changed. `stat -c %i`: the container's file was inode **1925288**; after
`sed -i` the file on disk was **1925164** – `sed -i` (and many editors) write a **new** file, the container still
sees the old one. Mounting the **folder** fixed it: `server_tokens` commented out + reload → `server: nginx/1.28.0`;
back on + reload → `server: nginx`.

**Finding 3 – nginx remembers the api's address.** With a plain `server api:8000;` nginx looks the name up once,
at start. I stopped api, let another container take its address (`172.18.0.3`), started api (now `172.18.0.5`):
**502 for 25 seconds and counting** – `connect() failed (111: Connection refused) … upstream: "http://172.18.0.3:8000"`.
With `zone` + `server api:8000 resolve;` + `resolver 127.0.0.11 valid=10s;` (nginx 1.27.3+): **200 after 2 s**.

**CI (`.github/workflows/ci-61.yml`)**, run the way a runner does: lint ✓ · test: **30 passed** (98.50 %) ·
nginx job: certificates 0.44 s · `nginx -t` ✓ · `up -d --wait` 10.91 s · `301 https://localhost/health/live` ·
`"revision":"0005"` over HTTPS · `strict-transport-security` ✓ · port 8000 not reachable ✓. (My run used the
stand-in images, built before – `--build` needs Docker Hub.) `actionlint` + the JSON schema check: ok.

## Interview questions
1. **Why put Nginx in front of uvicorn?** One entry point that ends TLS, speaks HTTP/2, compresses, limits body
   size and request rate, adds security headers, buffers slow clients – and the app has no public port.
2. **Behind a proxy, `request.url` says `http` and the client IP is the proxy's. Why, and how do you fix it?**
   The proxy opens a new connection. It passes the original in `X-Forwarded-For` / `-Proto`; the app server must
   trust those headers – but **only** from the proxy (uvicorn: `FORWARDED_ALLOW_IPS`), or anyone could fake them.
3. **502 or 504 – what's the difference?** 502 Bad Gateway: the upstream refused or sent a broken answer
   (connection refused). 504 Gateway Timeout: it didn't answer in time (`proxy_connect_timeout`, `proxy_read_timeout`).

## Homework
1. **A stricter limit for writes:** `POST /courses` at most 2 requests/s per IP in its own `location` – and keep
   the security headers there (the `add_header` trap).
2. **A JSON access log:** `log_format` with `$request_time` and `$upstream_response_time`, plus a request id
   (`$request_id`) sent to the api as `X-Request-ID` – and find it in the api's log (Video 55).
3. **Static files from nginx:** a `/docs-site/` folder served by nginx itself with `Cache-Control` and `gzip` –
   the api never sees those requests.

Answer at the start of Video 62 (deploy to a cloud VM).

## Homework answer (shown at the start of Video 62)

The homework changed this folder: the app is now **1.10.1** (`app/request_log.py`), `nginx/default.conf` has a
write limit, a JSON access log and a static location, and there's a new `docs-site/` folder. The numbers in the
sections above are from Video 61 (1.10.0). Tests: **35 passed** · coverage **98.73 %**
(`tests/test_request_log.py` + 3 new tests in `tests/test_nginx_conf.py`).

### 1. A stricter limit for writes – and the second inheritance trap
```nginx
map $request_method $write_key { POST $binary_remote_addr; default ""; }  # an EMPTY key is never counted
limit_req_zone $write_key zone=writes:10m rate=2r/s;

location = /courses {
    limit_req zone=perip burst=20 nodelay;     # listed AGAIN - see below
    limit_req zone=writes burst=4 nodelay;
    proxy_pass http://api;
}
```
The proxy settings (`proxy_set_header`, the timeouts) moved to the **server** level, so every location with a
`proxy_pass` inherits them. Measured:

| | |
|---|---|
| 10 `POST /courses` at once | **5 × 201, 5 × 429** (burst 4 + 1) |
| 6 POSTs one after another | `201 201 201 201 201 429` |
| a 429 from the write limit | still has `strict-transport-security` – no `add_header` in the location |
| 60 `GET /courses` at once | 24 × 200, 36 × 429 – the per-IP limit, not the write limit |

**Finding – `limit_req` is inherited like `add_header`.** With only `limit_req zone=writes` in the location,
60 `GET /courses` at once gave **60 × 200** – the server's per-IP limit was gone there – while
`/health/live` (location `/`) still gave 23 × 200, 37 × 429. A `limit_req` in a location **replaces** the
server's ones (nginx docs: "inherited from the previous level if and only if there are no limit_req
directives defined on the current level"). So `perip` is listed again, and a test checks it.

### 2. A JSON access log with a request id
`log_format json_access escape=json '{…"request_id":"$request_id",…"request_time":$request_time,
"upstream_response_time":"$upstream_response_time"…}'` · `proxy_set_header X-Request-ID $request_id;` ·
`add_header X-Request-ID $request_id always;` – the api logs it (`app/request_log.py`, a small Video 55).

```
$ curl -D - https://localhost/courses/1 | grep x-request-id
x-request-id: b4ca6ebfb023f54d712e5924b258d3d4
$ docker compose logs nginx | grep b4ca6ebf
{"time":"2026-11-17T06:47:51+00:00","request_id":"b4ca6ebfb023f54d712e5924b258d3d4","remote_addr":"172.18.0.1",
 "request":"GET /courses/1 HTTP/2.0","status":200,"bytes":68,"request_time":0.007,"upstream_response_time":"0.007",…}
$ docker compose logs api | grep b4ca6ebf
{"event": "request.done", "request_id": "b4ca6ebfb023f54d712e5924b258d3d4", "method": "GET",
 "path": "/courses/1", "status": 200, "duration_ms": 3.8}
```
One id, both logs. `request_time` is the whole request in nginx (7 ms), `upstream_response_time` only the api
(7 ms – the api itself measured 3.8 ms of it). A static file: `"request_time":0.000,"upstream_response_time":""`
– no upstream at all. `upstream_response_time` is a **string** in the format: for a 429 or a static file it's
empty, and with retries it can be `"0.004, 0.002"`.

### 3. Static files from nginx
`location /docs-site/ { root /srv; expires 1h; }` + `./docs-site:/srv/docs-site:ro` in compose.yaml:

| | |
|---|---|
| `GET /docs-site/index.html` | 200 · `cache-control: max-age=3600` · `expires` · `etag` · all 5 security headers · `content-encoding: gzip` |
| sizes | index.html **2,027 → 906 bytes** with gzip · style.css **1,050 → 545 bytes** (`text/css` added to `gzip_types`) |
| again with `If-None-Match` | **304, 0 bytes** |
| a missing file | 404 – from nginx |
| the api's log | **0** lines with `docs-site` |

**The `add_header` trap, measured.** With `add_header Cache-Control "public, max-age=3600";` in that location
instead of `expires 1h;`, the answer had **only** `cache-control: public, max-age=3600` – no HSTS, no
nosniff, no `X-Frame-Options`, no `Referrer-Policy`, no `X-Request-ID`. With `expires 1h` all of them are back.
`expires` is its own directive, so it doesn't trigger the trap.

**ci-61 again, with the homework** (run the way a runner does): lint ✓ · **35 passed** (98.73 %) · `nginx -t` ✓ ·
`up -d --wait` 10.76 s · `"version":"1.10.1","revision":"0005"` over HTTPS · HSTS ✓ · port 8000 closed ✓.
