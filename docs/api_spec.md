# well-risk API spec

Not implemented yet - this documents the planned shape so the frontend
scaffold has something concrete to build against. Field names match
`WellRecord` / `ClassifiedWell` / `GridJoinedWell` in `src/well_risk/models.py`
exactly; nothing here introduces a new field name.

Framework choice (not yet built): FastAPI, since it gives typed request/response
models for free from these dataclasses and matches the Python-first stack in
the README. Not a hard requirement - swap if there's a reason to.

## GET /api/wells

List wells with filters, for the risk table.

**Query params**

| Param | Type | Notes |
|---|---|---|
| `parish` | string | matches `parish_name`, case-insensitive. Omit for all. |
| `risk_tier` | string | one of `RiskTier` values (`critical`, `high`, `medium`, `low`, `active`, `unclassified`). Repeatable. |
| `in_floodlens_coverage` | bool | filter by `GridJoinedWell.in_floodlens_coverage` |
| `limit` | int | default 50, max 200 |
| `offset` | int | default 0 |
| `sort` | string | `risk_tier` (default, worst first) or `well_status_date` |

**Response `200`**

```json
{
  "total": 8400,
  "limit": 50,
  "offset": 0,
  "wells": [
    {
      "well_serial_num": 246837,
      "well_name": "SL 21089",
      "parish_name": "LAFOURCHE",
      "org_operator_name": "HILCORP ENERGY COMPANY",
      "risk_tier": "high",
      "risk_reason": "LEGEND_DESC matched 'TEMPORARILY ABANDONED' ('TEMPORARILY ABANDONED WELL  NO PRODUCT SPECIFIED')",
      "surface_lat_dec_deg": 29.19962622,
      "surface_long_dec_deg": -90.358838662,
      "in_floodlens_coverage": false
    }
  ]
}
```

## GET /api/wells/{well_serial_num}

Full detail for one well - every `WellRecord` field plus classification and grid join.

**Response `200`**: `WellRecord` fields flattened + `risk_tier`, `risk_reason`, `grid_lat`, `grid_lng`, `in_floodlens_coverage`.

**Response `404`**: unknown `well_serial_num`.

## GET /api/wells/map

Lightweight points for the map view. Same filters as `/api/wells` minus pagination (capped at 5,000 points server-side; returns `truncated: true` if the filtered set is larger - the frontend should push the user toward narrower filters rather than silently dropping wells).

**Response `200`**

```json
{
  "truncated": false,
  "points": [
    { "well_serial_num": 246837, "lat": 29.199626, "lng": -90.358839, "risk_tier": "high" }
  ]
}
```

`lat`/`lng` here are the raw `surface_lat_dec_deg`/`surface_long_dec_deg`, not the FloodLens-snapped grid point - the map plots actual well locations, the grid join is for overlaying FloodLens's subsidence layer underneath, a separate concern.

## GET /api/stats/summary

Backs the dashboard's metric cards.

**Query params**: same `parish` filter as `/api/wells` (so cards reflect the current filter state).

**Response `200`**

```json
{
  "wells_in_scope": 8400,
  "by_risk_tier": { "critical": 88, "high": 524, "medium": 1310, "low": 4200, "active": 2100, "unclassified": 178 },
  "high_risk_in_floodlens_coverage": 94,
  "parishes_covered": 3
}
```

`high_risk_in_floodlens_coverage` = wells where `risk_tier` in `{critical, high}` AND `in_floodlens_coverage=true` - this is the number that actually matters once FloodLens's subsidence layer is joined in; see the coverage gap noted in `grid_join.py`. Today that number will undercount badly for Plaquemines/Lafourche since neither is in FloodLens's bounds yet.

## GET /api/parishes

For the parish filter dropdown.

**Response `200`**

```json
{ "parishes": [{ "parish_name": "JEFFERSON", "well_count": 3100 }, { "parish_name": "PLAQUEMINES", "well_count": 2900 }, { "parish_name": "LAFOURCHE", "well_count": 2400 }] }
```

## Open questions before implementing

- Refresh cadence: SONRIS is queried live today (`schema_explore.py`); a real API needs a cached/materialized dataset (nightly batch through `classify.py` + `grid_join.py`) rather than hitting ArcGIS per request - matches how `batch_score.py` works on the FloodLens side.
- Auth: none planned, matches FloodLens's public-data posture. Revisit if this ever exposes non-public data.
- `ORPHAN_STATUS_CODE`'s meaning is still unconfirmed (see `classify.py`) - decide whether to expose the raw code in the API before it's decoded, or hold it back.
