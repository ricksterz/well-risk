"""
Batch pipeline: pull every well in the 3 target parishes, classify it,
grid-join it, and write the result to a single JSON file the API reads from.

Runs against the live ArcGIS endpoint per invocation - matches the "run
nightly" model FloodLens's own batch_score.py uses, not a per-request live
query. maxRecordCount on this service is 1000 (confirmed 2026-08-02 via the
layer metadata), so pulling all 3 parishes (30,375 wells as of 2026-08-04)
takes ~31 paginated requests.

Usage: python -m well_risk.pipeline [--output data/processed/wells.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from well_risk.classify import classify_well
from well_risk.grid_join import join_well_to_grid
from well_risk.models import WellRecord
from well_risk.schema_explore import ARCGIS_QUERY_URL

PAGE_SIZE = 1000
DEFAULT_TIMEOUT = 30.0

# Exact match on the CLAUDE.md/README's 3 target parishes. WELL_RISK_STUDY_BOUNDS
# (grid_join.py) is a bbox and pulls in ~17 neighboring parishes as spillover
# (confirmed 2026-08-04: 38,418 wells by bbox vs 30,375 by exact parish name) -
# filtering here on PARISH_NAME is what actually keeps the dataset in scope.
TARGET_PARISHES = ("JEFFERSON", "PLAQUEMINES", "LAFOURCHE")

# ArcGIS field name -> WellRecord field name, for the subset this project uses.
_FIELD_MAP = {
    "WELL_SERIAL_NUM": "well_serial_num",
    "API_NUM": "api_num",
    "WELL_NAME": "well_name",
    "ORGANIZATION_ID": "organization_id",
    "ORG_OPER_NAME": "org_operator_name",
    "FIELD_ID": "field_id",
    "FIELD_NAME": "field_name",
    "PARISH_CODE": "parish_code",
    "PARISH_NAME": "parish_name",
    "SURFACE_LAT_DEC_DEG": "surface_lat_dec_deg",
    "SURFACE_LONG_DEC_DEG": "surface_long_dec_deg",
    "LEGEND": "legend",
    "LEGEND_DESC": "legend_desc",
    "ORPHANED_FLAG": "orphaned_flag",
    "ORPHAN_STATUS_CODE": "orphan_status_code",
    "WELL_STATUS_CODE": "well_status_code",
    "WELL_STATUS_DATE": "well_status_date",
    "SPUD_DATE": "spud_date",
    "PERMIT_DATE": "permit_date",
    "MEASURED_DEPTH": "measured_depth",
    "PRODUCT_TYPE_CODE": "product_type_code",
    "WELL_CLASS_TYPE_CODE": "well_class_type_code",
    "HYPERLINK": "hyperlink",
}
_DATE_FIELDS = {"well_status_date", "spud_date", "permit_date"}


def _epoch_ms_to_date(value: int | None) -> date | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date()


def _attrs_to_well_record(attrs: dict) -> WellRecord:
    kwargs = {}
    for arcgis_name, field_name in _FIELD_MAP.items():
        value = attrs.get(arcgis_name)
        if field_name in _DATE_FIELDS:
            value = _epoch_ms_to_date(value)
        kwargs[field_name] = value
    return WellRecord(**kwargs)


def fetch_all_wells(
    parishes: tuple[str, ...] = TARGET_PARISHES,
    url: str = ARCGIS_QUERY_URL,
    page_size: int = PAGE_SIZE,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[WellRecord]:
    """Paginate every well in `parishes`. Prints progress to stderr - this can take a minute."""
    out_fields = ",".join(_FIELD_MAP)
    parish_list = ",".join(f"'{p}'" for p in parishes)

    wells: list[WellRecord] = []
    offset = 0
    while True:
        params = {
            "where": f"PARISH_NAME IN ({parish_list})",
            "outFields": out_fields,
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": page_size,
            "returnGeometry": "false",
        }
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"ArcGIS endpoint returned an error: {data['error']}")

        features = data.get("features", [])
        wells.extend(_attrs_to_well_record(f["attributes"]) for f in features)
        print(f"  fetched {len(wells)} wells so far (offset={offset})", file=sys.stderr)

        if not data.get("exceededTransferLimit") and len(features) < page_size:
            break
        offset += page_size

    return wells


def build_dataset(parishes: tuple[str, ...] = TARGET_PARISHES) -> list[dict]:
    wells = fetch_all_wells(parishes=parishes)
    rows = []
    for well in wells:
        classified = classify_well(well)
        joined = join_well_to_grid(classified)
        row = asdict(well)
        for field_name in _DATE_FIELDS:
            if row[field_name] is not None:
                row[field_name] = row[field_name].isoformat()
        row["risk_tier"] = classified.risk_tier.value
        row["risk_reason"] = classified.risk_reason
        row["grid_lat"] = joined.grid_lat
        row["grid_lng"] = joined.grid_lng
        row["in_floodlens_coverage"] = joined.in_floodlens_coverage
        rows.append(row)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/processed/wells.json", help="Output JSON path")
    args = parser.parse_args(argv)

    rows = build_dataset()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2))
    print(f"Wrote {len(rows)} wells to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
