
# Flock Energy - Urja Meter Ops API

This repository provides a small read-only FastAPI adapter and React operations console for the legacy Urja Meter Ops portal. It keeps the portal session server-side, normalizes verified HTML surfaces, and exposes a clean versioned API to the browser.

## Current status

Portal reconnaissance verified `/login` and the browser-side JSON endpoints used by the meter and transformer pages. The HTML routes render an empty shell before the browser fetches those JSON records, so the backend reads the same authenticated JSON endpoints. No dedicated meter-detail endpoint has been verified; detail lookups remain search-based. See [PROTOCOL.md](PROTOCOL.md).

## Architecture

```text
Browser -> React UI -> FastAPI -> UrjaPortalClient -> Legacy Urja Portal
```

The client owns authentication and cookies. Parsers own HTML normalization. API routes own pagination, errors, and the browser contract. The browser never receives portal credentials. Live login uses only the backend-configured `URJA_USERNAME` and `URJA_PASSWORD`; the login endpoint does not accept caller-supplied credentials.

## Features

- Live meter register with search and pagination
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
GET /api/v1/hierarchy
```

The session routes control server-side adapter state and keep portal credentials off the browser. In demo mode, `authenticated` reflects the local simulation state only; it does not indicate an authenticated session with Urja.

The adapter reads the portal's live paginated meter and transformer records. It is intentionally read-only and does not provide meter registration.

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

The implementation favors a small in-memory session client over Redis or a database because the assignment scope is a single read-only adapter. It does not add a local index, bulk ingestion, invented hierarchy, or speculative upstream routes.

See [REFLECTION.md](REFLECTION.md) for assumptions, mistakes, and review notes.
