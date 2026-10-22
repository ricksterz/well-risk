import { useEffect, useState } from "react";
import { fetchParishes, fetchSummary, fetchWells } from "./api.js";
import FilterBar from "./components/FilterBar.jsx";
import MetricCards from "./components/MetricCards.jsx";
import MapView from "./components/MapView.jsx";
import RiskList from "./components/RiskList.jsx";
import Disclaimers from "./components/Disclaimers.jsx";

export default function App() {
  const [parishes, setParishes] = useState([]);
  const [summary, setSummary] = useState(null);
  const [wells, setWells] = useState([]);
  const [parish, setParish] = useState("");
  const [riskTier, setRiskTier] = useState("");
  const [error, setError] = useState(null);

  // On failure, clear what was showing rather than leave stale numbers up
  // under a filter they no longer match.
  const onFail = (clear) => (err) => {
    console.error(err);
    setError("The data service isn't responding, so nothing shown here is current. Try again in a moment.");
    clear();
  };

  useEffect(() => {
    fetchParishes()
      .then((d) => {
        setParishes(d.parishes);
        setError(null);
      })
      .catch(onFail(() => setParishes([])));
  }, []);

  useEffect(() => {
    fetchSummary(parish)
      .then((d) => {
        setSummary(d);
        setError(null);
      })
      .catch(onFail(() => setSummary(null)));
  }, [parish]);

  useEffect(() => {
    fetchWells({ parish, riskTier })
      .then((d) => {
        setWells(d.wells);
        setError(null);
      })
      .catch(onFail(() => setWells([])));
  }, [parish, riskTier]);

  const filteredWells = riskTier ? wells.filter((w) => w.risk_tier === riskTier) : wells;

  return (
    <div className="app">
      <header>
        <h1>Well risk dashboard</h1>
        <p className="subtitle">Louisiana orphan &amp; abandonment risk, joined to flood subsidence</p>
      </header>

      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}

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

      <Disclaimers />
    </div>
  );
}
