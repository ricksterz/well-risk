# louisiana-well-risk

Pulls Louisiana DNR/SONRIS oil & gas well data (location, age, status) for
Jefferson, Plaquemines, and Lafourche parishes, classifies wells by
abandonment/orphan risk, and joins the result onto a lat/lon grid so it can
be merged with the existing [FloodLens](https://github.com/ricksterz/floodlens)
subsidence dataset as an additional risk layer.

This project grew out of a prototype script (`sonris_floodlens_join.py`) that
sketched the full pipeline against unverified field-name guesses. It's being
rebuilt here as a proper package, phase by phase, confirming real data before
any field names get hardcoded.

## Status: Phase 1 - schema discovery

The live SONRIS field names are **unverified**. Before `classify.py` or
`grid_join.py` exist, `schema_explore.py` needs to be run against the real
endpoints to confirm actual field names. Nothing downstream should assume a
field name until it's been seen in real output.

Two possible data sources, both unconfirmed from this environment:

- **ArcGIS REST query endpoint** (`giswebnew.dotd.la.gov/.../SONRIS/MapServer/0/query`)
  - fast, but per its own service metadata it's a stale snapshot (~April 2018).
- **DNR bulk download portal** (`sonris-gis.dnr.state.la.us`)
  - the current, daily-updated source, but reportedly sits behind some kind
    of login/terms gate of unknown strictness.

`schema_explore.py` probes both: it prints the ArcGIS endpoint's real field
list and a sample record, and inspects the DNR portal's login page to report
what kind of gate it actually presents (real credentials vs. click-through
terms vs. unclear) rather than assuming either.

## Project layout

```
well-risk/
├── pyproject.toml           src/ layout, well_risk package, deps: pandas, requests, pytest
├── src/
│   └── well_risk/
│       ├── __init__.py
│       └── schema_explore.py   Phase 1: confirm real field names before anything else
└── tests/                       classify.py / grid_join.py tests land here once built
```

`classify.py` (abandonment/orphan risk classification) and `grid_join.py`
(well density/age joined onto a configurable lat/lon grid, matching
FloodLens's grid resolution) are next, once real field names are confirmed
from `schema_explore.py`'s output.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running schema discovery

```bash
python -m well_risk.schema_explore
# or, after `pip install -e .`:
well-risk-schema-explore
```

Options:

```bash
well-risk-schema-explore --bbox MIN_LON MIN_LAT MAX_LON MAX_LAT --sample-size 5
well-risk-schema-explore --skip-dnr-gate     # only query the ArcGIS endpoint
well-risk-schema-explore --skip-arcgis       # only check the DNR portal gate
```

## Testing

```bash
pytest
```
