const RISK_TIERS = ["all", "critical", "high", "medium", "low", "active", "unclassified"];

export default function FilterBar({ parishes, parish, onParishChange, riskTier, onRiskTierChange }) {
  return (
    <div className="filter-bar">
      <select value={parish} onChange={(e) => onParishChange(e.target.value)}>
        <option value="">All parishes</option>
        {parishes.map((p) => (
          <option key={p.parish_name} value={p.parish_name}>
            {p.parish_name} ({p.well_count})
          </option>
        ))}
      </select>

      <div className="pill-group">
        {RISK_TIERS.map((tier) => (
          <button
            key={tier}
            className={`pill${(riskTier || "all") === tier ? " pill-active" : ""}`}
            onClick={() => onRiskTierChange(tier === "all" ? "" : tier)}
          >
            {tier[0].toUpperCase() + tier.slice(1)}
          </button>
        ))}
      </div>
    </div>
  );
}
