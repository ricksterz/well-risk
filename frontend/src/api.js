// Talks to the real API in src/well_risk/api.py (docs/api_spec.md is its
// spec). Defaults to same-origin ("") since in production this frontend is
// served by that same FastAPI process (see Dockerfile) - set
// VITE_API_BASE_URL only for local dev, where the Vite dev server and
// uvicorn run on different ports. Falls back to MOCK data on fetch failure
// so the UI still renders if the backend is down or mid-deploy.

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

const MOCK_SUMMARY = {
  wells_in_scope: 8400,
  by_risk_tier: { critical: 88, high: 524, medium: 1310, low: 4200, active: 2100, unclassified: 178 },
  high_risk_in_floodlens_coverage: 94,
  parishes_covered: 3,
};

const MOCK_PARISHES = {
  parishes: [
    { parish_name: "JEFFERSON", well_count: 3100 },
    { parish_name: "PLAQUEMINES", well_count: 2900 },
    { parish_name: "LAFOURCHE", well_count: 2400 },
  ],
};

const MOCK_WELLS = {
  total: 4,
  limit: 50,
  offset: 0,
  wells: [
    {
      well_serial_num: 246837,
      well_name: "SL 21089",
      parish_name: "LAFOURCHE",
      org_operator_name: "HILCORP ENERGY COMPANY",
      risk_tier: "high",
      risk_reason: "LEGEND_DESC matched 'TEMPORARILY ABANDONED'",
      surface_lat_dec_deg: 29.199626,
      surface_long_dec_deg: -90.358839,
      in_floodlens_coverage: false,
    },
    {
      well_serial_num: 190874,
      well_name: "SL 19087",
      parish_name: "PLAQUEMINES",
      org_operator_name: "EXAMPLE OPERATOR LLC",
      risk_tier: "critical",
      risk_reason: "ORPHANED_FLAG=Y",
      surface_lat_dec_deg: 29.42,
      surface_long_dec_deg: -89.72,
      in_floodlens_coverage: false,
    },
    {
      well_serial_num: 221563,
      well_name: "SL 22156",
      parish_name: "JEFFERSON",
      org_operator_name: "EXAMPLE OPERATOR LLC",
      risk_tier: "medium",
      risk_reason: "LEGEND_DESC matched 'SHUT-IN'",
      surface_lat_dec_deg: 29.96,
      surface_long_dec_deg: -90.12,
      in_floodlens_coverage: true,
    },
    {
      well_serial_num: 208741,
      well_name: "SL 20874",
      parish_name: "LAFOURCHE",
      org_operator_name: "HILCORP ENERGY COMPANY",
      risk_tier: "medium",
      risk_reason: "LEGEND_DESC matched 'INACTIVE'",
      surface_lat_dec_deg: 29.55,
      surface_long_dec_deg: -90.3,
      in_floodlens_coverage: false,
    },
  ],
};

async function getJson(path, fallback) {
  try {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`${res.status}`);
    return await res.json();
  } catch {
    return fallback;
  }
}

export const fetchSummary = (parish) =>
  getJson(`/api/stats/summary${parish ? `?parish=${encodeURIComponent(parish)}` : ""}`, MOCK_SUMMARY);

export const fetchParishes = () => getJson("/api/parishes", MOCK_PARISHES);

export const fetchWells = ({ parish, riskTier } = {}) => {
  const params = new URLSearchParams();
  if (parish) params.set("parish", parish);
  if (riskTier) params.set("risk_tier", riskTier);
  const qs = params.toString();
  return getJson(`/api/wells${qs ? `?${qs}` : ""}`, MOCK_WELLS);
};
