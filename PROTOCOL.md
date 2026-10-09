# Urja Portal Protocol

## Verified reconnaissance

The portal is a SvelteKit application titled **Urja Meter Ops**. A GET to the base URL redirects to `/login`. The login page renders a plain HTML form with `method="POST"`, fields named `email` and `password`, and no rendered CSRF field.

The supplied credentials were used only during local reconnaissance. The successful login response was JSON and set an HttpOnly, Secure, SameSite=Lax cookie named `__Secure-better-auth.session_token` with a one-hour lifetime. The base route redirects an authenticated session to `/meters`.

## Discovered endpoints

| Purpose | Method | Path | Parameters | Verified response |
| --- | --- | --- | --- | --- |
| Login | POST | `/login` | Form fields `email`, `password` | JSON success response and session cookie |
| Portal entry | GET | `/` | Session cookie | 302 to `/meters` after authentication |
| Meter page | GET | `/meters` | Session cookie | HTML page |
| Transformer page | GET | `/transformers` | Session cookie | HTML page; relationship shape still requires inspection |

No consumption endpoint was verified. The adapter therefore does not invent one and returns `501 UPSTREAM_ENDPOINT_UNKNOWN` for the modern consumption route.

The authenticated `/meters` page currently renders `0 total` and `No meters found.` There is no registration form or verified write endpoint. Meter registration is outside this read-only adapter and must be performed by an authorized operator in the portal or upstream system.

The API does not currently have a separately verified meter-detail HTML page. `GET /api/v1/meters/{meter_id}` resolves by reading the normalized meter list and matching the requested identifier; this is a read through the discovered register, not a claim that a dedicated upstream detail endpoint exists.

## Data mapping

The parser maps table headers semantically when they are exposed by the HTML:

| Legacy concept | API field |
| --- | --- |
| `ID`, `Meter ID`, or `Meter` | `id` |
| `Serial Number`, `Serial`, or `Meter Serial Number` | `serial_number` |
| `Status` or `State` | `status` |
| `Location` or `Address` | `location` |
| `Feeder`, `Transformer`, `Substation`, `Network` | `network` object |

Whitespace is collapsed and empty values become `null`. Unknown fields are not fabricated.

## Session management

`UrjaPortalClient` uses one long-lived `httpx.AsyncClient`, which preserves cookies in memory. Authentication is guarded by an asyncio lock. A redirect to `/login`, 401, or 403 invalidates the session and triggers one reauthentication attempt. Credentials, cookies, authorization headers, and upstream HTML are not logged.

The API exposes `GET /api/v1/session`, `POST /api/v1/session/login`, and `POST /api/v1/session/logout` for the UI's session toggle. Logout clears the adapter's in-memory cookie; the next data request can authenticate again because the adapter owns the portal session.

## Known limitations

- The rendered `/meters` and `/transformers` documents were identified, but the final table/detail payloads and any internal fetch calls need a browser network trace for complete field coverage.
- No separate meter-detail page or live consumption endpoint has been verified; both remain best-effort adapters over the list view and demo fixtures.
- Consumption, date filters, timestamp granularity, and hierarchy nesting remain `UNKNOWN — REQUIRES INVESTIGATION`.
- The application is read-only and never submits portal mutation requests.
- Demo consumption data is synthetic and must be labeled as such; it is not presented as real utility telemetry.
