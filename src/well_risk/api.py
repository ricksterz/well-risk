"""
FastAPI backend implementing docs/api_spec.md exactly.

Serves from the materialized dataset written by `well-risk-build-dataset`
(pipeline.py) - not a live ArcGIS query per request, matching the "batch
job, API reads the result" model noted as an open question in the spec.
Reload the process (or wire up a scheduled restart) after rebuilding the
dataset; there's no file-watching/hot-reload of the data here.

In production (see Dockerfile) this process also serves the built frontend
(frontend/dist) as static files, same-origin - matching how FloodLens's
single Flask service works. Locally, run the Vite dev server separately
instead (frontend/dist won't exist until `npm run build`); the static
mount below is skipped when that directory is missing.

Run: uvicorn well_risk.api:app --reload
"""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from well_risk.models import RiskTier

DATASET_PATH = Path(os.environ.get("WELL_RISK_DATASET_PATH", "data/processed/wells.json"))
FRONTEND_DIST = Path(os.environ.get("WELL_RISK_FRONTEND_DIST", "frontend/dist"))
MAP_POINTS_CAP = 5000

_wells: list[dict] = []


def _load_dataset() -> list[dict]:
    if not DATASET_PATH.exists():
        raise RuntimeError(
            f"{DATASET_PATH} not found - run `well-risk-build-dataset` first "
            "(or set WELL_RISK_DATASET_PATH to an existing file)."
        )
    return json.loads(DATASET_PATH.read_text())


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _wells
    _wells = _load_dataset()
    yield


app = FastAPI(title="well-risk API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:5174").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _matches(well: dict, parish: str | None, risk_tiers: list[str] | None, in_floodlens_coverage: bool | None) -> bool:
    if parish and (well.get("parish_name") or "").upper() != parish.upper():
        return False
    if risk_tiers and well.get("risk_tier") not in risk_tiers:
        return False
    if in_floodlens_coverage is not None and well.get("in_floodlens_coverage") != in_floodlens_coverage:
        return False
    return True


_RISK_TIER_SORT_ORDER = {tier.value: i for i, tier in enumerate(RiskTier)}


def _sort_key_risk_tier(well: dict):
    return _RISK_TIER_SORT_ORDER.get(well.get("risk_tier"), len(_RISK_TIER_SORT_ORDER))


_WELL_SUMMARY_FIELDS = (
    "well_serial_num",
    "well_name",
    "parish_name",
    "org_operator_name",
    "risk_tier",
    "risk_reason",
    "surface_lat_dec_deg",
    "surface_long_dec_deg",
    "in_floodlens_coverage",
)


@app.get("/api/wells")
def list_wells(
    parish: str | None = None,
    risk_tier: list[str] | None = Query(default=None),
    in_floodlens_coverage: bool | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="risk_tier", pattern="^(risk_tier|well_status_date)$"),
):
    matched = [w for w in _wells if _matches(w, parish, risk_tier, in_floodlens_coverage)]
    if sort == "risk_tier":
        matched.sort(key=_sort_key_risk_tier)
    else:
        matched.sort(key=lambda w: w.get("well_status_date") or "", reverse=True)

    page = matched[offset : offset + limit]
    return {
        "total": len(matched),
        "limit": limit,
        "offset": offset,
        "wells": [{k: w.get(k) for k in _WELL_SUMMARY_FIELDS} for w in page],
    }


@app.get("/api/wells/map")
def wells_map(
    parish: str | None = None,
    risk_tier: list[str] | None = Query(default=None),
    in_floodlens_coverage: bool | None = None,
):
    # Must stay registered before /api/wells/{well_serial_num} - Starlette
    # matches routes in declaration order, and an unconstrained {int} path
    # param will otherwise swallow the literal "map" segment first (it did,
    # confirmed by a failing test before this ordering fix).
    matched = [
        w
        for w in _wells
        if _matches(w, parish, risk_tier, in_floodlens_coverage)
        and w.get("surface_lat_dec_deg") is not None
        and w.get("surface_long_dec_deg") is not None
    ]
    truncated = len(matched) > MAP_POINTS_CAP
    points = [
        {
            "well_serial_num": w["well_serial_num"],
            "lat": w["surface_lat_dec_deg"],
            "lng": w["surface_long_dec_deg"],
            "risk_tier": w["risk_tier"],
        }
        for w in matched[:MAP_POINTS_CAP]
    ]
    return {"truncated": truncated, "points": points}


@app.get("/api/wells/{well_serial_num}")
def get_well(well_serial_num: int):
    for w in _wells:
        if w.get("well_serial_num") == well_serial_num:
            return w
    raise HTTPException(status_code=404, detail=f"well_serial_num {well_serial_num} not found")


@app.get("/api/stats/summary")
def stats_summary(parish: str | None = None):
    matched = [w for w in _wells if _matches(w, parish, None, None)]
    by_tier = {tier.value: 0 for tier in RiskTier}
    for w in matched:
        tier = w.get("risk_tier")
        if tier in by_tier:
            by_tier[tier] += 1

    high_risk_in_coverage = sum(
        1
        for w in matched
        if w.get("risk_tier") in (RiskTier.CRITICAL.value, RiskTier.HIGH.value) and w.get("in_floodlens_coverage")
    )
    parishes_covered = len({w.get("parish_name") for w in matched if w.get("parish_name")})

    return {
        "wells_in_scope": len(matched),
        "by_risk_tier": by_tier,
        "high_risk_in_floodlens_coverage": high_risk_in_coverage,
        "parishes_covered": parishes_covered,
    }


@app.get("/api/parishes")
def parishes():
    counts: dict[str, int] = {}
    for w in _wells:
        name = w.get("parish_name")
        if name:
            counts[name] = counts.get(name, 0) + 1
    return {"parishes": [{"parish_name": name, "well_count": cnt} for name, cnt in sorted(counts.items())]}


# Registered last so it never shadows the /api/* routes above - Starlette
# matches in declaration order, same reasoning as the /api/wells/map fix.
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend-assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # SPA with no client-side routing today - every non-API, non-asset
        # path just gets index.html.
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
