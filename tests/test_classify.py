from dataclasses import replace

from well_risk.classify import classify_well
from well_risk.models import RiskTier, WellRecord

BASE = WellRecord(
    well_serial_num=1,
    api_num=None,
    well_name=None,
    organization_id=None,
    org_operator_name=None,
    field_id=None,
    field_name=None,
    parish_code=None,
    parish_name=None,
    surface_lat_dec_deg=None,
    surface_long_dec_deg=None,
    legend=None,
    legend_desc=None,
    orphaned_flag=None,
    orphan_status_code=None,
    well_status_code=None,
    well_status_date=None,
    spud_date=None,
    permit_date=None,
    measured_depth=None,
    product_type_code=None,
    well_class_type_code=None,
    hyperlink=None,
)


def test_orphaned_flag_wins_regardless_of_legend():
    well = replace(BASE, orphaned_flag="Y", legend_desc="ACTIVE - PRODUCING OIL")
    result = classify_well(well)
    assert result.risk_tier == RiskTier.CRITICAL
    assert "ORPHANED_FLAG=Y" in result.risk_reason


def test_unable_to_locate_is_critical():
    well = replace(BASE, legend_desc="UNABLE TO LOCATE WELL-NO PLUG/ABND REP OIL")
    assert classify_well(well).risk_tier == RiskTier.CRITICAL


def test_temporarily_abandoned_is_high():
    well = replace(BASE, legend_desc="TEMPORARILY ABANDONED WELL OIL")
    assert classify_well(well).risk_tier == RiskTier.HIGH


def test_shut_in_no_future_utility_is_high_not_medium():
    well = replace(BASE, legend_desc="SHUT-IN DRY HOLE - NO FUTURE UTILITY GAS")
    assert classify_well(well).risk_tier == RiskTier.HIGH


def test_shut_in_waiting_on_market_is_medium():
    well = replace(BASE, legend_desc="SHUT-IN WAITING ON MARKET OIL")
    assert classify_well(well).risk_tier == RiskTier.MEDIUM


def test_plugged_and_abandoned_is_low():
    well = replace(BASE, legend_desc="PLUGGED AND ABANDONED OIL")
    assert classify_well(well).risk_tier == RiskTier.LOW


def test_active_producing_is_active():
    well = replace(BASE, legend_desc="ACTIVE - PRODUCING OIL")
    assert classify_well(well).risk_tier == RiskTier.ACTIVE


def test_unmatched_legend_is_unclassified():
    well = replace(BASE, legend_desc="WATER OIL")
    result = classify_well(well)
    assert result.risk_tier == RiskTier.UNCLASSIFIED
    assert "needs manual review" in result.risk_reason


def test_missing_legend_desc_is_unclassified():
    well = replace(BASE, legend_desc=None)
    assert classify_well(well).risk_tier == RiskTier.UNCLASSIFIED
