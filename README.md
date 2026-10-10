# Urja Meter Ops — Read-Only API Adapter & Operations Console

A full-stack prototype that wraps the legacy **Urja Meter Ops** portal in a versioned **FastAPI** interface and a **React + Vite** operations console. The backend owns the portal session, fetches portal pages, normalizes supported table fields, and returns structured JSON to the frontend.

<p align="left">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white" />
  <img alt="React" src="https://img.shields.io/badge/UI-React-61DAFB?logo=react&logoColor=black" />
  <img alt="Vite" src="https://img.shields.io/badge/Build-Vite-646CFF?logo=vite&logoColor=white" />
  <img alt="Status" src="https://img.shields.io/badge/status-prototype-orange" />
</p>

> **Scope and data integrity:** This adapter is read-only. It does not create or modify meters in Urja. The portal's browser UI has been observed displaying a populated meter register (403 total in the supplied capture) and transformer rows. That visible UI is not, by itself, proof that the current backend parser returns every upstream row. The live response must be checked with the configured credentials. Consumption remains demo-only until a real upstream consumption endpoint is verified.

## Contents

- [Highlights](#highlights)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Repository layout](#repository-layout)
- [Requirements](#requirements)
- [Run locally](#run-locally)
- [Demo mode and live mode](#demo-mode-and-live-mode)
- [API reference](#api-reference)
- [Meter data mapping](#meter-data-mapping)
- [Errors and troubleshooting](#errors-and-troubleshooting)
- [Tests and build checks](#tests-and-build-checks)
- [Docker development setup](#docker-development-setup)
- [Security notes](#security-notes)
- [Known limitations and next steps](#known-limitations-and-next-steps)
- [Related documentation](#related-documentation)

## Highlights

- **Versioned API:** endpoints under `/api/v1` for health, session state, meter register, meter lookup, transformer listing, and consumption contract boundary.
- **Server-side portal session:** HTTPX maintains upstream cookies in the backend; portal credentials are not sent to the React application.
- **HTML normalization:** BeautifulSoup extracts supported fields from table-based pages and maps them into Pydantic response models.
- **Search and pagination:** the meter-list API accepts `search`, `page`, and `page_size` query parameters.
- **Demo fixtures:** run the UI and API without connecting to the live portal.
- **Consistent errors:** HTTP and validation errors use a JSON envelope.
- **Interactive API documentation:** FastAPI serves Swagger UI, ReDoc, and an OpenAPI schema.
- **Responsive operations UI:** React routes for the meter register, meter views, transformers, and consumption demo/placeholder.

## Architecture

```text
┌────────────────────────────┐
│      React + Vite UI       │
│    Browser / Operations    │
└─────────────┬──────────────┘
              │ JSON over HTTP
              ▼
┌────────────────────────────┐
│       FastAPI API          │
│        /api/v1/*           │
├────────────────────────────┤
│ Routes · validation · API  │
│ response/error contracts   │
└─────────────┬──────────────┘
              │
       ┌──────┴────────┐
       ▼               ▼
┌──────────────┐  ┌───────────────┐
│ Portal client│  │ Demo fixtures │
│ HTTPX/cookies│  │ local samples │
└──────┬───────┘  └───────────────┘
       │
       ▼
┌────────────────────────────┐
│   Urja Meter Ops portal    │
│ /login · /meters ·         │
│ /transformers              │
└────────────────────────────┘
```

### Design boundaries

- `UrjaPortalClient` owns upstream HTTP requests, the in-memory cookie jar, and reauthentication behavior.
- Parsers convert upstream HTML tables into typed models; routes handle filtering, pagination, and API errors.
- Demo mode returns local sample data instead of live portal records.
- One shared `UrjaPortalClient` is created per backend process. This is a single-operator prototype, not isolated per-user session management.
- The API is read-only against Urja. No upstream write operations are implemented.

## Technology stack

| Layer | Main technologies |
|---|---|
| Backend | Python 3.10+, FastAPI, Uvicorn, Pydantic Settings, HTTPX, BeautifulSoup |
| Frontend | React 18, Vite, React Router, TanStack Query, Lucide React |
| Tests | pytest, pytest-asyncio, FastAPI test utilities |
| API description | OpenAPI, Swagger UI, ReDoc |
| Local orchestration | Docker Compose (development setup) |

## Repository layout

```text
ujra_meter_apii129/
├── backend/
│   ├── app/
│   │   ├── core/config.py       # Environment-backed settings
│   │   ├── client.py            # Portal HTTP client and session
│   │   ├── demo_data.py         # Local sample records
│   │   ├── models.py            # Pydantic API schemas
│   │   ├── parsers.py           # HTML table parsers
│   │   └── main.py              # FastAPI app and routes
│   ├── tests/                   # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── services/api.js      # Frontend API calls
│   │   └── App.jsx              # Application UI and routes
│   ├── package.json
│   └── vite.config.js
├── .env.example                # Environment template
├── docker-compose.yml
├── openapi.json                # Committed OpenAPI snapshot
├── PROTOCOL.md                 # Portal reconnaissance and field mapping
├── REFLECTION.md               # Decisions, assumptions, and learnings
└── README.md
```

## Requirements

- Python **3.10 or newer**
- Node.js **18 or newer** and npm
- Git
- Optional: Docker Desktop with Docker Compose
- Authorized Urja portal credentials for live mode

## Run locally

The instructions below use **Windows PowerShell** and assume commands are run from the repository root.

### 1. Clone the repository and create configuration

```powershell
git clone https://github.com/Aravind79-ara/ujra_meter_apii129.git
cd ujra_meter_apii129
Copy-Item .env.example .env
```

The backend loads `.env` from the **repository root**. Do not place secrets in the frontend environment or commit `.env`.

### 2. Choose demo mode for the first run

Open the root `.env` and set:

```dotenv
DEMO_MODE=true
```

Demo mode is the easiest way to check that the API and frontend start without contacting Urja. The sample records and consumption readings are synthetic.

### 3. Create a Python environment and install backend dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

If PowerShell blocks environment activation, install using the virtual environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### 4. Start the backend

From the repository root, run:

```powershell
python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

The API is available at `http://127.0.0.1:8000`.

### 5. Start the frontend in a second terminal

```powershell
cd frontend
npm install
npm run dev
```

Vite is configured to use port `3000`. Open `http://localhost:3000`.

### 6. Explore the API

- **Swagger UI:** <http://127.0.0.1:8000/docs>
- **ReDoc:** <http://127.0.0.1:8000/redoc>
- **Runtime OpenAPI schema:** <http://127.0.0.1:8000/openapi.json>
- **Health endpoint:** <http://127.0.0.1:8000/api/v1/health>

## Demo mode and live mode

### Demo mode

Set `DEMO_MODE=true` in the root `.env`. The API returns local fixtures for the meter register, hierarchy, and consumption. Demo session state is a simulation and does **not** mean the backend is authenticated to Urja.

### Live mode

Set the following values in the root `.env`:

```dotenv
URJA_BASE_URL=https://urja-ops.flockenergy.tech
URJA_USERNAME=your_authorized_username
URJA_PASSWORD=your_authorized_password
DEMO_MODE=false
```

Restart Uvicorn after changing configuration.

In live mode, the backend logs in with the configured credentials, keeps the session cookie on the server, and requests the portal's `/meters` and `/transformers` pages. A successful browser login does not share its cookie with the backend; FastAPI must authenticate its own independent HTTPX session.

A visible record count in the browser does not guarantee that the adapter has parsed the same records. If the API returns `200` with `total: 0`, inspect the backend response and compare its authenticated HTML with the browser's Network panel. The current parser is table-based, so the adapter needs HTML with the expected table structure to extract rows.

### Environment variables

| Variable | Default / example | Purpose |
|---|---|---|
| `URJA_BASE_URL` | `https://urja-ops.flockenergy.tech` | Upstream portal URL |
| `URJA_USERNAME` | Empty | Authorized username for live mode |
| `URJA_PASSWORD` | Empty | Authorized password for live mode |
| `DEMO_MODE` | `false` | Use local fixtures when `true`; use the live adapter when `false` |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend CORS origin |
| `REQUEST_TIMEOUT` | `15` seconds | Timeout for upstream HTTP requests |
| `LOG_LEVEL` | `INFO` | Configured log level |
| `API_HOST` | `0.0.0.0` | Intended API bind host; local command above explicitly binds `127.0.0.1` |
| `API_PORT` | `8000` | Intended API port; local command above explicitly uses port `8000` |
| `VITE_API_URL` | `http://127.0.0.1:8000/api/v1` | Frontend API base URL; configured in the frontend build environment, not the backend `.env` |

For a deployed frontend, set `VITE_API_URL` to the reachable backend base URL **including `/api/v1`**. The localhost default works only when the browser can access the backend at that loopback address.

## API reference

All application routes use the `/api/v1` prefix.

| Method | Endpoint | Description | Notes |
|---|---|---|---|
| `GET` | `/health` | API and upstream reachability | In demo mode reports `upstream: "demo"`; live mode checks the portal login page responds. It is not proof of an authenticated session. |
| `GET` | `/session` | Adapter session state | Reflects the backend's single in-memory session. |
| `POST` | `/session/login` | Authenticate with backend-configured credentials | Bodyless request; credentials are not accepted from the frontend. |
| `POST` | `/session/logout` | Clear local adapter cookies/session state | Does not log out the independent browser session. A later data request can trigger login again. |
| `GET` | `/meters` | List normalized meter records | Supports `page`, `page_size` (1–100), and `search`. |
| `GET` | `/meters/{meter_id}` | Look up a meter | Searches the normalized meter register; no separate upstream detail page is implemented. |
| `GET` | `/meters/{meter_id}/consumption` | Consumption contract boundary | Demo mode returns synthetic readings; live mode returns `501` until a real upstream endpoint is verified. |
| `GET` | `/hierarchy` | Transformer page adapter | Current live parser returns flat transformer nodes; parent-child relationships are not reconstructed. |

### Request examples

List the first 20 records:

```http
GET /api/v1/meters?page=1&page_size=20
```

Search the parsed fields:

```http
GET /api/v1/meters?search=installed
```

Look up a meter identifier:

```http
GET /api/v1/meters/J100000
```

Retrieve transformer data:

```http
GET /api/v1/hierarchy
```

The meter ID above is an example based on the portal screen. Use an identifier that actually exists in the live response or the local demo dataset.

### Error response shape

API errors use this envelope:

```json
{
  "error": {
    "code": "METER_NOT_FOUND",
    "message": "Meter was not found in the portal."
  }
}
```

Common status codes:

| Status | Meaning |
|---|---|
| `400` | Required live configuration is missing |
| `401` | Portal authentication failed |
| `404` | Meter was not found |
| `422` | Invalid query parameter or request input |
| `501` | Live consumption endpoint has not been verified |
| `502` | Upstream request or response failure |
| `503` | Required service configuration is unavailable |
| `504` | Upstream request timed out |

The exact status depends on the path that failed. Inspect the response `error.code` and backend terminal output when troubleshooting.

## Meter data mapping

The portal's browser table has shown columns such as **Meter**, **Serial**, **Make**, **Phase**, **Status**, and **DT**. The current API model does not yet expose all those columns as dedicated top-level fields.

| Portal table field | Current API mapping | Current limitation |
|---|---|---|
| Meter | `id` | Parsed from the `meter`/ID column or, when present, the row link text |
| Serial | `serial_number` | Recognized from supported serial-number headers |
| Status | `status` | Recognized from `status` / `state` headers |
| Location / Address | `location` | Optional; only present if the source page includes it |
| Feeder / Transformer / Substation / Network | `network` object | Only recognized source headers are retained |
| Make | Not currently modeled | Requires adding a model field and parser mapping |
| Phase | Not currently modeled | Requires adding a model field and parser mapping |
| DT | Not currently modeled as a dedicated field | Requires explicit mapping, e.g. into a transformer/network field according to the API contract |

Unknown values are not invented. Extend the Pydantic `Meter` model, parser, fixtures, frontend display, and tests together when adding columns.

## Errors and troubleshooting

### The dashboard says “Demo”

Check `DEMO_MODE` in the **root** `.env`. `DEMO_MODE=true` intentionally uses local fixtures. Set it to `false`, configure the portal credentials, and restart the backend to attempt live access.

### Login fails in live mode

Check the configured base URL and credentials. A browser session is independent of the backend's HTTPX session. If login still fails, inspect the request URL, HTTP status, response content type, redirect location, and whether the expected session cookie was set. Never share the cookie value, password, or authorization headers.

### Meter endpoint returns `200` but `total` is zero

This usually means the API route did not extract rows from the content it received. Compare the authenticated `/meters` HTML received by the backend with the actual browser's Network response. Check whether rows exist in server-returned HTML or are loaded through a separate Fetch/XHR request. If the browser loads the data separately, implement the observed, authorized upstream request rather than guessing a new endpoint.

### The frontend cannot reach FastAPI

Check that Uvicorn is running on port `8000` and that `VITE_API_URL` points to the correct `/api/v1` base URL. A browser visiting a deployed frontend interprets `127.0.0.1` as the visitor's own computer, not the deployed backend.

### CORS blocks a request

Make sure `FRONTEND_URL` matches the frontend origin exactly (scheme, host, and port). For deployment, configure a specific origin allowlist rather than relying on local development origins.

### Consumption returns `501`

This is intentional in live mode. The adapter does not invent a consumption endpoint or reading contract. Demo readings are synthetic and must not be treated as real utility data.

## Tests and build checks

Run backend tests from the repository root:

```powershell
python -m pytest backend\tests -q
```

Build the frontend:

```powershell
cd frontend
npm install
npm run build
```

These commands describe how to validate a checkout; they do not imply that the current test suite or build has passed. Before release, add client-level tests for login success and failure, cookie handling, redirects, retry failure, timeouts, and logout. Also compare the committed `openapi.json` with the current schema at `/openapi.json` after changing endpoint signatures or response contracts.

## Docker development setup

Docker Compose runs the backend and **Vite development server**. It is intended for local development, not as a production deployment configuration.

```powershell
Copy-Item .env.example .env
# Edit .env and set DEMO_MODE=true for a sample-data run.
docker compose up --build
```

- Frontend: <http://localhost:3000>
- Swagger UI: <http://localhost:8000/docs>

The Compose backend runs inside a container and reads the root `.env` file. Do not expose this setup publicly without adding appropriate access controls and production server configuration.

## Security notes

- Never commit `.env`, portal credentials, cookies, or authorization headers.
- Keep upstream credentials and session cookies on the backend only.
- The application uses one shared, in-memory upstream session per backend process. Do not expose it as an unrestricted public API; add caller authentication and restrict access before public deployment.
- Use HTTPS for deployed services and configure CORS for trusted frontend origins only.
- Keep the upstream adapter read-only unless an explicit, authorized write contract is designed and reviewed.

## Known limitations and next steps

1. **Validate live row extraction end to end.** The portal UI has displayed a populated register, but the count and fields returned by the backend must be checked independently. The UI screenshot's count is dynamic and should not be hard-coded.
2. **Complete field mapping.** The current `Meter` model does not provide dedicated `make`, `phase`, or `DT` fields shown in the browser table.
3. **Add a real consumption integration only after discovery.** Live consumption returns `501` until the upstream endpoint, parameters, units, and timestamps are verified.
4. **Reconstruct hierarchy only from verified relationships.** The current live transformer parser produces a flat list.
5. **Improve frontend pagination.** The current service requests up to 100 meter records per call and does not request subsequent pages.
6. **Complete session UI integration.** The frontend API service currently focuses on data routes; wire session endpoints to the interface if user-facing login/logout controls are required.
7. **Harden deployment.** The global session is not multi-user isolated; add API access control, secret management, monitoring, and production serving before public deployment.
8. **Keep docs and tests in sync.** Regenerate the OpenAPI snapshot and test the HTTPX client behavior whenever route or authentication logic changes.

## Related documentation

- [`PROTOCOL.md`](PROTOCOL.md) — portal reconnaissance, discovered pages, session behavior, and parser assumptions. Re-check it when the upstream portal changes.
- [`REFLECTION.md`](REFLECTION.md) — design decisions, trade-offs, and follow-up work.
- [`openapi.json`](openapi.json) — committed OpenAPI snapshot; compare it with the live schema at `/openapi.json`.


