import { useState } from "react";
import {
  Link,
  NavLink,
  Route,
  Routes,
  useParams,
} from "react-router-dom";
import {
  Activity,
  ArrowLeft,
  ChevronRight,
  CircleAlert,
  Gauge,
  LayoutDashboard,
  Menu,
  Network,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "./services/api";

function Shell({ children }) {
  const [open, setOpen] = useState(false);

  const links = [
    ["/", "Overview", LayoutDashboard],
    ["/meters", "Meters", Gauge],
    ["/meters/MTR-101/consumption", "Consumption", Activity],
    ["/hierarchy", "Hierarchy", Network],
  ];

  return (
    <div className="app-shell">
      <aside className={open ? "sidebar open" : "sidebar"}>
        <div className="brand">
          <span className="brand-mark">
            <Activity size={18} />
          </span>

          <span>URJA / OPS</span>

          <button
            className="icon-button mobile-only"
            onClick={() => setOpen(false)}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>

        <div className="workspace-label">
          FLOCK ENERGY <span>READ ONLY</span>
        </div>

        <nav>
          {links.map(([to, label, Icon]) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

      </aside>

      <main className="main">
        <header className="topbar">
          <button
            className="icon-button mobile-only"
            onClick={() => setOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={20} />
          </button>

          <div className="crumb">
            METER OPERATIONS <span>/</span> LIVE VIEW
          </div>

          <div className="top-status">
            <i /> READ ONLY
          </div>
        </header>

        <div className="content">{children}</div>
      </main>
    </div>
  );
}

function Notice({ message, retry }) {
  return (
    <div className="notice">
      <CircleAlert size={19} />

      <div>
        <strong>Could not load this view</strong>
        <p>{message}</p>

        {retry && (
          <button className="button secondary" onClick={retry}>
            <RefreshCw size={15} />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

function Loading() {
  return (
    <div className="loading-grid">
      <div className="skeleton wide" />
      <div className="skeleton" />
      <div className="skeleton" />
      <div className="skeleton large" />
    </div>
  );
}

function Status({ value }) {
  return (
    <span className={`status ${(value ?? "unknown").toLowerCase()}`}>
      <i />
      {value ?? "Unknown"}
    </span>
  );
}

function Overview() {
  const meters = useQuery({
    queryKey: ["meters"],
    queryFn: () => api.meters(),
  });

  const health = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
  });

  const items = meters.data?.items ?? [];

  const active = items.filter(
    (meter) => (meter.status ?? "").toLowerCase() === "active"
  ).length;

  const upstreamOnline =
    health.data?.upstream === "reachable" ||
    health.data?.upstream === "demo";

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">OPERATIONS / OVERVIEW</p>
          <h1>Meter command center</h1>
          <p className="lede">
            A clear view of the connected Urja estate and its current portal
            state.
          </p>
        </div>

        <Link className="button primary" to="/meters">
          <Search size={16} />
          Browse meters
        </Link>
      </div>

      {meters.isLoading ? (
        <Loading />
      ) : meters.isError ? (
        <Notice
          message={meters.error.message}
          retry={() => void meters.refetch()}
        />
      ) : (
        <>
          <div className="kpi-grid">
            <Kpi
              label="Discovered meters"
              value={String(meters.data?.total ?? 0)}
              detail={
                health.data?.upstream === "demo"
                  ? "Local demo dataset"
                  : "From the live portal page"
              }
              accent="teal"
            />

            <Kpi
              label="Active status"
              value={String(active)}
              detail="Where a status is exposed"
              accent="lime"
            />

            <Kpi
              label="Portal session"
              value={upstreamOnline ? "Online" : "Unknown"}
              detail={
                health.data?.upstream === "demo"
                  ? "Demo mode"
                  : "Upstream probe"
              }
              accent="amber"
            />
          </div>

          <section className="section-grid">
            <div className="panel feature-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">NEXT ACTION</p>
                  <h2>Review the meter register</h2>
                </div>

                <Gauge size={22} />
              </div>

              <p>
                Search and inspect the normalized records returned from the
                authenticated portal adapter.
              </p>

              <Link className="text-link" to="/meters">
                Open meter register
                <ChevronRight size={15} />
              </Link>
            </div>

            <div className="panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">INTEGRATION STATUS</p>
                  <h2>Adapter boundary</h2>
                </div>

                <span className="status active">
                  <i />
                  Stable
                </span>
              </div>

              <dl className="mini-list">
                <div>
                  <dt>Session</dt>
                  <dd>HttpOnly cookie</dd>
                </div>

                <div>
                  <dt>Verified routes</dt>
                  <dd>/login · /meters · /transformers</dd>
                </div>

                <div>
                  <dt>Consumption</dt>
                  <dd
                    className={
                      health.data?.upstream === "demo" ? "" : "muted"
                    }
                  >
                    {health.data?.upstream === "demo"
                      ? "Demo records available"
                      : "Endpoint pending discovery"}
                  </dd>
                </div>
              </dl>
            </div>
          </section>
        </>
      )}
    </>
  );
}

function Kpi({ label, value, detail, accent }) {
  return (
    <div className={`kpi ${accent}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-detail">{detail}</div>
    </div>
  );
}

function Meters() {
  const [search, setSearch] = useState("");

  const query = useQuery({
    queryKey: ["meters", search],
    queryFn: () => api.meters(search),
  });

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">REGISTRY / METERS</p>
          <h1>Meter register</h1>
          <p className="lede">
            Search the portal’s normalized meter records.
          </p>
        </div>

        <div className="count-badge">
          {query.data?.total ?? "--"} records
        </div>
      </div>

      <div className="toolbar">
        <div className="search-field">
          <Search size={17} />

          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search ID, serial, status or location"
            aria-label="Search meters"
          />
        </div>

        <button
          className="button secondary"
          onClick={() => void query.refetch()}
          disabled={query.isFetching}
        >
          <RefreshCw size={15} />
          Refresh
        </button>
      </div>

      {query.isLoading ? (
        <Loading />
      ) : query.isError ? (
        <Notice
          message={query.error.message}
          retry={() => void query.refetch()}
        />
      ) : (
        <div className="panel table-panel">
          {query.data?.items.length ? (
            <table>
              <thead>
                <tr>
                  <th>Meter</th>
                  <th>Serial number</th>
                  <th>Status</th>
                  <th>Location</th>
                  <th>Network</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {query.data.items.map((meter) => (
                  <tr key={meter.id}>
                    <td>
                      <Link
                        className="meter-link"
                        to={`/meters/${encodeURIComponent(meter.id)}`}
                      >
                        {meter.id}
                        <small>Open record</small>
                      </Link>
                    </td>

                    <td>
                      {meter.serial_number ?? (
                        <span className="muted">Not exposed</span>
                      )}
                    </td>

                    <td>
                      <Status value={meter.status} />
                    </td>

                    <td>
                      {meter.location ?? (
                        <span className="muted">Not exposed</span>
                      )}
                    </td>

                    <td>
                      {Object.values(meter.network).filter(Boolean).join(" · ") || (
                        <span className="muted">Not exposed</span>
                      )}
                    </td>

                    <td>
                      <Link
                        className="icon-link"
                        to={`/meters/${encodeURIComponent(meter.id)}`}
                        aria-label={`Open ${meter.id}`}
                      >
                        <ChevronRight size={18} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty">
              <Gauge size={28} />

              <h3>No meters registered in Urja</h3>

              <p>
                The authenticated portal currently reports zero meters. This
                adapter is read-only, so registration must be completed by an
                authorized operator in Urja or its upstream source.
              </p>
            </div>
          )}
        </div>
      )}
    </>
  );
}

function MeterDetail() {
  const { meterId = "" } = useParams();

  const query = useQuery({
    queryKey: ["meter", meterId],
    queryFn: () => api.meter(meterId),
  });

  return (
    <>
      {query.isLoading ? (
        <Loading />
      ) : query.isError ? (
        <Notice
          message={query.error.message}
          retry={() => void query.refetch()}
        />
      ) : (
        query.data && (
          <>
            <Link className="back-link" to="/meters">
              <ArrowLeft size={16} />
              Back to meter register
            </Link>

            <div className="detail-heading">
              <div>
                <p className="eyebrow">METER RECORD</p>
                <h1>{query.data.id}</h1>
                <p className="lede">
                  Normalized record from the meter register.
                </p>
              </div>

              <Status value={query.data.status} />
            </div>

            <div className="detail-grid">
              <Info
                title="Identity"
                rows={[
                  ["Meter ID", query.data.id],
                  ["Serial number", query.data.serial_number],
                  ["Status", query.data.status],
                ]}
              />

              <Info
                title="Location"
                rows={[["Location", query.data.location]]}
              />

              <Info
                title="Network"
                rows={Object.entries(query.data.network).map(
                  ([key, value]) => [key, value]
                )}
              />
            </div>

            <div className="panel unavailable">
              <div className="unavailable-icon">
                <Activity size={20} />
              </div>

              <div>
                <p className="eyebrow">CONSUMPTION</p>
                <h2>Readings are not yet connected</h2>

                <p>
                  The portal reconnaissance verified the meter register, but
                  did not verify a consumption endpoint or timestamp contract.
                  No readings are fabricated here.
                </p>
              </div>
            </div>
          </>
        )
      )}
    </>
  );
}

function Info({ title, rows }) {
  return (
    <div className="panel info-panel">
      <p className="eyebrow">{title}</p>

      {rows.length ? (
        <dl>
          {rows.map(([key, value]) => (
            <div key={key}>
              <dt>{key.split("_").join(" ")}</dt>
              <dd>
                {value || <span className="muted">Not exposed</span>}
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="muted">No network fields were exposed.</p>
      )}
    </div>
  );
}

function Tree({ node }) {
  return (
    <div className="tree-node">
      <div className="tree-label">
        <span className="tree-dot" />
        {node.label}
        <span className="kind">{node.kind}</span>
      </div>

      {node.children.map((child) => (
        <div className="tree-children" key={child.id}>
          <Tree node={child} />
        </div>
      ))}
    </div>
  );
}

function Hierarchy() {
  const query = useQuery({
    queryKey: ["hierarchy"],
    queryFn: api.hierarchy,
  });

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">NETWORK / TOPOLOGY</p>
          <h1>Hierarchy explorer</h1>
          <p className="lede">
            Explore only relationships the upstream portal exposes reliably.
          </p>
        </div>
      </div>

      {query.isLoading ? (
        <Loading />
      ) : query.isError ? (
        <Notice
          message={query.error.message}
          retry={() => void query.refetch()}
        />
      ) : query.data?.available ? (
        <div className="panel tree-panel">
          {query.data.nodes.map((node) => (
            <Tree key={node.id} node={node} />
          ))}
        </div>
      ) : (
        <div className="panel empty">
          <Network size={30} />

          <h3>Hierarchy not available</h3>

          <p>
            {query.data?.message ??
              "No reliable hierarchy structure was discovered."}
          </p>

          <Link className="button secondary" to="/meters">
            Inspect meters
          </Link>
        </div>
      )}
    </>
  );
}

function Consumption() {
  const { meterId = "MTR-101" } = useParams();

  const query = useQuery({
    queryKey: ["consumption", meterId],
    queryFn: () => api.consumption(meterId),
  });

  return (
    <>
      {query.isLoading ? (
        <Loading />
      ) : query.isError ? (
        <Notice
          message={query.error.message}
          retry={() => void query.refetch()}
        />
      ) : (
        <>
          <Link
            className="back-link"
            to={`/meters/${encodeURIComponent(meterId)}`}
          >
            <ArrowLeft size={16} />
            Back to meter record
          </Link>

          <div className="page-heading">
            <div>
              <p className="eyebrow">METER / CONSUMPTION</p>
              <h1>Consumption records</h1>
              <p className="lede">
                {meterId} · {query.data.unit ?? "Unit not exposed"}
              </p>
            </div>

            <span className="count-badge">
              {query.data.readings.length} readings
            </span>
          </div>

          <div className="panel table-panel">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Meter</th>
                  <th>Unit</th>
                  <th>Value</th>
                </tr>
              </thead>

              <tbody>
                {query.data.readings.map((reading) => (
                  <tr key={reading.timestamp}>
                    <td>
                      {new Date(reading.timestamp)
                        .toISOString()
                        .slice(0, 10)}
                    </td>

                    <td>{meterId}</td>
                    <td>{query.data.unit ?? "-"}</td>
                    <td>{reading.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}

function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/meters" element={<Meters />} />
        <Route path="/meters/:meterId" element={<MeterDetail />} />
        <Route
          path="/meters/:meterId/consumption"
          element={<Consumption />}
        />
        <Route path="/hierarchy" element={<Hierarchy />} />
        <Route path="*" element={<Overview />} />
      </Routes>
    </Shell>
  );
}

export default App;