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

const metricDefinitions = {
  model_reliability_score: {
    formula: "(W1 * (1/Failure Rate) + W2 * (1/P95 Latency) + W3 * (1/Jitter)) / Total Weights",
    relevance: "Measures consistent availability and responsiveness. Primary metric for Infrastructure Teams and SLA compliance.",
  },
  audit_governance_score: {
    formula: "(W4 * Compliance Pass Rate) - (W5 * Domain Violation Rate) - (W6 * Alert Triage Time)",
    relevance: "Tracks data cleanliness and alert resolution speed. Key for Compliance Officers and Orchestration Service (OS) performance.",
  },
  trust_quality_score: {
    formula: "(W7 * Accuracy) - (W8 * Drift (KS Score)) - (W9 * Confidence Variance) / Total Weights",
    relevance: "Evaluates predictive correctness and statistical stability. Penalizes drift and variance.",
  },
  accuracy: {
    formula: "(True Positives + True Negatives) / Total Samples",
    relevance: "Measures core correctness of predictions against ground truth.",
  },
  f1_score: {
    formula: "2 * ( (Precision * Recall) / (Precision + Recall) )",
    relevance: "Balances recall and precision. Essential for imbalanced datasets.",
  },
  rmse: {
    formula: "sqrt( (1/N) * SUM[ (Actual[i] - Predicted[i])^2 ] )",
    relevance: "Quantifies average prediction error. Ensures output stays within tolerances.",
  },
  feature_drift: {
    formula: "max_x |F_live(x) - F_baseline(x)|",
    relevance: "Detects distribution shifts in input features. Flags silent data drift.",
  },
  domain_violation_count: {
    formula: "SUM [ 1 if (Value[i] < Min_Baseline[i] OR Value[i] > Max_Baseline[i]) else 0 ]",
    relevance: "Counts inputs outside known safe ranges. Critical for OT/IoT safety.",
  },
  p95_latency: {
    formula: "95th percentile of latency_ms over time window",
    relevance: "Flags slow responses. SLA-critical for real-time systems.",
  },
  failure_rate: {
    formula: "Number of Failures / Total Inferences",
    relevance: "Tracks service-halting errors. Directly impacts uptime.",
  },
  watts_per_inference: {
    formula: "Average GPU Power / Inferences per Second",
    relevance: "Sustainability metric. Detects energy inefficiency or compute waste.",
  },
  confidence_floor: {
    formula: "Minimum confidence_score over time window (T)",
    relevance: "Establishes safety margin. Ensures model rarely acts below threshold.",
  },
  confidence_variance: {
    formula: "Variance of confidence_score over time window (T)",
    relevance: "Detects instability. High variance signals drift before accuracy drops.",
  },
};

function MetricCard({ name, value, baseline, formula, relevance }) {
  const low = baseline?.low ?? null;
  const high = baseline?.high ?? null;
  const status = low !== null && high !== null && (value < low || value > high)
    ? { label: "❌ Violation", color: "text-red-600" }
    : { label: "✅ OK", color: "text-green-600" };

  return (
    <div className="bg-white border rounded p-4 shadow space-y-2">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">{name}</h3>
        <span className={`font-semibold ${status.color}`}>{status.label}</span>
      </div>
      <p className="text-sm font-mono">Value: {value}</p>
      {low !== null && high !== null && (
        <p className="text-sm text-gray-600">Baseline: {low} – {high}</p>
      )}
      <p className="text-sm italic text-gray-700">Formula: {formula}</p>
      <p className="text-sm text-gray-800">{relevance}</p>
    </div>
  );
}

function MetricDashboard({ section }) {
  const { metrics, baselines } = label;

  const sections = {
    assurance: [
      {
        title: "System-Level Weighted Composite Scores",
        keys: [
          "model_reliability_score",
          "audit_governance_score",
          "trust_quality_score",
        ],
      },
      {
        title: "Model Accuracy & Calibration",
        keys: ["accuracy", "f1_score", "rmse"],
      },
      {
        title: "Data Integrity & Statistical Drift",
        keys: ["feature_drift", "domain_violation_count"],
      },
      {
        title: "Operational Performance & Sustainability",
        keys: ["p95_latency", "failure_rate", "watts_per_inference"],
      },
      {
        title: "Resilience, Audit & Transparency",
        keys: ["confidence_floor", "confidence_variance"],
      },
    ],
  };

  if (section === "assurance") {
    return (
      <div className="space-y-8">
        {sections.assurance.map((group) => (
          <section key={group.title}>
            <h2 className="text-xl font-bold mb-2">{group.title}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {group.keys.map((key) => (
                <MetricCard
                  key={key}
                  name={formatLabel(key)}
                  value={metrics[key]}
                  baseline={baselines[key]}
                  formula={metricDefinitions[key]?.formula}
                  relevance={metricDefinitions[key]?.relevance}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    );
  }

  return null;
}

function formatLabel(key) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export default MetricDashboard;
