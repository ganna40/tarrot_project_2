# Tarot Engine Lab

A source-traceable Tarot Engine v1. PostgreSQL and a deterministic rule engine decide the score, verdict, and three-card flow first; OpenAI is optional and only turns that plan into natural Korean. The `docs/` directory contains a static GitHub Pages client for interactive API verification.

## Current dataset

- 78 RWS card identities
- 156 approved `GENERAL` meanings: every card × upright/reversed
- 342 meaning-tag links
- 385 Golden Dawn correspondences
- 55 reusable relation rules
- 103 controlled semantic tags
- Source locators, rights basis, derivation status, and editorial review metadata

Meaning source: A. E. Waite, *The Pictorial Key to the Tarot*, Part III. Golden Dawn source: Book T / Liber LXXVIII material published in *The Equinox* I(8), 1912. The runtime Korean meanings are short editorial paraphrases rather than copied passages. Relation rules are explicitly marked `DESIGNED` and are not attributed to historical authors.

Detailed source decisions: [`docs/data/public-domain-source-register.md`](docs/data/public-domain-source-register.md)

## Architecture

```text
GitHub Pages validator
        │ POST /api/v1/readings
        ▼
Render FastAPI web service (HTTPS)
  ├─ question context classification
  ├─ PostgreSQL approved-knowledge lookup
  ├─ tag transition rules
  ├─ Golden Dawn elemental dignity modifier
  ├─ deterministic score, verdict, and flow
  └─ optional OpenAI wording
        │
        ▼
Render PostgreSQL
```

OpenAI API keys are never entered in the static page. `OPENAI_API_KEY` stays in the backend environment only.

## GitHub Pages

The repository includes `.github/workflows/pages.yml`, which publishes `docs/` as the web UI.

One-time repository setting:

```text
Settings → Pages → Build and deployment → Source: GitHub Actions
```

After that, pushes to `new` that change `docs/**` deploy automatically.

Public URL:

```text
https://ganna40.github.io/tarrot_project_2/
```

The Pages UI can run in local demo mode without any backend. For real engine verification, connect it to the Render HTTPS API described below.

## Deploy backend to Render

The root `render.yaml` provisions both a FastAPI web service and PostgreSQL in Render's Singapore region.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ganna40/tarrot_project_2/tree/new)

During the first Blueprint deployment Render asks for these secret values:

```text
API_ACCESS_KEY   a long random string you will also enter in the Pages API settings
OPENAI_API_KEY   your server-side OpenAI API key
OPENAI_MODEL     the OpenAI API model ID you want to use
```

`API_ACCESS_KEY` protects the public backend so other visitors cannot spend your OpenAI API quota. Never use the OpenAI API key itself as the browser access token.

The Blueprint automatically configures:

```text
Web service: tarot-engine-api-ganna40
Database:    tarot-engine-db-ganna40
Region:      Singapore
Plan:        Free
CORS:        https://ganna40.github.io
Health:      /health
Branch:      new
```

After Render reports the web service as Live, copy its HTTPS URL. It will be an `onrender.com` address assigned by Render.

Then open:

```text
https://ganna40.github.io/tarrot_project_2/
```

and configure `API 설정`:

```text
실행 모드: 원격 API
API 기본 URL: https://<your-render-service>.onrender.com
상담 엔드포인트: /api/v1/readings
Health 경로: /health
인증 방식: Bearer Token
백엔드 접근 토큰: the same API_ACCESS_KEY configured in Render
```

The browser sends only `API_ACCESS_KEY` to the backend. The OpenAI key remains exclusively in Render's server-side environment.

### Free-tier note

Render Free web services can spin down after inactivity, so the first request after a pause can take longer. Free Render Postgres is intended for evaluation and currently expires after its free retention period; upgrade or move the database before relying on it for persistent production data.

## Run backend locally

```bash
cp .env.example .env
docker compose up --build
```

PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Endpoints:

```text
API docs: http://localhost:8000/docs
Health:   http://localhost:8000/health
Reading:  http://localhost:8000/api/v1/readings
Legacy-compatible path: http://localhost:8000/api/consultation
```

For optional OpenAI wording:

```dotenv
OPENAI_API_KEY=...
OPENAI_MODEL=your_model_id
```

For optional public-backend access protection:

```dotenv
API_ACCESS_KEY=a-long-random-value
```

The static validator can send this value as a Bearer token or `X-API-Key`. Do not use the OpenAI key as the access token.

## Local static validator

Local serving is optional and mainly useful when testing an HTTP localhost backend, because an HTTPS GitHub Pages site cannot call an insecure HTTP backend in normal browsers.

```bash
python3 -m http.server 8080 --directory docs
```

PowerShell:

```powershell
py -m http.server 8080 --directory docs
```

## Curated-data workflow

```text
Public-domain source
→ deterministic generator
→ reviewable CSV package
→ structural/source validation
→ approved PostgreSQL seed
→ rule engine
```

Generate and validate:

```bash
python ingestion/build_public_domain_dataset.py
PYTHONPATH=backend python ingestion/validate_candidates.py
```

Load into a configured database:

```bash
PYTHONPATH=backend python ingestion/load_candidates.py --database-url "$DATABASE_URL"
```

Curated files live in `backend/data/curated/`. `APPROVED` means project source/structure/editorial review, not endorsement by an academic institution or professional diviner.

## API example

```bash
curl -X POST http://localhost:8000/api/v1/readings \
  -H "Content-Type: application/json" \
  -d '{
    "question": "게임을 만들면 투자를 받을 수 있을까?",
    "reading_context": "BUSINESS",
    "spread_type": "three_card",
    "cards": [
      {"code": "TEN_OF_SWORDS", "orientation": "UPRIGHT"},
      {"code": "EIGHT_OF_WANDS", "orientation": "UPRIGHT"},
      {"code": "HIEROPHANT", "orientation": "UPRIGHT"}
    ],
    "response_length": "SHORT",
    "include_trace": true,
    "use_llm": false
  }'
```

## Verification

```bash
python -m pip install -r backend/requirements.txt
python ingestion/build_public_domain_dataset.py
PYTHONPATH=backend python ingestion/validate_candidates.py
python -m pytest -q
npm test
npm run check:static
```

GitHub Actions repeats the dataset validator, backend tests, a real PostgreSQL schema/seed check, and the static UI tests.

## Core files

```text
render.yaml                  Render Web Service + PostgreSQL Blueprint
backend/app/curated_data.py   typed CSV loader and validator
backend/app/seed.py           idempotent public-domain seed
backend/app/models.py         normalized database models
backend/app/repository.py     approved knowledge and rule lookup
backend/app/engine.py         deterministic verdict and flow
backend/app/openai_service.py optional wording layer

ingestion/build_public_domain_dataset.py
ingestion/validate_candidates.py
ingestion/load_candidates.py

backend/data/curated/         reviewable source-derived package
docs/                         GitHub Pages validator
.github/workflows/pages.yml   GitHub Pages deployment
```
