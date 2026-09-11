const base = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";
async function request(path, options = {}) {
  const response = await fetch(`${base}${path}`, options);
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.error?.message ?? body.detail?.message ?? "Unable to reach the operations API."); }
  return response.json();
}
export const api = {
  meters: (search = "") => request(`/meters?page_size=100${search ? `&search=${encodeURIComponent(search)}` : ""}`),
  meter: (id) => request(`/meters/${encodeURIComponent(id)}`),
  consumption: (id) => request(`/meters/${encodeURIComponent(id)}/consumption`),
  hierarchy: () => request("/hierarchy"),
  health: () => request("/health"),
  session: () => request("/session"),
  login: (credentials) => request("/session/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(credentials) }),
  logout: () => request("/session/logout", { method: "POST" }),
  register: (credentials) => request("/session/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(credentials) }),
};
