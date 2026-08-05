"""
Join classified wells onto a lat/lon grid.

Grid convention mirrors FloodLens's own `src/batch_score.py::generate_grid`
(confirmed 2026-08-02 via `gh api repos/ricksterz/floodlens/contents/...`):
points start at (lat_min, lng_min) and step by `resolution` degrees, each
coordinate rounded to 6 decimals. Matching that exactly - not just using a
similar resolution - is what lets grid cells line up with FloodLens's actual
subsidence cells wherever the two projects' coverage overlaps.

SCOPE GAP (unresolved, decided 2026-08-04 not to guess past this): FloodLens's
committed bounds only cover Jefferson, Orleans, St. Bernard, and St. Tammany.
well-risk's target area (Jefferson, Plaquemines, Lafourche) only overlaps
FloodLens on Jefferson. Rather than block on FloodLens extending its bounds
or building a real subsidence model for the other two parishes - both real
decisions outside this project's scope - join_well_to_grid() now separates
two concerns that used to be conflated:

- grid_lat/grid_lng: this project's OWN study-area grid cell, covering all
  three target parishes (WELL_RISK_STUDY_BOUNDS below). Always populated for
  any well with coordinates inside that area, so the well-risk map/heatmap
  has something to plot everywhere in scope.
- in_floodlens_coverage: True only when the well also falls inside
  FloodLens's actual FULL_SERVICE_BOUNDS, meaning grid_lat/grid_lng is ALSO a
  real FloodLens grid point with real subsidence data behind it (same anchor
  + resolution). False elsewhere - correctly, since FloodLens has no data to
  join in Plaquemines or most of Lafourche today. Nothing is fabricated for
  the gap; the API spec's `high_risk_in_floodlens_coverage` stat undercounts
  for those two parishes until the gap closes, by design (see docs/api_spec.md).
"""

from __future__ import annotations

from well_risk.models import ClassifiedWell, GridJoinedWell

# Copied from floodlens/src/batch_score.py as of 2026-08-02. Re-sync if
# FloodLens changes its bounds or resolution.
JEFFERSON_ORLEANS_BOUNDS = {
    "lat_min": 29.920,
    "lat_max": 30.040,
    "lng_min": -90.250,
    "lng_max": -89.950,
}
FULL_SERVICE_BOUNDS = {
    "lat_min": 29.800,
    "lat_max": 30.600,
    "lng_min": -90.350,
    "lng_max": -89.650,
}

# well-risk's own study area: a rough bounding box around Jefferson,
# Plaquemines, and Lafourche parishes, eyeballed from known landmarks (not
# an authoritative parish-boundary file - no such file is wired up yet).
# Generous on purpose: Plaquemines runs down to the mouth of the Mississippi
# (~28.9N near South Pass), Lafourche down to Port Fourchon (~29.1N,
# -90.20W). Anchored independently of FULL_SERVICE_BOUNDS, so cells here
# don't line up with FloodLens's grid - only cells that also pass the
# FloodLens-bounds check in join_well_to_grid do.
WELL_RISK_STUDY_BOUNDS = {
    "lat_min": 28.800,
    "lat_max": 30.100,
    "lng_min": -90.750,
    "lng_max": -89.100,
}

DEFAULT_RESOLUTION = 0.002


def snap_to_grid(
    lat: float,
    lng: float,
    resolution: float = DEFAULT_RESOLUTION,
    bounds: dict = FULL_SERVICE_BOUNDS,
) -> tuple[float, float] | None:
    """Snap (lat, lng) to the nearest grid point within `bounds`, or None if out of bounds."""
    if not (bounds["lat_min"] <= lat <= bounds["lat_max"]):
        return None
    if not (bounds["lng_min"] <= lng <= bounds["lng_max"]):
        return None

    lat_steps = round((lat - bounds["lat_min"]) / resolution)
    lng_steps = round((lng - bounds["lng_min"]) / resolution)
    grid_lat = round(bounds["lat_min"] + lat_steps * resolution, 6)
    grid_lng = round(bounds["lng_min"] + lng_steps * resolution, 6)
    return grid_lat, grid_lng


def join_well_to_grid(classified: ClassifiedWell, resolution: float = DEFAULT_RESOLUTION) -> GridJoinedWell:
    well = classified.well
    if well.surface_lat_dec_deg is None or well.surface_long_dec_deg is None:
        return GridJoinedWell(classified=classified, grid_lat=None, grid_lng=None, in_floodlens_coverage=False)

    lat, lng = well.surface_lat_dec_deg, well.surface_long_dec_deg

    floodlens_snap = snap_to_grid(lat, lng, resolution, FULL_SERVICE_BOUNDS)
    if floodlens_snap is not None:
        grid_lat, grid_lng = floodlens_snap
        return GridJoinedWell(classified=classified, grid_lat=grid_lat, grid_lng=grid_lng, in_floodlens_coverage=True)

    study_snap = snap_to_grid(lat, lng, resolution, WELL_RISK_STUDY_BOUNDS)
    if study_snap is not None:
        grid_lat, grid_lng = study_snap
        return GridJoinedWell(classified=classified, grid_lat=grid_lat, grid_lng=grid_lng, in_floodlens_coverage=False)

    return GridJoinedWell(classified=classified, grid_lat=None, grid_lng=None, in_floodlens_coverage=False)
