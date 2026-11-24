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
pytest --cov                          # 30 passed · coverage 98.50 %
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
