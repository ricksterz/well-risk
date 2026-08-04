import { useEffect, useState } from "react";
import { fetchParishes, fetchSummary, fetchWells } from "./api.js";
import FilterBar from "./components/FilterBar.jsx";
import MetricCards from "./components/MetricCards.jsx";
import MapView from "./components/MapView.jsx";
import RiskList from "./components/RiskList.jsx";

export default function App() {
  const [parishes, setParishes] = useState([]);
  const [summary, setSummary] = useState(null);
  const [wells, setWells] = useState([]);
  const [parish, setParish] = useState("");
  const [riskTier, setRiskTier] = useState("");

  useEffect(() => {
    fetchParishes().then((d) => setParishes(d.parishes));
  }, []);

  useEffect(() => {
    fetchSummary(parish).then(setSummary);
  }, [parish]);

  useEffect(() => {
    fetchWells({ parish, riskTier }).then((d) => setWells(d.wells));
  }, [parish, riskTier]);

  const filteredWells = riskTier ? wells.filter((w) => w.risk_tier === riskTier) : wells;

  return (
    <div className="app">
      <header>
        <h1>Well risk dashboard</h1>
        <p className="subtitle">Louisiana orphan &amp; abandonment risk, joined to flood subsidence</p>
      </header>

      <FilterBar
        parishes={parishes}
        parish={parish}
        onParishChange={setParish}
        riskTier={riskTier}
        onRiskTierChange={setRiskTier}
      />

      <MetricCards summary={summary} />

      <div className="main-grid">
        <MapView wells={filteredWells} />
        <RiskList wells={filteredWells} />
      </div>
    </div>
  );
}
