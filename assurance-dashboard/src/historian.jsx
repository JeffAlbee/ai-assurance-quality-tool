import { useState, useEffect } from "react";
import axios from "axios";

function Historian() {
  const [modelId, setModelId] = useState("flood-risk-predictor");
  const [violations, setViolations] = useState([]);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (!modelId) return;
    axios.get(`/v1/model/violations?model_id=${modelId}`)
      .then((res) => {
        console.log("Fetched violations:", res.data);
        if (Array.isArray(res.data)) {
          setViolations(res.data);
          setStatus(null);
        } else {
          setViolations([]);
          setStatus("❌ Unexpected response format");
        }
      })
      .catch((err) => {
        console.error("Violation fetch error:", err);
        setViolations([]);
        setStatus("❌ Failed to fetch violations");
      });
  }, [modelId]);

  return (
    <section className="space-y-6">
      {/* Search Header */}
      <div className="bg-white p-4 rounded shadow">
        <h2 className="text-xl font-semibold mb-2">Historian Search</h2>
        <input
          type="text"
          value={modelId}
          onChange={(e) => setModelId(e.target.value)}
          placeholder="Enter model ID"
          className="border rounded px-3 py-2 w-full text-sm"
        />
        {status && <p className="text-sm text-red-600 mt-2">{status}</p>}
      </div>

      {/* Scrollable Violation Log */}
      <div className="bg-white p-4 rounded shadow h-[600px] overflow-y-scroll">
        <h2 className="text-xl font-semibold mb-4">Violation History</h2>
        {violations.length === 0 ? (
          <p className="text-sm text-gray-500">
            No violations found for model <strong>{modelId}</strong>.
          </p>
        ) : (
          <ul className="space-y-4">
            {violations.map((entry, idx) => (
              <li key={idx} className="border-b pb-2">
                <p className="text-sm font-medium text-gray-700">
                  <strong>Timestamp:</strong> {entry?.timestamp || "Unknown"}
                </p>
                <ul className="list-disc ml-4 text-sm text-red-600">
                  {Array.isArray(entry?.violations) ? (
                    entry.violations.map((v, i) => (
                      <li key={i}>
                        {v?.metric || "Unknown"}{" "}
                        {v?.type === "min" ? "below" : "above"} threshold:{" "}
                        {v?.value ?? "?"} vs {v?.threshold ?? "?"}
                      </li>
                    ))
                  ) : (
                    <li className="text-gray-500">No violation details</li>
                  )}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

export default Historian;
