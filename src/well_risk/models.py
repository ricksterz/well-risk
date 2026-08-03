"""
Data model for classified well records.

Fields on WellRecord mirror confirmed SONRIS attribute names 1:1 (see
schema_explore.py) - only a subset actually used downstream is carried,
not all 85. RiskTier and the LEGEND-based classification live in
classify.py, which builds ClassifiedWell from WellRecord.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class RiskTier(str, Enum):
    """Ordered worst-to-best. Values are the labels shown in the UI."""

    CRITICAL = "critical"  # explicitly flagged orphan, or unlocatable
    HIGH = "high"  # temporarily abandoned / no-future-utility shut-in
    MEDIUM = "medium"  # inactive, expired permit, waiting on market/pipeline
    LOW = "low"  # properly plugged and abandoned per regulation
    ACTIVE = "active"  # currently producing or injecting
    UNCLASSIFIED = "unclassified"  # water well, bad data, or unmapped LEGEND code


@dataclass
class WellRecord:
    """One row from DNRSvc/OC MapServer layer 0, confirmed field names only."""

    well_serial_num: int
    api_num: str | None
    well_name: str | None
    organization_id: str | None
    org_operator_name: str | None
    field_id: str | None
    field_name: str | None
    parish_code: str | None
    parish_name: str | None
    surface_lat_dec_deg: float | None
    surface_long_dec_deg: float | None
    legend: str | None
    legend_desc: str | None
    orphaned_flag: str | None
    orphan_status_code: str | None
    well_status_code: str | None
    well_status_date: date | None
    spud_date: date | None
    permit_date: date | None
    measured_depth: float | None
    product_type_code: str | None
    well_class_type_code: str | None
    hyperlink: str | None


@dataclass
class ClassifiedWell:
    well: WellRecord
    risk_tier: RiskTier
    risk_reason: str


@dataclass
class GridJoinedWell:
    """A ClassifiedWell snapped onto a FloodLens-compatible lat/lon grid.

    grid_lat/grid_lng are None when the well falls outside the FloodLens
    bounds preset used for the join - see grid_join.py for why that's
    common for Plaquemines/Lafourche wells today.
    """

    classified: ClassifiedWell
    grid_lat: float | None
    grid_lng: float | None
    in_floodlens_coverage: bool
