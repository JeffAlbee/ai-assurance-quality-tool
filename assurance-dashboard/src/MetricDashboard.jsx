import React from "react";

const label = {
  txid: "demo-001",
  prediction: "safe",
  model_version: "BridgeTypeModel-v1",
  timestamp: "2025-10-15T21:12:34Z",
  metrics: {
    accuracy: 0.92,
    f1_score: 0.88,
    rmse: 1.2,
    feature_drift: 0.03,
    domain_violation_count: 2,
    p95_latency: 180,
    failure_rate: 0.01,
    watts_per_inference: 0.5,
    confidence_floor: 0.81,
    confidence_variance: 0.04,
    model_reliability_score: 0.91,
    audit_governance_score: 0.87,
    trust_quality_score: 0.89,
  },
  baselines: {
    accuracy: { low: 0.88, high: 0.95 },
    f1_score: { low: 0.83, high: 0.90 },
    rmse: { low: 1.0, high: 1.5 },
    feature_drift: { low: 0.0, high: 0.05 },
    domain_violation_count: { low: 0, high: 3 },
    p95_latency: { low: 0, high: 200 },
    failure_rate: { low: 0, high: 0.02 },
    watts_per_inference: { low: 0, high: 0.6 },
    confidence_floor: { low: 0.8, high: 1.0 },
    confidence_variance: { low: 0.0, high: 0.05 },
  },
};

function MetricDashboard({ section }) {
  const { metrics, baselines } = label;

  if (section === "scores") {
    return (
      <div className="space-y-3">
        {["model_reliability_score", "audit_governance_score", "trust_quality_score"].map((key) => (
          <div key={key} className="flex justify-between border-b pb-2">
            <span className="font-medium capitalize">{key.replace(/_/g, " ")}</span>
            <span>{metrics[key]}</span>
          </div>
        ))}
      </div>
    );
  }

  if (section === "metrics") {
    return (
      <table className="w-full text-sm border">
        <thead>
          <tr className="bg-gray-200 text-left">
            <th className="p-2">Metric</th>
            <th className="p-2">Value</th>
            <th className="p-2">Low</th>
            <th className="p-2">High</th>
            <th className="p-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(metrics).map(([key, value]) => {
            if (key.includes("score")) return null;

            const baseline = baselines[key];
            const low = baseline?.low ?? null;
            const high = baseline?.high ?? null;

            let status = "✅ OK";
            if (low !== null && high !== null) {
              if (value < low || value > high) {
                status = "❌ Violation";
              }
            }

            return (
              <tr key={key} className="border-t">
                <td className="p-2">{key}</td>
                <td className="p-2">{value}</td>
                <td className="p-2">{low}</td>
                <td className="p-2">{high}</td>
                <td className="p-2">{status}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  }

  return null;
}

export default MetricDashboard;
