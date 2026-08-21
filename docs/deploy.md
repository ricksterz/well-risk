# Deploying well-risk

Single Docker service on Render, matching FloodLens's deploy shape
(`render.yaml`, `Dockerfile` at repo root). Verified locally:

- `npm run build` produces `frontend/dist` correctly (confirmed 2026-08-04).
- `WELL_RISK_FRONTEND_DIST=frontend/dist uvicorn well_risk.api:app` serves
  both the built frontend and `/api/*` from one process, same-origin,
  confirmed via the browser (network tab showed only same-origin requests,
  real data rendered).
- `.dockerignore` keeps `.env` (and the real Mapbox token in it) out of the
  build context - it never gets copied into the image as a file. The token
  only enters the image as a build ARG (below).

Not yet verified: the actual `docker build` (no Docker available in this
environment) and Render's real behavior deploying it. Two things worth
confirming on first deploy:

1. **Render passes env vars as Docker build args** for `runtime: docker`
   services - this is what lets `ARG VITE_MAPBOX_TOKEN` in the Dockerfile
   pick up the `VITE_MAPBOX_TOKEN` env var set in the Render dashboard.
   Documented Render behavior, but unverified against this specific
   Dockerfile - if the map falls back to the coordinate-frame placeholder
   after deploy, this is the first thing to check.
2. **Build time**: the Docker build re-pulls all 30,375 wells from SONRIS
   (~31 paginated requests) as its last step. Expect a few minutes per
   deploy, not seconds.

## Steps (need your Render account - I can't do this part)

1. Push this repo to GitHub (already done - `ricksterz/well-risk`, `main`).
2. In the Render dashboard: New → Blueprint → connect the `well-risk` repo.
   Render reads `render.yaml` automatically.
3. Before the first deploy, set the `VITE_MAPBOX_TOKEN` env var (dashboard
   → the new service → Environment) - it's marked `sync: false` in
   `render.yaml` so Render won't ask you to commit it, just enter it once.
4. Deploy. First build will take longer than usual (frontend build + full
   SONRIS pull). Subsequent deploys refresh the well dataset automatically
   as part of the build - there's no separate scheduled refresh yet.

## Known gaps at deploy time

- No scheduled dataset refresh - each Render deploy re-pulls fresh data,
  but nothing triggers a deploy on a schedule. A Render cron job hitting
  a redeploy hook (or a GitHub Actions scheduled workflow that pushes an
  empty commit) would close this.
- No auth/rate limiting on the API - fine for public SONRIS data, but
  worth knowing before pointing real traffic at it.
- The FloodLens coverage gap (Plaquemines/Lafourche) is unchanged by
  deployment - see `grid_join.py`'s module docstring.
