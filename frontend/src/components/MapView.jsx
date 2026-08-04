import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import MapPlaceholder from "./MapPlaceholder.jsx";

const TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

const TIER_COLOR = {
  critical: "#e24b4a",
  high: "#e24b4a",
  medium: "#ef9f27",
  low: "#888780",
  active: "#888780",
  unclassified: "#888780",
};

const TIER_BADGE_CLASS = {
  critical: "badge-danger",
  high: "badge-danger",
  medium: "badge-warning",
  low: "badge-neutral",
  active: "badge-neutral",
  unclassified: "badge-neutral",
};

const DEFAULT_CENTER = [-90.05, 29.55]; // Jefferson/Plaquemines/Lafourche area
const DEFAULT_ZOOM = 8;

function MapboxView({ wells }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);

  useEffect(() => {
    mapboxgl.accessToken = TOKEN;
    const dark = matchMedia("(prefers-color-scheme: dark)").matches;
    mapRef.current = new mapboxgl.Map({
      container: containerRef.current,
      style: dark ? "mapbox://styles/mapbox/dark-v11" : "mapbox://styles/mapbox/light-v11",
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
    });
    mapRef.current.addControl(new mapboxgl.NavigationControl(), "top-right");
    return () => mapRef.current?.remove();
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    const located = wells.filter((w) => w.surface_lat_dec_deg != null && w.surface_long_dec_deg != null);
    located.forEach((w) => {
      const badgeClass = TIER_BADGE_CLASS[w.risk_tier] || "badge-neutral";
      const popup = new mapboxgl.Popup({ offset: 12 }).setHTML(
        `<p class="map-popup-name">${w.well_name || w.well_serial_num}</p>` +
          `<p class="map-popup-parish">${w.parish_name || ""}</p>` +
          `<span class="badge ${badgeClass}">${w.risk_tier}</span>`
      );
      const marker = new mapboxgl.Marker({ color: TIER_COLOR[w.risk_tier] || TIER_COLOR.low })
        .setLngLat([w.surface_long_dec_deg, w.surface_lat_dec_deg])
        .setPopup(popup)
        .addTo(mapRef.current);
      markersRef.current.push(marker);
    });

    if (located.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      located.forEach((w) => bounds.extend([w.surface_long_dec_deg, w.surface_lat_dec_deg]));
      mapRef.current.fitBounds(bounds, { padding: 40, maxZoom: 11, duration: 0 });
    }
  }, [wells]);

  return (
    <div className="map-panel">
      <p className="panel-label">Well locations</p>
      <div ref={containerRef} className="map-area mapbox-area" />
      <div className="map-legend">
        <span><i className="legend-dot dot-critical" />Critical / high</span>
        <span><i className="legend-dot dot-medium" />Medium</span>
        <span><i className="legend-dot dot-low" />Low / active</span>
      </div>
    </div>
  );
}

// No token configured (e.g. CI, a fresh checkout without .env) - fall back
// to the coordinate-frame placeholder rather than a broken map div.
export default function MapView({ wells }) {
  if (!TOKEN) return <MapPlaceholder wells={wells} />;
  return <MapboxView wells={wells} />;
}
