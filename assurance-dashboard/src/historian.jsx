import { useState, useEffect } from "react";
import axios from "axios";

function Historian() {
  const [modelId, setModelId] = useState("flood-risk-predictor");
  const [violations, setViolations] = useState([]);
  const [status, setStatus] = useState(null);

  const [selectedMetric, setSelectedMetric] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  useEffect(() => {
    if (!modelId) return;

    axios
      .get(`http://localhost:9100/v1/history/logs?model_id=${modelId}`)
      .then((res) => {
        console.log("Fetched historian logs:", res.data);
        if (Array.isArray(res.data)) {
          const sorted = [...res.data].sort(
            (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
          );
          setViolations(sorted);
          setStatus(null);
        } else {
          setViolations([]);
          setStatus("❌ Unexpected response format");
        }
      })
      .catch((err) => {
        console.error("Historian fetch error:", err);
        setViolations([]);
        setStatus("❌ Failed to fetch historian logs");
      });
  }, [modelId]);

  const exportCSV = () => {
    const header = "timestamp,metric,type,value,threshold\n";
    const rows = filteredViolations.flatMap((entry) =>
      Array.isArray(entry.violations)
        ? entry.violations.map(
            (v) =>
              `${entry.timestamp},${v.metric},${v.type},${v.value},${v.threshold}`
          )
        : []
    );
    const blob = new Blob([header + rows.join("\n")], {
      type: "text/csv",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${modelId}-violations.csv`;
    link.click();
  };

  const triggerArchive = () => {
    axios
      .post("http://localhost:9100/v1/history/archive", null, {
        params: { model_id: modelId },
      })
      .then((res) => {
        const count = res.data.archived_count ?? 0;
        if (count === 0) {
          alert("✅ Archive ran, but no entries older than 30 days were found.");
        } else {
          alert(`✅ Archived ${count} entries for ${modelId}`);
        }
      })
      .catch((err) => {
        console.error("Archive error:", err);
        alert("❌ Failed to archive history");
      });
  };

  const filteredViolations = violations.filter((entry) => {
    const ts = new Date(entry.timestamp);

    if (startDate && ts < new Date(startDate)) return false;
    if (endDate && ts > new Date(endDate)) return false;

    if (selectedMetric) {
      const hasMetric = entry.violations.some((v) => v.metric === selectedMetric);
      if (!hasMetric) return false;
    }

    return true;
  });

  const latestTimestamp =
    violations.length > 0 ? violations[0]?.timestamp : null;

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

        {/* Filter Controls */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <label className="block font-medium mb-1">Filter by Metric</label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="border rounded px-3 py-2 w-full"
            >
              <option value="">All Metrics</option>
              <option value="accuracy">Accuracy</option>
              <option value="precision">Precision</option>
              <option value="recall">Recall</option>
              <option value="f1_score">F1 Score</option>
              <option value="latency">Latency</option>
              <option value="throughput">Throughput</option>
              <option value="drift_score">Drift Score</option>
              <option value="confidence_variance">Confidence Variance</option>
              <option value="false_positive_rate">False Positive Rate</option>
              <option value="true_negative_rate">True Negative Rate</option>
            </select>
          </div>
          <div>
            <label className="block font-medium mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="border rounded px-3 py-2 w-full"
            />
          </div>
          <div>
            <label className="block font-medium mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="border rounded px-3 py-2 w-full"
            />
          </div>
        </div>
      </div>

      {/* Scrollable Violation Log */}
      <div className="bg-white p-4 rounded shadow h-[600px] overflow-y-scroll">
        <h2 className="text-xl font-semibold mb-4">Violation History</h2>

        {/* Summary Header */}
        {filteredViolations.length > 0 && (
          <div className="mb-4 text-sm text-gray-700">
            <p>
              <strong>Total Entries:</strong> {filteredViolations.length}
            </p>
            <p>
              <strong>Latest Timestamp:</strong>{" "}
              {latestTimestamp || "—"}
            </p>
            <div className="mt-2 flex gap-2">
              <button
                onClick={exportCSV}
                className="px-3 py-1 bg-purple-600 text-white rounded text-sm"
              >
                Export CSV
              </button>
              <button
                onClick={triggerArchive}
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm"
              >
                Archive History
              </button>
            </div>
          </div>
        )}

        {filteredViolations.length === 0 ? (
          <p className="text-sm text-gray-500">
            No violations found for model <strong>{modelId}</strong>.
          </p>
        ) : (
          <ul className="space-y-4">
            {filteredViolations.map((entry, idx) => (
              <li key={idx} className="border-b pb-2">
                <p className="text-sm font-medium text-gray-700">
                  <strong>Timestamp:</strong>{" "}
                  {entry?.timestamp || "Unknown"}
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
                    <li className="text-gray-500">
                      No violation details
                    </li>
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
