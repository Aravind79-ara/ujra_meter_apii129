
# Flock Energy - Urja Meter Ops API

This repository provides a small read-only FastAPI adapter and React operations console for the legacy Urja Meter Ops portal. It keeps the portal session server-side, normalizes verified HTML surfaces, and exposes a clean versioned API to the browser.

## Current status

Portal reconnaissance verified `/login`, `/`, `/meters`, and `/transformers`, including the form fields and session cookie behavior. No dedicated meter-detail endpoint or live consumption endpoint has been verified, so detail lookups remain list-based and the consumption contract remains intentionally limited. See [PROTOCOL.md](PROTOCOL.md).

## Architecture

```text
Browser -> React UI -> FastAPI -> UrjaPortalClient -> Legacy Urja Portal
```

The client owns authentication and cookies. Parsers own HTML normalization. API routes own pagination, errors, and the browser contract. The browser never receives portal credentials. Live login uses only the backend-configured `URJA_USERNAME` and `URJA_PASSWORD`; the login endpoint does not accept caller-supplied credentials.

## Features

- Meter register with search and pagination
- Meter detail view
- Verified hierarchy/transformer page adapter
- Responsive operations dashboard
- Session reauthentication and normalized errors
- FastAPI OpenAPI documentation

## Stack

Backend: Python 3.10+, FastAPI, Pydantic, httpx, BeautifulSoup4, pytest.

Frontend: React, JavaScript, Vite, TanStack Query, React Router, Lucide icons, CSS responsive layout.

## Run locally

Prerequisites: Python 3.10+, Node.js 18+, and npm.

```powershell
Copy-Item .env.example .env
# DEMO_MODE=true provides local sample data; set it to false for live Urja data.
# Fill URJA_USERNAME and URJA_PASSWORD when DEMO_MODE=false; never commit .env.

python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The UI is at `http://localhost:3000`. API docs are at `http://localhost:8000/docs`, `/redoc`, and `/openapi.json`.

## API

```text
GET /api/v1/health
GET /api/v1/session
POST /api/v1/session/login
POST /api/v1/session/logout
GET /api/v1/meters?page=1&page_size=20&search=...
GET /api/v1/meters/{meter_id}
GET /api/v1/meters/{meter_id}/consumption
GET /api/v1/hierarchy
```

The consumption route exists as an explicit contract boundary: live mode returns `501` until a real portal endpoint is verified, while demo mode returns synthetic sample readings clearly labeled as demo data. The sample readings are not real utility measurements and are only included for local UI validation. The session routes control server-side adapter state and keep portal credentials off the browser. In demo mode, `authenticated` reflects the local simulation state only; it does not indicate an authenticated session with Urja.

The portal currently reports zero meters. This service is intentionally read-only and does not provide meter registration. A meter must be registered by an authorized operator in Urja or its upstream utility system, after which refreshing the register will discover it.

## Tests and validation

```powershell
python -m pytest backend\tests -q
cd frontend
npm run build
```

The automated tests do not depend on the live portal. Live reconnaissance is documented separately because it requires the configured credentials and must remain read-only.

## Docker

`docker-compose.yml` provides the backend and a Vite development server for the frontend; it does not serve a production static build. Supply a local `.env` at runtime; portal credentials are read from the backend environment and are never placed in the image.

## Design decisions and omissions

The implementation favors a small in-memory session client over Redis or a database because the assignment scope is a single read-only adapter. It does not add a local index, bulk ingestion, invented hierarchy, or speculative upstream routes. The next high-value step is authenticated browser network capture, followed by fixtures and consumption support.

See [REFLECTION.md](REFLECTION.md) for assumptions, mistakes, and review notes.
