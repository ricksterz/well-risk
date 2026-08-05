from dataclasses import replace

from well_risk.classify import classify_well
from well_risk.grid_join import (
    FULL_SERVICE_BOUNDS,
    WELL_RISK_STUDY_BOUNDS,
    join_well_to_grid,
    snap_to_grid,
)
from well_risk.models import WellRecord

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
    legend_desc="ACTIVE - PRODUCING OIL",
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


def test_snap_to_grid_lands_on_a_multiple_of_resolution():
    result = snap_to_grid(29.9199, -90.35, resolution=0.002, bounds=FULL_SERVICE_BOUNDS)
    assert result is not None
    grid_lat, grid_lng = result
    steps = round((grid_lat - FULL_SERVICE_BOUNDS["lat_min"]) / 0.002)
    assert abs(FULL_SERVICE_BOUNDS["lat_min"] + steps * 0.002 - grid_lat) < 1e-9


def test_snap_to_grid_out_of_bounds_returns_none():
    # Lafourche parish coordinates - south/west of FULL_SERVICE_BOUNDS
    assert snap_to_grid(29.35, -90.4, bounds=FULL_SERVICE_BOUNDS) is None


def test_join_well_to_grid_jefferson_well_is_in_coverage():
    well = replace(BASE, surface_lat_dec_deg=29.95, surface_long_dec_deg=-90.1)
    joined = join_well_to_grid(classify_well(well))
    assert joined.in_floodlens_coverage is True
    assert joined.grid_lat is not None
    assert joined.grid_lng is not None


def test_join_well_to_grid_lafourche_well_gets_study_cell_but_no_floodlens_data():
    # Outside FloodLens's FULL_SERVICE_BOUNDS but inside well-risk's own
    # WELL_RISK_STUDY_BOUNDS - should still get a grid cell for the app's
    # own map, just flagged as not backed by real FloodLens subsidence data.
    well = replace(BASE, surface_lat_dec_deg=29.35, surface_long_dec_deg=-90.4)
    joined = join_well_to_grid(classify_well(well))
    assert joined.in_floodlens_coverage is False
    assert joined.grid_lat is not None
    assert joined.grid_lng is not None


def test_join_well_to_grid_outside_study_area_entirely_is_none():
    # Nowhere near any of the three target parishes.
    well = replace(BASE, surface_lat_dec_deg=32.5, surface_long_dec_deg=-92.1)
    joined = join_well_to_grid(classify_well(well))
    assert joined.in_floodlens_coverage is False
    assert joined.grid_lat is None
    assert joined.grid_lng is None


def test_join_well_to_grid_missing_coords_is_out_of_coverage():
    well = replace(BASE, surface_lat_dec_deg=None, surface_long_dec_deg=None)
    joined = join_well_to_grid(classify_well(well))
    assert joined.in_floodlens_coverage is False


def test_well_risk_study_bounds_cover_known_plaquemines_and_lafourche_points():
    # Venice, LA (southern Plaquemines) and Port Fourchon (southern
    # Lafourche) - both must fall inside the study bounds for the gap-fix
    # above to actually help the two parishes it's meant for.
    venice = (29.28, -89.36)
    port_fourchon = (29.11, -90.20)
    for lat, lng in (venice, port_fourchon):
        assert WELL_RISK_STUDY_BOUNDS["lat_min"] <= lat <= WELL_RISK_STUDY_BOUNDS["lat_max"]
        assert WELL_RISK_STUDY_BOUNDS["lng_min"] <= lng <= WELL_RISK_STUDY_BOUNDS["lng_max"]
