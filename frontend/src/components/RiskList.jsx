const TIER_BADGE_CLASS = {
  critical: "badge-danger",
  high: "badge-danger",
  medium: "badge-warning",
  low: "badge-neutral",
  active: "badge-neutral",
  unclassified: "badge-neutral",
};

export default function RiskList({ wells }) {
  const sorted = [...wells].sort((a, b) => a.risk_tier.localeCompare(b.risk_tier));

  return (
    <div>
      <p className="panel-label">Top risk wells</p>
      <div className="risk-list">
        {sorted.map((w) => (
          <div className="risk-row" key={w.well_serial_num}>
            <div>
              <p className="risk-well-name">{w.well_name || w.well_serial_num}</p>
              <p className="risk-well-parish">{w.parish_name}</p>
            </div>
            <span className={`badge ${TIER_BADGE_CLASS[w.risk_tier] || "badge-neutral"}`}>{w.risk_tier}</span>
          </div>
        ))}
        {sorted.length === 0 && <p className="empty-state">No wells match the current filters.</p>}
      </div>
    </div>
  );
}
