// Talks to the real API in src/well_risk/api.py (docs/api_spec.md is its
// spec). Defaults to same-origin ("") since in production this frontend is
// served by that same FastAPI process (see Dockerfile) - set
// VITE_API_BASE_URL only for local dev, where the Vite dev server and
// uvicorn run on different ports.
//
// Failures throw. This used to fall back to hardcoded mock data so the UI
// rendered without a backend, but on a public site that meant a down or
// mid-deploy API silently showed made-up numbers as if they were real.

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function getJson(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${path} returned ${res.status}`);
  return res.json();
}

export const fetchSummary = (parish) =>
  getJson(`/api/stats/summary${parish ? `?parish=${encodeURIComponent(parish)}` : ""}`);

export const fetchParishes = () => getJson("/api/parishes");

export const fetchWells = ({ parish, riskTier } = {}) => {
  const params = new URLSearchParams();
  if (parish) params.set("parish", parish);
  if (riskTier) params.set("risk_tier", riskTier);
  const qs = params.toString();
  return getJson(`/api/wells${qs ? `?${qs}` : ""}`);
};
