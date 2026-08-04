const TIER_CLASS = {
  critical: "dot-critical",
  high: "dot-critical",
  medium: "dot-medium",
  low: "dot-low",
  active: "dot-low",
  unclassified: "dot-low",
};

// No map library wired up yet - positions wells by normalizing lat/lng into
// the plotted area's bounding box. Swap for Mapbox/Leaflet once picked;
// FloodLens already uses Mapbox (frontend/index.html), worth matching.
// Until then, corner coordinates + a reference grid + a compass mark give the
// dots an actual frame - plain floating points otherwise read as noise.
export default function MapPlaceholder({ wells }) {
  const located = wells.filter((w) => w.surface_lat_dec_deg != null && w.surface_long_dec_deg != null);
  const lats = located.map((w) => w.surface_lat_dec_deg);
  const lngs = located.map((w) => w.surface_long_dec_deg);
  const latMin = Math.min(...lats, 29);
  const latMax = Math.max(...lats, 30.5);
  const lngMin = Math.min(...lngs, -90.5);
  const lngMax = Math.max(...lngs, -89.4);

  const fmtLat = (v) => `${v.toFixed(2)}°N`;
  const fmtLng = (v) => `${Math.abs(v).toFixed(2)}°W`;

  return (
    <div className="map-panel">
      <p className="panel-label">Well locations</p>
      <div className="map-frame">
        <div className="map-area">
          <div className="map-gridlines" />
          <span className="map-corner map-corner-nw">{fmtLat(latMax)}, {fmtLng(lngMin)}</span>
          <span className="map-corner map-corner-se">{fmtLat(latMin)}, {fmtLng(lngMax)}</span>
          <span className="map-compass" title="North is up">N ↑</span>
          {located.map((w) => (
            <div
              key={w.well_serial_num}
              className={`map-dot ${TIER_CLASS[w.risk_tier] || "dot-low"}`}
              style={{
                left: `${((w.surface_long_dec_deg - lngMin) / (lngMax - lngMin || 1)) * 100}%`,
                top: `${100 - ((w.surface_lat_dec_deg - latMin) / (latMax - latMin || 1)) * 100}%`,
              }}
              title={`${w.well_name || w.well_serial_num} - ${w.risk_tier} - ${w.surface_lat_dec_deg.toFixed(4)}, ${w.surface_long_dec_deg.toFixed(4)}`}
            />
          ))}
        </div>
      </div>
      <div className="map-legend">
        <span><i className="legend-dot dot-critical" />Critical / high</span>
        <span><i className="legend-dot dot-medium" />Medium</span>
        <span><i className="legend-dot dot-low" />Low / active</span>
      </div>
    </div>
  );
}
