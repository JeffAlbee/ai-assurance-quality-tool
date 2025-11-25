import React, { useState, useEffect } from "react";
import { metricGroups } from "./metrics";       // non-system metrics
import { systemMetrics } from "./SystemMetrics"; // system-level metrics

function ConsultingMetrics() {
  const [licenseInfo, setLicenseInfo] = useState(null);
  const [results, setResults] = useState({});
  const [notes, setNotes] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/v1/license/status")
      .then((res) => res.json())
      .then((data) => setLicenseInfo(data))
      .catch(() => {
        console.warn("License status fetch failed");
        setLicenseInfo({ status: "inactive", level: "basic" });
      });
  }, []);

  const MetricCard = ({ name, formula, relevance, inputs, compute, statusThreshold }) => {
    const [values, setValues] = useState({});
    const [result, setResult] = useState(null);

    const handleChange = (key, val) => {
      setValues({ ...values, [key]: val });
    };

    const handleCalculate = () => {
      const score = compute(values);
      setResult(score);
      setResults((prev) => ({ ...prev, [name]: score }));
    };

    const status =
      result === null
        ? null
        : statusThreshold
        ? statusThreshold(result)
        : result < 0.5
        ? { label: "❌ Needs Improvement", color: "text-red-600" }
        : { label: "✅ Acceptable", color: "text-green-600" };

    return (
      <div className="bg-white border rounded p-4 shadow space-y-2">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold">{name}</h3>
          {status && <span className={`font-semibold ${status.color}`}>{status.label}</span>}
        </div>
        <p className="text-sm italic text-gray-700">Formula: {formula}</p>
        <p className="text-sm text-gray-800">{relevance}</p>

        <div className="grid grid-cols-2 gap-2 mt-2">
          {inputs.map((input) => (
            <input
              key={input}
              type="text"
              placeholder={input}
              className="border rounded px-2 py-1 text-sm"
              onChange={(e) => handleChange(input, e.target.value)}
            />
          ))}
        </div>

        <button
          onClick={handleCalculate}
          className="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-sm"
        >
          Calculate
        </button>

        {result !== null && (
          <div className="mt-3 space-y-2">
            <p className="text-sm font-mono">
              Score: {typeof result === "number" ? result.toFixed(4) : JSON.stringify(result)}
            </p>
            {typeof result === "number" && (
              <div className="w-full bg-gray-200 rounded h-3">
                <div
                  className="bg-green-500 h-3 rounded"
                  style={{ width: `${Math.min(Math.max(result * 100, 0), 100)}%` }}
                ></div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // Export JSON report
  const handleExport = () => {
    const payload = {
      timestamp: new Date().toISOString(),
      license: licenseInfo || { status: "unknown", level: "basic" },
      results,
      notes,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "consulting_report.json";
    link.click();
    URL.revokeObjectURL(url);
  };

  // Print report directly (browser dialog allows "Save as PDF")
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="px-4 py-6 space-y-6">
      <h2 className="text-xl font-semibold mb-2">Consulting Tool: Model Performance Assessment</h2>

      {/* System-Level Metrics Section */}
      <section className="space-y-4">
        <h3 className="text-lg font-bold">System-Level Weighted Composite Scores</h3>
        <p className="text-sm text-gray-600">
          High-level metrics calculated by the Historical Data Compiler and stored in the Assurance Service for executive dashboards and reporting.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {systemMetrics.map((m) => (
            <MetricCard key={m.name} {...m} />
          ))}
        </div>
      </section>

      {/* Other Metric Groups */}
      {metricGroups.map((group) => (
        <section key={group.title} className="space-y-4">
          <h3 className="text-lg font-bold">{group.title}</h3>
          <p className="text-sm text-gray-600">{group.description}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {group.metrics.map((m) => (
              <MetricCard key={m.name} {...m} />
            ))}
          </div>
        </section>
      ))}

      {/* Results Summary */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold">Calculated Results Summary</h3>
        {Object.keys(results).length === 0 ? (
          <p className="text-sm text-gray-500">No metrics calculated yet.</p>
        ) : (
          <table className="w-full border-collapse border text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-2 py-1 text-left">Metric</th>
                <th className="border px-2 py-1 text-left">Score</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(results).map(([metric, score]) => (
                <tr key={metric}>
                  <td className="border px-2 py-1">{metric}</td>
                  <td className="border px-2 py-1">
                    {typeof score === "number" ? score.toFixed(4) : JSON.stringify(score)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* Engagement Notes */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold">Engagement Notes</h3>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add context, observations, and next steps for the client…"
          className="w-full border rounded px-3 py-2 text-sm"
          rows={4}
        />
      </section>

      {/* Export & Print Buttons */}
      <div className="flex gap-4 mt-6">
        <button
          onClick={handleExport}
          className="px-4 py-2 bg-purple-700 text-white rounded text-sm"
        >
          Export Report (JSON)
        </button>
        <button
          onClick={handlePrint}
          className="px-4 py-2 bg-green-700 text-white rounded text-sm"
        >
          Print Report (Save as PDF)
        </button>
      </div>
    </div>
  );
}

export default ConsultingMetrics;
