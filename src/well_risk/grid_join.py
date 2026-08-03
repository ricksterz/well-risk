"""
Join classified wells onto FloodLens's lat/lon grid.

Grid convention mirrors FloodLens's own `src/batch_score.py::generate_grid`
(confirmed 2026-08-02 via `gh api repos/ricksterz/floodlens/contents/...`):
points start at (lat_min, lng_min) and step by `resolution` degrees, each
coordinate rounded to 6 decimals. Matching that exactly - not just using a
similar resolution - is what lets this project's grid cells actually line
up with FloodLens's subsidence cells for a join.

IMPORTANT SCOPE GAP: FloodLens's committed bounds presets only cover
Jefferson, Orleans, St. Bernard, and St. Tammany parishes. well-risk's
target area (Jefferson, Plaquemines, Lafourche, per CLAUDE.md/README) only
overlaps FloodLens on Jefferson - most of Plaquemines and all of Lafourche
fall outside both presets below. Wells outside the chosen bounds are
returned with grid_lat/grid_lng=None and in_floodlens_coverage=False rather
than silently snapped to a meaningless nearest edge. Closing this gap means
either FloodLens extending FULL_SERVICE_BOUNDS, or this project computing
its own subsidence grid for the uncovered parishes - a decision for
whoever owns both repos, not something to guess here.
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
DEFAULT_RESOLUTION = 0.002


def snap_to_grid(
    lat: float,
    lng: float,
    resolution: float = DEFAULT_RESOLUTION,
    bounds: dict = FULL_SERVICE_BOUNDS,
) -> tuple[float, float] | None:
    """Snap (lat, lng) to the nearest FloodLens grid point, or None if out of bounds."""
    if not (bounds["lat_min"] <= lat <= bounds["lat_max"]):
        return None
    if not (bounds["lng_min"] <= lng <= bounds["lng_max"]):
        return None

    lat_steps = round((lat - bounds["lat_min"]) / resolution)
    lng_steps = round((lng - bounds["lng_min"]) / resolution)
    grid_lat = round(bounds["lat_min"] + lat_steps * resolution, 6)
    grid_lng = round(bounds["lng_min"] + lng_steps * resolution, 6)
    return grid_lat, grid_lng


def join_well_to_grid(
    classified: ClassifiedWell,
    resolution: float = DEFAULT_RESOLUTION,
    bounds: dict = FULL_SERVICE_BOUNDS,
) -> GridJoinedWell:
    well = classified.well
    if well.surface_lat_dec_deg is None or well.surface_long_dec_deg is None:
        return GridJoinedWell(classified=classified, grid_lat=None, grid_lng=None, in_floodlens_coverage=False)

    snapped = snap_to_grid(well.surface_lat_dec_deg, well.surface_long_dec_deg, resolution, bounds)
    if snapped is None:
        return GridJoinedWell(classified=classified, grid_lat=None, grid_lng=None, in_floodlens_coverage=False)

    grid_lat, grid_lng = snapped
    return GridJoinedWell(classified=classified, grid_lat=grid_lat, grid_lng=grid_lng, in_floodlens_coverage=True)
