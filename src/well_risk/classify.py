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

`LEGEND_DESC` text doesn't perfectly match the renderer's 174-label set -
confirmed 2026-08-04 by pulling all 111 distinct LEGEND_DESC values live and
diffing against the renderer list. E.g. "P&A PER INSPECTION" occurs in real
data where the renderer's legend says "PLUGGED/ABNDED PER INSPECTION" -
DNR's own text has drift between the two. Rules match on live LEGEND_DESC
values, not the renderer list, and are checked periodically against a fresh
dataset-wide pull (see tests/test_classify.py for the confirmed 428-well
UNCLASSIFIED residual as of that pull).

ORPHANED_FLAG is NOT a live-risk signal by itself - confirmed 2026-08-04 by
correlating it against LEGEND_DESC across all 15,861 flagged wells
statewide: 94.6% share ORPHAN_STATUS_CODE='23' (Act 404 Engineering
program), and within that single code, current LEGEND_DESC spans the full
range from unresolved ("ACT 404 ORPHAN WELL-ENG") to already-resolved
("PLUGGED AND ABANDONED", ~6.5k wells) to even "ACTIVE - PRODUCING" (~700
wells). The flag is a permanent "this well passed through the state orphan
program at some point" marker that DNR does not clear once a well is
plugged or returns to production - it is not cleared to "N" after
resolution. Treating orphaned_flag=='Y' as always CRITICAL (the original
version of this function) would misclassify roughly half of flagged wells
as currently critical when SONRIS's own current status field says
otherwise. ORPHAN_STATUS_CODE's remaining values (26=Injection & Mining
program, and the rare 10/19/20/28/29/30/31/32, each under 10 wells
statewide) look like program/division categories rather than a status
progression, but that's inferred from distribution, not a published
domain - still unconfirmed.
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
    (RiskTier.LOW, ("PLUGGED/ABNDED PER INSPECTION", "P&A PER INSPECTION")),
    (RiskTier.LOW, ("PLUGGED BACK",)),
    (RiskTier.ACTIVE, ("ACTIVE",)),
    (RiskTier.ACTIVE, ("PERMITTED",)),
    (RiskTier.ACTIVE, ("APPROVAL TO CONSTRUCT",)),
    (RiskTier.ACTIVE, ("CONVERSION TO OIL",)),
    (RiskTier.ACTIVE, ("MULTIPLE COMPLETED",)),
    (RiskTier.ACTIVE, ("REVERTED",)),
]

# Tiers where the well's *current* status is resolved - the orphan flag is
# history, not an active liability, so it doesn't escalate these.
_RESOLVED_TIERS = {RiskTier.LOW, RiskTier.ACTIVE}


def _legend_tier(legend_desc: str | None) -> tuple[RiskTier, str, str]:
    upper = (legend_desc or "").upper()
    for tier, keywords in _RISK_RULES:
        for kw in keywords:
            if kw in upper:
                return tier, kw, f"LEGEND_DESC matched {kw!r} ({legend_desc!r})"
    return (
        RiskTier.UNCLASSIFIED,
        "",
        f"no risk keyword matched LEGEND_DESC={legend_desc!r} - needs manual review",
    )


def classify_well(well: WellRecord) -> ClassifiedWell:
    legend_tier, _matched_kw, legend_reason = _legend_tier(well.legend_desc)

    if well.orphaned_flag != "Y":
        return ClassifiedWell(well=well, risk_tier=legend_tier, risk_reason=legend_reason)

    orphan_note = "ORPHANED_FLAG=Y"
    if well.orphan_status_code:
        orphan_note += f" (ORPHAN_STATUS_CODE={well.orphan_status_code}, program/category unconfirmed)"

    if legend_tier in _RESOLVED_TIERS:
        # Went through the orphan program at some point, but current status
        # is already resolved (plugged) or the well is back in active use -
        # DNR doesn't clear the flag after resolution, so don't let it
        # override a status that's no longer a live risk.
        reason = f"{legend_reason}; {orphan_note} historically, but current status is resolved"
        return ClassifiedWell(well=well, risk_tier=legend_tier, risk_reason=reason)

    reason = f"{orphan_note}; current status still unresolved ({well.legend_desc!r})"
    return ClassifiedWell(well=well, risk_tier=RiskTier.CRITICAL, risk_reason=reason)
