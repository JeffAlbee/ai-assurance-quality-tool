// src/SystemMetrics.jsx
import React from "react";

// Utility helper
const safeDivide = (num, denom) => (denom > 0 ? num / denom : 0);

export const systemMetrics = [
  {
    name: "Model Reliability Score",
    formula: "(W1 * (1/Failure Rate) + W2 * (1/P95 Latency) + W3 * (1/Jitter)) / Total Weights",
    relevance:
      "Operational Health at a Glance: Measures consistent availability and responsiveness. Primary metric for Infrastructure Teams and SLA compliance.",
    inputs: ["Failure Rate", "P95 Latency", "Jitter", "W1", "W2", "W3", "Total Weights"],
    compute: ({ "Failure Rate": f = 0.01, "P95 Latency": l = 1, Jitter = 1, W1 = 1, W2 = 1, W3 = 1, "Total Weights": tw = 3 }) =>
      tw > 0 ? (W1 * (1 / f) + W2 * (1 / l) + W3 * (1 / Jitter)) / tw : 0,
  },
  {
    name: "Audit & Governance Score",
    formula: "(W4 * Compliance Pass Rate) - (W5 * Domain Violation Rate) - (W6 * Alert Triage Time)",
    relevance:
      "Regulatory Compliance: Measures organizational response and data cleanliness. Key for Compliance Officers and OS performance.",
    inputs: ["Compliance Pass Rate", "Domain Violation Rate", "Alert Triage Time", "W4", "W5", "W6"],
    compute: ({ "Compliance Pass Rate": c = 1, "Domain Violation Rate": d = 0, "Alert Triage Time": t = 0, W4 = 1, W5 = 1, W6 = 1 }) =>
      W4 * c - W5 * d - W6 * t,
  },
  {
    name: "Trust & Quality Score",
    formula: "(W7 * Accuracy) - (W8 * Drift (KS Score)) - (W9 * Confidence Variance) / Total Weights",
    relevance:
      "Model Intelligence Health: Measures predictive correctness and stability. Penalizes drift and variance.",
    inputs: ["Accuracy", "Drift (KS Score)", "Confidence Variance", "W7", "W8", "W9", "Total Weights"],
    compute: ({ Accuracy = 0.9, "Drift (KS Score)": d = 0.05, "Confidence Variance": v = 0.01, W7 = 1, W8 = 1, W9 = 1, "Total Weights": tw = 3 }) =>
      tw > 0 ? (W7 * Accuracy - W8 * d - W9 * v) / tw : 0,
  },
  {
    name: "Remote Labor Index (RLI)",
    formula: "Successful Outcomes / Total Projects Attempted by AI",
    relevance:
      "Economic performance: Measures AI agent’s ability to complete projects autonomously with verified quality.",
    inputs: ["Successful Outcomes", "Total Projects Attempted"],
    compute: ({ "Successful Outcomes": s = 0, "Total Projects Attempted": t = 1 }) => safeDivide(s, t),
  },
];
