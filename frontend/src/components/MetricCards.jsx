export default function MetricCards({ summary }) {
  if (!summary) return null;
  const cards = [
    { label: "Wells in scope", value: summary.wells_in_scope.toLocaleString() },
    { label: "Orphaned / abandoned", value: (summary.by_risk_tier.critical + summary.by_risk_tier.high).toLocaleString() },
    { label: "High risk in FloodLens coverage", value: summary.high_risk_in_floodlens_coverage.toLocaleString(), danger: true },
    { label: "Parishes covered", value: summary.parishes_covered },
  ];

  return (
    <div className="metric-grid">
      {cards.map((c) => (
        <div className="metric-card" key={c.label}>
          <p className="metric-label">{c.label}</p>
          <p className={`metric-value${c.danger ? " metric-danger" : ""}`}>{c.value}</p>
        </div>
      ))}
    </div>
  );
}
