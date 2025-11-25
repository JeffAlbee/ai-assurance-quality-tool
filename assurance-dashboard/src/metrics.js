// src/metrics.jsx

// Utility helpers
const safeDivide = (num, denom) => (denom > 0 ? num / denom : 0);
const variance = (arr) => {
  if (!arr || arr.length === 0) return 0;
  const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
  return arr.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / arr.length;
};

export const metricGroups = [
  {
    title: "Model Accuracy & Calibration",
    description:
      "Metrics requiring ground truth labels to verify predictive correctness of the model.",
    metrics: [
      {
        name: "Accuracy (Classification)",
        formula: "(True Positives + True Negatives) / Total Samples",
        relevance:
          "Measures the core correctness of predictions against ground truth.",
        inputs: ["True Positives", "True Negatives", "Total Samples"],
        compute: ({ "True Positives": tp = 0, "True Negatives": tn = 0, "Total Samples": total = 1 }) =>
          safeDivide(tp + tn, total),
      },
      {
        name: "F1 Score (Classification)",
        formula: "2 * (Precision * Recall) / (Precision + Recall)",
        relevance:
          "Balances recall and precision. Essential for imbalanced datasets.",
        inputs: ["Precision", "Recall"],
        compute: ({ Precision = 0, Recall = 0 }) =>
          Precision + Recall > 0 ? (2 * Precision * Recall) / (Precision + Recall) : 0,
      },
      {
        name: "RMSE (Regression)",
        formula: "sqrt( (1/N) * SUM[ (Actual[i] - Predicted[i])^2 ] )",
        relevance:
          "Quantifies average prediction error for regression models.",
        inputs: ["Actual Values (comma-separated)", "Predicted Values (comma-separated)"],
        compute: ({ "Actual Values (comma-separated)": a = "", "Predicted Values (comma-separated)": p = "" }) => {
          const actual = a.split(",").map(Number);
          const pred = p.split(",").map(Number);
          if (actual.length !== pred.length || actual.length === 0) return 0;
          const mse = actual.reduce((sum, val, i) => sum + Math.pow(val - pred[i], 2), 0) / actual.length;
          return Math.sqrt(mse);
        },
      },
    ],
  },
  {
    title: "Data Integrity & Statistical Drift",
    description:
      "Metrics comparing live production data against baselines to detect anomalies or distribution changes.",
    metrics: [
      {
        name: "Feature Drift (KS Statistic)",
        formula: "max_x |F_live(x) - F_baseline(x)|",
        relevance:
          "Detects distribution shifts in input features.",
        inputs: ["Drift Score"],
        compute: ({ "Drift Score": d = 0 }) => d,
      },
      {
        name: "Feature Domain Violation Count",
        formula: "SUM [ 1 if (Value[i] < Min_Baseline[i] OR Value[i] > Max_Baseline[i]) else 0 ]",
        relevance:
          "Counts inputs outside safe ranges. Critical for OT/IoT safety.",
        inputs: ["Violation Count"],
        compute: ({ "Violation Count": v = 0 }) => v,
      },
    ],
  },
  {
    title: "Operational Performance & Sustainability",
    description:
      "Metrics tracking SLA compliance and resource consumption in production environments.",
    metrics: [
      {
        name: "P95 Latency",
        formula: "95th percentile of latency_ms over time window",
        relevance:
          "Flags slow responses. SLA-critical for real-time systems.",
        inputs: ["Latency Values (comma-separated)"],
        compute: ({ "Latency Values (comma-separated)": vals = "" }) => {
          const arr = vals.split(",").map(Number).sort((a, b) => a - b);
          if (arr.length === 0) return 0;
          const idx = Math.floor(0.95 * arr.length);
          return arr[idx];
        },
      },
      {
        name: "Model Failure Rate",
        formula: "Number of Failures / Total Inferences",
        relevance:
          "Tracks system-halting errors impacting uptime.",
        inputs: ["Failures", "Total Inferences"],
        compute: ({ Failures = 0, "Total Inferences": t = 1 }) => safeDivide(Failures, t),
      },
      {
        name: "Watts Per Inference (WPI)",
        formula: "Average GPU Power / Inferences per Second",
        relevance:
          "Sustainability metric. Detects energy inefficiency.",
        inputs: ["Average GPU Power", "Inferences per Second"],
        compute: ({ "Average GPU Power": g = 0, "Inferences per Second": i = 1 }) => safeDivide(g, i),
      },
    ],
  },
  {
    title: "Resilience, Audit, & Transparency",
    description:
      "Metrics providing auditable proof and stability checks for regulatory compliance.",
    metrics: [
      {
        name: "Immutable Ingestion TXID",
        formula: "SHA256(TIB Message Payload)",
        relevance:
          "Cryptographic guarantee linking raw input to final decision.",
        inputs: ["Message Payload"],
        compute: ({ "Message Payload": payload = "" }) => `sha256(${payload})`, // placeholder
      },
      {
        name: "Decision Confidence Floor",
        formula: "Minimum confidence_score over time window (T)",
        relevance:
          "Establishes safety margin by tracking lowest confidence.",
        inputs: ["Confidence Scores (comma-separated)"],
        compute: ({ "Confidence Scores (comma-separated)": vals = "" }) => {
          const arr = vals.split(",").map(Number).filter((n) => !isNaN(n));
          return arr.length > 0 ? Math.min(...arr) : 0;
        },
      },
      {
        name: "Confidence Variance",
        formula: "Variance of confidence_score values over time window (T)",
        relevance:
          "Sensitive indicator of silent drift. High variance signals instability before accuracy drops.",
        inputs: ["Confidence Scores (comma-separated)"],
        compute: ({ "Confidence Scores (comma-separated)": vals = "" }) => {
          const arr = vals.split(",").map(Number).filter((n) => !isNaN(n));
          return arr.length > 0 ? variance(arr) : 0;
        },
      },
      {
        name: "Top-K Feature Attribution (Snapshot)",
        formula: "Array of {feature_name, score}",
        relevance:
          "Provides rapid Explainability (XAI). Crucial for post-incident analysis to show which features drove the decision.",
        inputs: ["Feature Names (comma-separated)", "Feature Scores (comma-separated)"],
        compute: ({ "Feature Names (comma-separated)": names = "", "Feature Scores (comma-separated)": scores = "" }) => {
          const nArr = names.split(",").map((s) => s.trim());
          const sArr = scores.split(",").map(Number).filter((n) => !isNaN(n));
          return nArr.map((name, i) => ({ feature: name, score: sArr[i] ?? null }));
        },
      },
    ],
  },
];
