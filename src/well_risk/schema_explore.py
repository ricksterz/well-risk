"""
Schema discovery for Louisiana SONRIS oil & gas well data.

Phase 1 of well-risk: before any field names are hardcoded elsewhere in this
package, this script queries the live data sources and prints back what they
actually return - field names, types, and a sample record - so a human can
confirm them before `classify.py` or `grid_join.py` are built on top of
guesses.

Two sources are probed, per the two options identified in the original
prototype:

1. ArcGIS REST query endpoint (LTRC/SONRIS MapServer) - fast, but per its own
   service metadata this is a stale snapshot (~April 2018). Useful for a
   first look at field naming conventions, not for production data.
2. DNR's bulk download portal (sonris-gis.dnr.state.la.us) - the current,
   daily-updated source, reportedly behind some kind of login/terms gate of
   unknown strictness. `check_dnr_bulk_portal_gate()` fetches the login page
   and reports what it actually contains (a real credentials form vs. a
   click-through terms page vs. something unclear) instead of assuming
   either. It does not submit the form or attempt to authenticate.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass

import requests

ARCGIS_QUERY_URL = "https://giswebnew.dotd.la.gov/arcgis/rest/services/LTRC/SONRIS/MapServer/0/query"
DNR_BULK_LOGIN_URL = "https://sonris-gis.dnr.state.la.us/website/DownloadLogin.html"

# Rough bbox covering Jefferson / Plaquemines / Lafourche parishes (Barataria
# Basin core). Only used to keep exploratory queries small - not a claim
# about exact parish boundaries.
DEFAULT_BBOX = (-90.4, 29.2, -89.7, 30.1)

DEFAULT_TIMEOUT = 30.0


@dataclass
class ArcGISSchemaResult:
    fields: list[dict]
    sample_record: dict | None
    raw_response: dict


def explore_arcgis_schema(
    bbox: tuple[float, float, float, float] | None = DEFAULT_BBOX,
    url: str = ARCGIS_QUERY_URL,
    sample_size: int = 5,
    timeout: float = DEFAULT_TIMEOUT,
) -> ArcGISSchemaResult:
    """
    Query the ArcGIS REST endpoint for a small sample and return its real
    field list plus one sample record's raw attributes. No field names are
    assumed here - only whatever the service actually reports.
    """
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "json",
        "resultRecordCount": sample_size,
        "returnGeometry": "true",
    }
    if bbox:
        min_lon, min_lat, max_lon, max_lat = bbox
        params["geometry"] = f"{min_lon},{min_lat},{max_lon},{max_lat}"
        params["geometryType"] = "esriGeometryEnvelope"
        params["spatialRel"] = "esriSpatialRelIntersects"
        params["inSR"] = "4326"

    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"ArcGIS endpoint returned an error payload: {data['error']}")

    fields = data.get("fields", [])
    features = data.get("features", [])
    sample_record = features[0]["attributes"] if features else None

    return ArcGISSchemaResult(fields=fields, sample_record=sample_record, raw_response=data)


def print_arcgis_schema(result: ArcGISSchemaResult, url: str = ARCGIS_QUERY_URL) -> None:
    print(f"ArcGIS endpoint: {url}")
    if not result.fields:
        print("  No 'fields' key in the response - endpoint may have changed shape.")
    else:
        print(f"  {len(result.fields)} fields returned:")
        for f in result.fields:
            print(f"    {f.get('name')!r:30s} type={f.get('type')!r:30s} alias={f.get('alias')!r}")

    print()
    if result.sample_record is None:
        print("  No features returned for this bbox/query - try a wider --bbox.")
    else:
        print("  Sample record (raw attributes):")
        print(json.dumps(result.sample_record, indent=4, default=str))


def check_dnr_bulk_portal_gate(url: str = DNR_BULK_LOGIN_URL, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """
    Fetch the DNR bulk-download login page and report what kind of gate it
    actually presents, instead of assuming it needs real credentials.

    This only inspects the HTML (form presence, password inputs, terms/agree
    language) - it does not submit the form or attempt to authenticate.
    """
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    html = resp.text
    lower_html = html.lower()

    return {
        "status_code": resp.status_code,
        "final_url": resp.url,
        "content_length": len(html),
        "has_form": "<form" in lower_html,
        "has_password_field": 'type="password"' in lower_html,
        "mentions_terms": any(
            phrase in lower_html for phrase in ("terms of use", "i agree", "accept the terms")
        ),
    }


def print_dnr_gate_findings(findings: dict, url: str = DNR_BULK_LOGIN_URL) -> None:
    print(f"DNR bulk portal: {url}")
    print(f"  HTTP {findings['status_code']}, final URL: {findings['final_url']}")
    print(f"  Page has a <form>: {findings['has_form']}")
    print(f"  Page has a password input: {findings['has_password_field']}")
    print(f"  Page mentions terms/agree language: {findings['mentions_terms']}")
    if findings["has_password_field"]:
        print("  -> Looks like it wants real credentials.")
    elif findings["mentions_terms"]:
        print("  -> Looks like a click-through terms gate, not real auth - confirm manually.")
    else:
        print("  -> Unclear from page structure alone - inspect manually in a browser.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        default=list(DEFAULT_BBOX),
        help="Bounding box for the ArcGIS sample query (default: Jefferson/Plaquemines/Lafourche area)",
    )
    parser.add_argument("--sample-size", type=int, default=5, help="Number of sample records to request")
    parser.add_argument("--arcgis-url", default=ARCGIS_QUERY_URL, help="Override the ArcGIS query endpoint")
    parser.add_argument("--dnr-gate-url", default=DNR_BULK_LOGIN_URL, help="Override the DNR bulk portal login URL")
    parser.add_argument("--skip-arcgis", action="store_true", help="Skip the ArcGIS schema query")
    parser.add_argument("--skip-dnr-gate", action="store_true", help="Skip the DNR bulk portal gate check")
    args = parser.parse_args(argv)

    exit_code = 0

    if not args.skip_arcgis:
        print("=" * 70)
        print("ArcGIS REST endpoint schema")
        print("=" * 70)
        try:
            result = explore_arcgis_schema(bbox=tuple(args.bbox), url=args.arcgis_url, sample_size=args.sample_size)
            print_arcgis_schema(result, url=args.arcgis_url)
        except Exception as exc:
            print(f"  FAILED: {exc}", file=sys.stderr)
            exit_code = 1
        print()

    if not args.skip_dnr_gate:
        print("=" * 70)
        print("DNR bulk download portal gate check")
        print("=" * 70)
        try:
            findings = check_dnr_bulk_portal_gate(url=args.dnr_gate_url)
            print_dnr_gate_findings(findings, url=args.dnr_gate_url)
        except Exception as exc:
            print(f"  FAILED: {exc}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
