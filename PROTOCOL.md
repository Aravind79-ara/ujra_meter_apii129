# Urja Portal Protocol

## Verified reconnaissance

The portal is a SvelteKit application titled **Urja Meter Ops**. A GET to the base URL redirects to `/login`. The login page renders a plain HTML form with `method="POST"`, fields named `email` and `password`, and no rendered CSRF field.

The supplied credentials were used only during local reconnaissance. The successful login response was JSON and set an HttpOnly, Secure, SameSite=Lax cookie named `__Secure-better-auth.session_token` with a one-hour lifetime. The exact JSON fields were not recorded; the adapter therefore verifies an HTTP 200 JSON object and the observed session cookie without inventing a response field. The base route redirects an authenticated session to `/meters`.

## Discovered endpoints

| Purpose | Method | Path | Parameters | Verified response |
| --- | --- | --- | --- | --- |
| Login | POST | `/login` | Form fields `email`, `password` | JSON success response and session cookie |
| Portal entry | GET | `/` | Session cookie | 302 to `/meters` after authentication |
| Meter register data | GET | `/portal/meters/search` | Session cookie; `q`, `page` | JSON `{ data, total, page, pageSize }`; verified with 403 total records |
| Transformer data | GET | `/portal/dts` | Session cookie; `page` | JSON `{ data, total, page, pageSize }`; verified with 40 total records |
| Meter page | GET | `/meters` | Session cookie | HTML shell; rows are loaded from `/portal/meters/search` in the browser |
| Transformer page | GET | `/transformers` | Session cookie | HTML shell; rows are loaded from `/portal/dts` in the browser |

The HTML page is not the data source: its server-rendered table is only a loading/empty placeholder. The authenticated browser fetches meter and transformer rows from the JSON endpoints above. The adapter now calls those endpoints directly and follows their 20-record pagination.

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

The JSON meter endpoint provides `meterId`, `serialNo`, `make`, `phaseType`, `installStatus`, and `dtCode`; these map to the API meter ID, serial number, make, phase, status, and distribution-transformer code. Transformer records provide `code`, `name`, `feederCode`, and `capacityKva`.

Whitespace is collapsed and empty values become `null`. Unknown fields are not fabricated.

## Session management

`UrjaPortalClient` uses one long-lived `httpx.AsyncClient`, which preserves cookies in memory. Authentication is guarded by an asyncio lock. A redirect to `/login`, 401, or 403 invalidates the session and triggers one reauthentication attempt. Credentials, cookies, authorization headers, and upstream HTML are not logged.

The API exposes `GET /api/v1/session`, bodyless `POST /api/v1/session/login`, and `POST /api/v1/session/logout` for session control. Live login uses only backend-configured credentials; request-supplied credentials are not accepted. Logout clears the adapter's in-memory cookie; the next data request can authenticate again because the adapter owns the portal session. In demo mode, the session state is a local simulation and does not represent authentication with the Urja portal.

## Known limitations

- The meter and transformer list endpoints and their current fields are verified. The hierarchy relationships and any additional portal fields remain unverified.
- No separate meter-detail page has been verified; meter detail lookups remain search-based.
- Date filters and hierarchy nesting remain `UNKNOWN — REQUIRES INVESTIGATION`.
- The application is read-only and never submits portal mutation requests.
