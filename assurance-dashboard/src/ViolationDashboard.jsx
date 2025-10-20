import React, { useState } from "react";
import axios from "axios";

const formatLabel = (key) =>
  key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());

const ViolationDashboard = () => {
  const [modelId, setModelId] = useState("");
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchViolations = async () => {
    if (!modelId.trim()) {
      setError("Please enter a model ID.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await axios.get(`http://localhost:8000/v1/violations?model_id=${modelId}`);
      setViolations(res.data);
    } catch (err) {
      console.error("Failed to fetch violations", err);
      setError("Failed to fetch violations. Please check the model ID or try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Violation Log</h2>

      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={modelId}
          onChange={(e) => setModelId(e.target.value)}
          placeholder="Enter Model ID (e.g. bridge-risk-v1)"
          className="border px-3 py-2 rounded w-64"
        />
        <button
          onClick={fetchViolations}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          {loading ? "Loading..." : "Fetch"}
        </button>
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {violations.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border border-gray-300">
            <thead>
              <tr className="bg-gray-100 text-left">
                <th className="px-2 py-2">Metric</th>
                <th className="px-2 py-2">Value</th>
                <th className="px-2 py-2">Low</th>
                <th className="px-2 py-2">High</th>
                <th className="px-2 py-2">Type</th>
                <th className="px-2 py-2">User</th>
                <th className="px-2 py-2">Time</th>
              </tr>
            </thead>
            <tbody>
              {violations.map((v) => {
                const isViolation = v.value < v.baseline_low || v.value > v.baseline_high;
                const statusColor = isViolation ? "text-red-600 font-semibold" : "text-green-600";

                return (
                  <tr key={v.id} className="border-t border-gray-200">
                    <td className="px-2 py-2 font-medium">{formatLabel(v.metric)}</td>
                    <td className="px-2 py-2 font-mono">{v.value}</td>
                    <td className="px-2 py-2 font-mono">{v.baseline_low}</td>
                    <td className="px-2 py-2 font-mono">{v.baseline_high}</td>
                    <td className="px-2 py-2">{v.violation_type}</td>
                    <td className="px-2 py-2">{v.user}</td>
                    <td className="px-2 py-2">{new Date(v.timestamp).toLocaleString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        !loading && <p className="text-gray-500 text-sm">No violations found for this model.</p>
      )}
    </div>
  );
};

export default ViolationDashboard;
