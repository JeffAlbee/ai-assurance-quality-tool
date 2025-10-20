import { useState } from "react";
import MetricDashboard from "./MetricDashboard";
import ViolationDashboard from "./ViolationDashboard";

function App() {
  const [activeTab, setActiveTab] = useState("metrics");

  return (
    <div className="min-h-screen bg-[#F5F5F5] text-gray-900">
      <header className="flex justify-between items-center px-4 py-3 bg-[#003865] shadow">
        <div className="flex items-center w-40 h-10 overflow-hidden">
          <img
            src="/AIA_BB_Logo_horiz_FIN.png"
            alt="AI Assurance Logo"
            style={{ height: "112px", width: "auto", maxWidth: "560px" }}
          />
        </div>
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab("metrics")}
            className={`text-white px-3 py-1 rounded ${activeTab === "metrics" ? "bg-blue-700" : "bg-blue-500"}`}
          >
            Metrics
          </button>
          <button
            onClick={() => setActiveTab("violations")}
            className={`text-white px-3 py-1 rounded ${activeTab === "violations" ? "bg-blue-700" : "bg-blue-500"}`}
          >
            Violations
          </button>
        </nav>
      </header>

      {activeTab === "metrics" && (
        <>
          <section className="px-4 py-6 space-y-2">
            <h2 className="text-xl font-semibold">Latest Assurance Label</h2>
            <div className="space-y-1 text-sm">
              <p><strong>TxID:</strong> demo-001</p>
              <p><strong>Model:</strong> BridgeTypeModel-v1</p>
              <p><strong>Prediction:</strong> safe</p>
              <p><strong>Timestamp:</strong> 2025-10-15T21:12:34Z</p>
            </div>
          </section>

          <main className="px-4 pb-8 grid grid-cols-1 md:grid-cols-2 gap-8">
            <section>
              <h2 className="text-xl font-semibold mb-4">Composite Scores</h2>
              <MetricDashboard section="scores" />
            </section>
            <section>
              <h2 className="text-xl font-semibold mb-4">Metric Breakdown</h2>
              <MetricDashboard section="metrics" />
            </section>
          </main>
        </>
      )}

      {activeTab === "violations" && (
        <main className="px-4 py-6">
          <ViolationDashboard />
        </main>
      )}
    </div>
  );
}

export default App;
