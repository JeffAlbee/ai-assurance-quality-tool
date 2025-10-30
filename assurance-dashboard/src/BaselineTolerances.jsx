import { useState, useEffect } from "react";
import axios from "axios";

function BaselineTolerances() {
  const [modelId, setModelId] = useState("flood-risk-predictor");
  const [baselineTimestamp, setBaselineTimestamp] = useState("");
  const [version, setVersion] = useState("v1.0");
  const [notes, setNotes] = useState("Initial snapshot captured after model registration.");
  const [tolerances, setTolerances] = useState({});
  const [status, setStatus] = useState(null);

  const metricFields = [
    "accuracy",
    "rmse",
    "feature_drift",
    "confidence_floor",
    "confidence_variance",
    "domain_violation_count",
    "watts_per_inference"
  ];

  useEffect(() => {
    axios.get(`/v1/model/config`)
      .then((res) => {
        const model = res.data.models?.find((m) => m.model_id === modelId);
        if (model) {
          setBaselineTimestamp(model.baseline_timestamp || "Not set");
        }
      })
      .catch(() => setBaselineTimestamp("Unavailable"));

    axios.get(`/v1/model/tolerances?model_id=${modelId}`)
      .then((res) => setTolerances(res.data.tolerances || {}))
      .catch(() => setTolerances({}));
  }, [modelId]);

  const handleToleranceChange = (metric, bound, value) => {
    setTolerances((prev) => ({
      ...prev,
      [metric]: {
        ...prev[metric],
        [bound]: value === "" ? undefined : parseFloat(value)
      }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post("/v1/model/tolerances", {
        model_id: modelId,
        tolerances
      });
      setStatus("✅ Tolerances saved");
    } catch {
      setStatus("❌ Failed to save tolerances");
    }
  };

  return (
    <main className="px-4 py-6 space-y-6">
      {/* Metadata Section */}
      <section className="bg-white p-4 rounded shadow">
        <h2 className="text-xl font-semibold mb-2">Model Metadata</h2>
        <p className="text-sm"><strong>Model ID:</strong> {modelId}</p>
        <p className="text-sm"><strong>Baseline Timestamp:</strong> {baselineTimestamp}</p>
        <p className="text-sm"><strong>Version:</strong> {version}</p>
        <p className="text-sm"><strong>Notes:</strong> {notes}</p>
      </section>

      {/* Side-by-side layout */}
      <section className="flex flex-col lg:flex-row gap-6">
        {/* Grafana Dashboard */}
        <div className="bg-white p-4 rounded shadow w-full lg:w-2/3">
          <h2 className="text-xl font-semibold mb-2">Grafana Baseline Dashboard</h2>
          <iframe
            src="http://localhost:3000/goto/ff2fx0fi8ouf4d?orgId=1"
            width="30%"
            height="1100"
            frameBorder="0"
            title="Grafana BaselineTolerancesDashboard"
          />
        </div>

        {/* Tolerance Form */}
        <div className="bg-white p-4 rounded shadow w-full lg:w-1/3">
          <h2 className="text-xl font-semibold mb-2">Set Tolerances</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            {metricFields.map((metric) => (
              <div key={metric} className="grid grid-cols-3 gap-2 items-center">
                <label className="text-sm font-medium">{metric}</label>
                <input
                  type="number"
                  step="any"
                  placeholder="Min"
                  value={tolerances[metric]?.min ?? ""}
                  onChange={(e) => handleToleranceChange(metric, "min", e.target.value)}
                  className="border rounded px-2 py-1 text-sm"
                />
                <input
                  type="number"
                  step="any"
                  placeholder="Max"
                  value={tolerances[metric]?.max ?? ""}
                  onChange={(e) => handleToleranceChange(metric, "max", e.target.value)}
                  className="border rounded px-2 py-1 text-sm"
                />
              </div>
            ))}
            <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded text-sm">
              Save Tolerances
            </button>
            {status && <p className="text-sm mt-2">{status}</p>}
          </form>
        </div>
      </section>
    </main>
  );
}

export default BaselineTolerances;
