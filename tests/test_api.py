import json

import pytest
from fastapi.testclient import TestClient

FIXTURE_WELLS = [
    {
        "well_serial_num": 1,
        "api_num": None,
        "well_name": "SL 1",
        "organization_id": None,
        "org_operator_name": "ACME OIL",
        "field_id": None,
        "field_name": None,
        "parish_code": None,
        "parish_name": "JEFFERSON",
        "surface_lat_dec_deg": 29.95,
        "surface_long_dec_deg": -90.1,
        "legend": None,
        "legend_desc": "ACT 404 ORPHAN WELL-ENG OIL",
        "orphaned_flag": "Y",
        "orphan_status_code": "23",
        "well_status_code": None,
        "well_status_date": None,
        "spud_date": None,
        "permit_date": None,
        "measured_depth": None,
        "product_type_code": None,
        "well_class_type_code": None,
        "hyperlink": None,
        "risk_tier": "critical",
        "risk_reason": "ORPHANED_FLAG=Y; current status still unresolved",
        "grid_lat": 29.95,
        "grid_lng": -90.1,
        "in_floodlens_coverage": True,
    },
    {
        "well_serial_num": 2,
        "api_num": None,
        "well_name": "SL 2",
        "organization_id": None,
        "org_operator_name": "ACME OIL",
        "field_id": None,
        "field_name": None,
        "parish_code": None,
        "parish_name": "LAFOURCHE",
        "surface_lat_dec_deg": 29.35,
        "surface_long_dec_deg": -90.4,
        "legend": None,
        "legend_desc": "PLUGGED AND ABANDONED OIL",
        "orphaned_flag": None,
        "orphan_status_code": None,
        "well_status_code": None,
        "well_status_date": "2020-01-01",
        "spud_date": None,
        "permit_date": None,
        "measured_depth": None,
        "product_type_code": None,
        "well_class_type_code": None,
        "hyperlink": None,
        "risk_tier": "low",
        "risk_reason": "LEGEND_DESC matched 'PLUGGED AND ABANDONED'",
        "grid_lat": 29.35,
        "grid_lng": -90.4,
        "in_floodlens_coverage": False,
    },
]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    dataset_path = tmp_path / "wells.json"
    dataset_path.write_text(json.dumps(FIXTURE_WELLS))
    monkeypatch.setenv("WELL_RISK_DATASET_PATH", str(dataset_path))

    # Reimport fresh so DATASET_PATH picks up the env var set above.
    import importlib

    import well_risk.api as api_module

    importlib.reload(api_module)
    with TestClient(api_module.app) as test_client:
        yield test_client


def test_parishes_lists_both_fixture_parishes(client):
    resp = client.get("/api/parishes")
    assert resp.status_code == 200
    names = {p["parish_name"] for p in resp.json()["parishes"]}
    assert names == {"JEFFERSON", "LAFOURCHE"}


def test_stats_summary_counts_by_tier(client):
    resp = client.get("/api/stats/summary")
    body = resp.json()
    assert body["wells_in_scope"] == 2
    assert body["by_risk_tier"]["critical"] == 1
    assert body["by_risk_tier"]["low"] == 1
    assert body["high_risk_in_floodlens_coverage"] == 1  # well 1: critical + in coverage


def test_stats_summary_filters_by_parish(client):
    resp = client.get("/api/stats/summary?parish=jefferson")
    assert resp.json()["wells_in_scope"] == 1


def test_list_wells_filters_by_risk_tier(client):
    resp = client.get("/api/wells?risk_tier=low")
    body = resp.json()
    assert body["total"] == 1
    assert body["wells"][0]["well_serial_num"] == 2


def test_get_well_by_id(client):
    resp = client.get("/api/wells/1")
    assert resp.status_code == 200
    assert resp.json()["risk_tier"] == "critical"


def test_get_well_404(client):
    resp = client.get("/api/wells/999")
    assert resp.status_code == 404


def test_wells_map_returns_points(client):
    resp = client.get("/api/wells/map")
    body = resp.json()
    assert body["truncated"] is False
    assert len(body["points"]) == 2
    assert {"well_serial_num", "lat", "lng", "risk_tier"} <= body["points"][0].keys()
