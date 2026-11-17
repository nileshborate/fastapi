# 54 – API Versioning: v1 and v2 side by side, deprecation headers and the sunset

**Video 54** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project: a course API whose **v1** has old apps depending on it and whose **v2**
fixes its mistakes (a renamed field, the price as an exact `{amount, currency}` object, the teacher
as an object). Both versions run **side by side** as two mounted FastAPI apps with their **own docs**,
read and write **one store**, and every v1 response says **Deprecation**, **Sunset** and the
**successor** – until the sunset date, when v1 answers **410 Gone**.

## Run it
```bash
cd 54-api-versioning
pip install -r requirements.txt
fastapi dev app/main.py        # http://localhost:8000/v1/docs  ·  http://localhost:8000/v2/docs

python -m demos.breaking       # an old app on v1: "SQL JOINS - Rs 598" · on v2: KeyError 'name'
python -m demos.versions       # one store · deprecation headers on v1 only · Accept header · usage
python -m demos.sunset         # after the sunset: /v1 -> 410 Gone + successor · /v2 -> 200
pytest                         # 9 passed
```

## Project
```
app/
  store.py          CourseRecord - OUR model (price_paise: int) · COURSES · get_course · add_course
  v1/schemas.py     CourseV1 {id, name, teacher: str, price: int rupees}   - frozen forever
  v2/schemas.py     CourseV2 {id, title, teacher: {name}, price: {amount: "299.50", currency}, tags}
  v1/routes.py      GET /courses · GET /courses/{id} · POST /courses        (adapters to the store)
  v2/routes.py      the same three routes, v2 shapes
  deprecation.py    DeprecationMiddleware: Deprecation · Sunset · Link · 410 after the sunset · usage
  config.py         v1_deprecated_at 2026-11-01 · v1_sunset_at 2027-05-01 · deprecation_docs
  main.py           app.mount("/v1", v1) · app.mount("/v2", v2) · GET /courses/{id} by Accept header
demos/   breaking · versions · sunset         tests/   conftest · test_versions
```

## Breaking or not?
| change | breaking? |
|---|---|
| add a new endpoint, add an **optional** field to a response | no – same version |
| rename or remove a field (`name` → `title`) | **yes** |
| change a type (`price: 299` → `{"amount": "299.50"}`) | **yes** |
| make an optional input field required, tighten validation | **yes** |
| change the meaning of a value or a status code | **yes** |

## Two ways to choose a version
| | URL path `/v1/...` `/v2/...` | header `Accept: application/vnd.coursehub.v2+json` |
|---|---|---|
| easy to see / try in a browser | ✅ | ❌ |
| separate docs per version | ✅ (`/v1/docs`, `/v2/docs`) | harder |
| one URL per resource | ❌ | ✅ |
| caches | just work | need `Vary: Accept` |
This project uses the URL path, and shows the header way on `GET /courses/{id}`.

## Deprecation headers (RFC 9745 + RFC 8594)
```
Deprecation: @1793491200                                   # since 2026-11-01 00:00 UTC
Sunset: Sat, 01 May 2027 00:00:00 GMT                      # it stops working then
Link: </v2/courses/1>; rel="successor-version", <https://coursehub.example/docs/v1-sunset>; rel="deprecation"
```
After the sunset: `410 Gone` + `{"detail": "API v1 was removed. Please use v2.", "successor": "/v2/courses/1"}`.
`deprecated=True` on the router crosses out every v1 route in `/v1/docs`.

## Rules
- **Additive** changes need no new version. Only a **breaking** change does.
- Never change a released version – v1 stays exactly as it is until it is removed.
- One store, one internal model, a **thin adapter per version** (`from_record`) – not two copies of the logic.
- Money as an integer of paise inside, an exact Decimal string outside – never a float.
- Announce: `Deprecation`, `Sunset` (never earlier than the deprecation), `Link` to v2 and to the notice.
- Measure who still calls v1 (`X-Client-Id` → `/admin/v1-usage`) and talk to them before the sunset.
- After the sunset answer **410 Gone** with the successor – not a confusing 404.

## Interview questions
1. **When do you need a new API version?** Only for a breaking change: removing or renaming a field, changing a type or a meaning, or adding a required input. Additive changes – a new endpoint, a new optional field – go into the current version.
2. **URL versioning or header versioning?** URL versioning (`/v1`, `/v2`) is visible, easy to test and gives separate docs; header versioning keeps one URL per resource but is harder to try and needs `Vary: Accept` for caches. Both work; be consistent.
3. **How do you retire an old version?** Mark it deprecated in the docs and with `Deprecation`, `Sunset` and `Link` headers, publish a migration guide, track which clients still call it, contact them, and after the sunset date return `410 Gone` pointing to the successor.

## Homework
1. **An additive change:** add an optional `level` (`"beginner" | "intermediate" | "advanced"`, default `"beginner"`) to v2 only – v1 responses must not change at all.
2. **Another header:** `GET /courses/{id}` also accepts `API-Version: 2` (and `API-Version: 1`); an unknown version → **400**.
3. Tests for both.

Answer at the start of Video 55 (Structured Logging).
