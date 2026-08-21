# Multi-stage build, mirrors floodlens's single-service Docker deploy.
# Stage 1: build the frontend. Vite bakes VITE_* env vars in at build time,
# not runtime, so the Mapbox token has to be a build arg here.
FROM node:20-slim AS frontend-build
ARG VITE_MAPBOX_TOKEN
ENV VITE_MAPBOX_TOKEN=${VITE_MAPBOX_TOKEN}
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + the dataset pull. Rebuilding this image
# re-pulls fresh SONRIS data (~31 paginated ArcGIS requests) - a deploy is
# how this project's "batch refresh" happens, there's no separate cron yet.
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
RUN python -m well_risk.pipeline --output data/processed/wells.json

ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn well_risk.api:app --host 0.0.0.0 --port ${PORT}"]
