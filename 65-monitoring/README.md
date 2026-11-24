# 65 – Monitoring and alerts: Prometheus reads our API, Slack hears when it breaks

**Video 65** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

Until now we found out about problems when a user told us. Today the server watches itself:
the API counts every request on `GET /metrics`, **Prometheus** reads those numbers every 15 s, three
**alert rules** decide when something is wrong – and **Alertmanager** posts it to a Slack channel.
Fixed? Slack hears that too.

Course Hub **1.14.0** (Video 64 + its homework):
```
users ──▶ nginx ──▶ api  ── GET /metrics (inside the network only) ◀── prometheus ── rules.yml
                     │                                                    │ firing
                    db                                                    ▼
                                                     alertmanager ──▶ Slack #coursehub-alerts
you ── ssh -L 9090 ──▶ the server's 127.0.0.1:9090  (Prometheus UI: graphs + alerts)
```

## Set it up once
1. **A Slack incoming webhook** (Slack → Apps → Incoming Webhooks → a channel, e.g. `#coursehub-alerts`).
   The URL is a secret – it goes into a FILE on the server, never into git:
   ```bash
   ssh deploy@api.example.com 'cat > slack_url' <<< 'https://hooks.slack.com/services/T…/B…/…'
   ```
   `deploy/server-setup.sh` adds `SLACK_URL_FILE=/home/deploy/slack_url` to `.env`; compose mounts it at
   `/run/secrets/slack_url`, and `alertmanager.yml` reads it with `api_url_file`.
2. **Push.** rollout.sh starts `prometheus` and `alertmanager` once, and reloads them (`SIGHUP`) when a
   file in `monitoring/` changed – after `promtool check config`.
3. **Look at it** – port 9090 is on the server's `127.0.0.1` only, so through an SSH tunnel:
   ```bash
   ssh -N -L 9090:localhost:9090 -L 9093:localhost:9093 deploy@api.example.com
   # then open http://localhost:9090 (Prometheus) and http://localhost:9093 (Alertmanager)
   ```

## On your laptop
```bash
cd 65-monitoring
cp .env.example .env && ./scripts/make-certs.sh
docker compose up -d --build --wait        # + prometheus + alertmanager (Slack URL: the example file)
pip install -r requirements-dev.txt
pytest --cov                               # 68 passed · coverage 98.95 %
docker run --rm -v "$PWD/monitoring:/m:ro" -w /m --entrypoint promtool prom/prometheus:v3.5.0 \
    test rules rules_test.yml              # the alert rules have unit tests too: SUCCESS
```

## Project – what's new
```
app/metrics.py              http_requests_total{method,route,status} · http_request_duration_seconds
                            (histogram) · http_requests_in_progress · coursehub_info{version,commit}
                            route = the TEMPLATE (/courses/{course_id}) - unknown URLs: "unmatched"
app/main.py                 MetricsMiddleware + GET /metrics (not in the docs)
nginx/default.conf          location = /metrics { return 404; }   - never public
monitoring/prometheus.yml   scrape every 15 s · finds EVERY api container by Docker DNS (dns_sd_configs) ·
                            external_labels: server: coursehub-1 on every alert
monitoring/rules.yml        ApiDown (absent(up == 1), 1m) · HighErrorRate (> 5 % 5xx, 2m) ·
                            SlowRequests (p95 > 0.5 s, 5m)
monitoring/rules_test.yml   promtool unit tests for the rules
monitoring/alertmanager.yml group_by alertname · group_wait 30s · group_interval 1m · repeat 4h ·
                            Slack, send_resolved: true
compose.yaml                prometheus + alertmanager - ports on 127.0.0.1 ONLY · volume promdata (15d)
deploy/rollout.sh           starts them once · config changed → promtool check → SIGHUP (no restart)
.github/workflows/ci-65.yml lint: promtool check config + promtool test rules + amtool check-config
tests/                      68 tests: + 6 for /metrics, + "the rules are tested before any deploy"
```

## Honest note – how I ran it
The stand-in lab from Videos 62–64 (an Ubuntu container as the server, a test DNS, Pebble, my git server,
my registry, my runner script). New today:
- **Prometheus 3.5.0 and Alertmanager 0.28.1** are the official release binaries from GitHub (checksums
  verified), in small local images – my machine can't pull from Docker Hub. compose.yaml uses the official
  images (`prom/prometheus:v3.5.0`, `prom/alertmanager:v0.28.1`); `.env` on my lab swaps the names.
- **Slack:** a tiny stand-in web server that prints every message it gets, with the time. Alertmanager sends
  exactly what it would send to `hooks.slack.com`.
- **No Grafana** – my machine can't download it. The graphs in the video are Prometheus's own UI (real
  screenshots, through the SSH tunnel). Grafana reads the same PromQL.

## What the runs showed – real numbers
Traffic during the runs: `/courses`, `/courses/999`, `/health/ready` in a loop (~5 requests a second).

| run | result |
|---|---|
| the first push (1.14.0) | all ✓ · 68 passed · 48.0 s · 6 containers, 9090/9093 on `127.0.0.1` only |
| from the internet | `https://…/metrics` → **404** · port 9090 → no connection |
| a scanner: 5 random URLs | the series count stays **4** – all five are one series, `route="unmatched"` |
| incident 1: the api stops (`group_interval: 5m`) | Slack: **FIRING ApiDown after 109 s** · RESOLVED **290 s** after the api was back |
| incident 2: the database stops | `/courses` 500 in **5.03 s** · `/health/ready` 503 · `/health/live` 200 → **FIRING HighErrorRate after 240 s** ("24.67% of the requests fail with a 5xx") + SlowRequests |
| 1.14.1: `group_interval: 1m` + `server: coursehub-1` | all ✓ · 55.4 s · **378 × 200** · `monitoring: the config changed - check + reload` – no restart |
| incident 1 again (1m) | FIRING after **131 s** · RESOLVED **60 s** after the api was back |

Everything Slack got:
```
07:01:54  FIRING: ApiDown: No Course Hub api answers Prometheus
07:06:54  RESOLVED: ApiDown: No Course Hub api answers Prometheus
07:10:54  FIRING: HighErrorRate: 24.67% of the requests fail with a 5xx
07:13:54  FIRING: SlowRequests: 95 % of the requests take up to 5s
07:15:54  RESOLVED: HighErrorRate: 5.717% of the requests fail with a 5xx
07:16:49  RESOLVED: SlowRequests: 95 % of the requests take up to 1.509s
07:19:24  FIRING: ApiDown: No Course Hub api answers Prometheus
07:20:24  RESOLVED: ApiDown: No Course Hub api answers Prometheus
```

### Finding 1 – `up == 0` never fired
My first ApiDown rule was `up{job="coursehub-api"} == 0`. With the api stopped, that query was **empty**:
Prometheus finds the api through Docker's DNS – a stopped container has no DNS name, so there is no target,
and no `up` at all. `absent(up{job="coursehub-api"} == 1)` asks the right question – "does ANY api answer?"
– and returned 1. (It also covers the rollout, when two api containers answer for a moment.)

### Finding 2 – "fixed" arrived 5 minutes late
The api was back in 3 s, but Slack heard RESOLVED **290 s** later – and every message came on a 5-minute beat
(07:01:54, 07:06:54, …). `group_interval: 5m`: after a group's first message, Alertmanager sends changes
only every 5 minutes – resolved included. With `1m` in 1.14.1: RESOLVED after **60 s**.

### Finding 3 – an alert is never instant – count it
ApiDown: a scrape every 15 s + `for: 1m` + `group_wait: 30s` → ~2 minutes. HighErrorRate: 30 s after the
database stopped, the 5xx ratio was only **1.4 %** – `rate(…[5m])` still remembered 5 minutes of 200s. It
crossed 5 % after ~90 s, then `for: 2m`, then 30 s → **240 s**. That's the price of no false alarms – choose it.

### Finding 4 – "up to 5s" was a lie of the histogram
`/courses` waited **5.03 s** for the dead database. My slowest bucket is 5 s – so every one of those requests
landed in `+Inf`, and `histogram_quantile` can only say "the top bucket": 5 s. Your buckets must reach past
your longest timeout.

### Finding 5 – the RESOLVED message shows an old number
"RESOLVED: HighErrorRate: **5.717%**…" – that's the last value while it was firing, not the value now. The
annotation is not re-evaluated after the alert stops. Read RESOLVED as "it's over", not as a measurement.

## Interview questions
1. **Pull vs push – how does Prometheus get the numbers?** It PULLS: every 15 s it calls `GET /metrics` on
   every target it found. A target that doesn't answer gets `up = 0` – the scrape itself is a health check.
2. **Why `/courses/{course_id}` and not `/courses/7` as the label?** Every distinct label value is a new
   time series in memory. A path with ids – or a scanner's random URLs – grows them without limit
   ("high cardinality"). Templates: a fixed, small set.
3. **What is `for:` in an alert rule, and Alertmanager's `group_wait` / `group_interval`?** `for:` – how long
   the condition must stay true before the alert fires (no alarm for one bad scrape). `group_wait` – wait that
   long so alerts firing together become one message. `group_interval` – how often a group may send changes,
   resolved included.

## Homework
1. **Route by severity:** `critical` alerts go to a second receiver (a "pager" webhook) and repeat every
   30 min; `warning` stays in Slack only.
2. **A rollout stuck halfway:** an alert `TwoVersionsRunning` – `coursehub_info` shows more than one version
   for 5 minutes (a normal rollout takes ~30 s).
3. **Fix SlowRequests honestly:** buckets up to 10 s, and a `promtool` unit test for SlowRequests.

Answer at the start of Video 66.
