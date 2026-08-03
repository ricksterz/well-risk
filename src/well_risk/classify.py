"""
Orphan/abandonment risk classification for SONRIS oil & gas wells.

Every well record returned by the ArcGIS query carries a `LEGEND_DESC` field
- live plain-English text pulled straight from the DNRSvc/OC map service's
own legend (174 codes, confirmed 2026-08-02 via the service's `drawingInfo`
renderer, keyed on the `LEGEND` field). That vocabulary is authoritative:
it is literally what DNR calls each status on its own map. The RISK_RULES
below are NOT an official DNR risk scheme - DNR does not publish one beyond
the raw `ORPHANED_FLAG` - they are this project's judgment call, grouping
DNR's own status language into risk tiers. Treat tier assignments as a
starting point to validate against domain knowledge, not ground truth.

`ORPHAN_STATUS_CODE` (seen values: 10, 19, 20, 23, 26, 28, 29, 30, 31, 32)
has no published domain and is not decoded here - it's carried through in
the risk_reason string when present, for manual follow-up.
"""

from __future__ import annotations

from well_risk.models import ClassifiedWell, RiskTier, WellRecord

# Ordered most-specific/highest-risk first. First matching keyword set wins.
_RISK_RULES: list[tuple[RiskTier, tuple[str, ...]]] = [
    (RiskTier.CRITICAL, ("UNABLE TO LOCATE",)),
    (RiskTier.CRITICAL, ("ORPHAN",)),
    (RiskTier.HIGH, ("TEMPORARILY ABANDONED",)),
    (RiskTier.HIGH, ("NO FUTURE UTILITY",)),
    (RiskTier.MEDIUM, ("SHUT-IN",)),
    (RiskTier.MEDIUM, ("INACTIVE",)),
    (RiskTier.MEDIUM, ("PERMIT EXPIRED",)),
    (RiskTier.LOW, ("PLUGGED AND ABANDONED",)),
    (RiskTier.LOW, ("DRY AND PLUGGED",)),
    (RiskTier.LOW, ("PLUGGED/ABNDED PER INSPECTION",)),
    (RiskTier.LOW, ("PLUGGED BACK",)),
    (RiskTier.ACTIVE, ("ACTIVE",)),
    (RiskTier.ACTIVE, ("PERMITTED",)),
    (RiskTier.ACTIVE, ("APPROVAL TO CONSTRUCT",)),
    (RiskTier.ACTIVE, ("CONVERSION TO OIL",)),
    (RiskTier.ACTIVE, ("MULTIPLE COMPLETED",)),
    (RiskTier.ACTIVE, ("REVERTED",)),
]


def classify_well(well: WellRecord) -> ClassifiedWell:
    if well.orphaned_flag == "Y":
        reason = "ORPHANED_FLAG=Y"
        if well.orphan_status_code:
            reason += f" (ORPHAN_STATUS_CODE={well.orphan_status_code}, meaning unconfirmed)"
        return ClassifiedWell(well=well, risk_tier=RiskTier.CRITICAL, risk_reason=reason)

    legend_desc = (well.legend_desc or "").upper()
    for tier, keywords in _RISK_RULES:
        if any(kw in legend_desc for kw in keywords):
            return ClassifiedWell(
                well=well,
                risk_tier=tier,
                risk_reason=f"LEGEND_DESC matched {keywords[0]!r} ({well.legend_desc!r})",
            )

    return ClassifiedWell(
        well=well,
        risk_tier=RiskTier.UNCLASSIFIED,
        risk_reason=f"no risk keyword matched LEGEND_DESC={well.legend_desc!r} - needs manual review",
    )
