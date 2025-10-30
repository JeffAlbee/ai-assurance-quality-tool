import { useState, useEffect } from "react";
import axios from "axios";
import MetricDashboard from "./MetricDashboard";
import ModelConfigForm from "./ModelConfigForm";
import BaselineTolerances from "./BaselineTolerances";
import Historian from "./Historian"; // ✅ Unified tab

function App() {
  const [activeTab, setActiveTab] = useState("grafanaMetrics");
  const [licenseInfo, setLicenseInfo] = useState(null);

  useEffect(() => {
    axios
      .get("http://localhost:8000/v1/license/status")
      .then((res) => setLicenseInfo(res.data))
      .catch(() => {
        console.warn("License status fetch failed");
        setLicenseInfo({ status: "inactive", level: "basic" });
      });
  }, []);

  const LicenseHeader = () => {
    if (!licenseInfo) return null;
    const { level = "basic", status } = licenseInfo;
    const isActive = status === "active";
    const statusStyle = isActive ? "text-green-600 font-bold" : "text-red-600 font-bold";
    const statusText = isActive ? "Active" : "Expired";

    return (
      <div className="mb-4 text-sm">
        <p className="text-lg font-semibold">
          <strong>License Level:</strong> {level}
        </p>
        <p className={`text-lg font-semibold ${statusStyle}`}>
          <strong>License Status:</strong> {statusText}
        </p>
      </div>
    );
  };

  const TabContent = () => {
    switch (activeTab) {
      case "grafanaMetrics":
        return (
          <main className="px-4 py-6">
            <LicenseHeader />
            <h2 className="text-xl font-semibold mb-4">Real-Time Metrics</h2>
            <div className="rounded border bg-white p-4 shadow">
              <iframe
                src="http://localhost:3000/goto/cf2c91agdo2kgf?orgId=1"
                width="100%"
                height="750"
                frameBorder="0"
                title="Grafana Assurance Metrics"
              />
            </div>
          </main>
        );
      case "metrics":
        return (
          <main className="px-4 py-6 space-y-6">
            <LicenseHeader />
            <section>
              <h2 className="text-xl font-semibold">Latest Assurance Label</h2>
              <div className="space-y-1 text-sm">
                <p><strong>TxID:</strong> demo-001</p>
                <p><strong>Model:</strong> BridgeTypeModel-v1</p>
                <p><strong>Prediction:</strong> safe</p>
                <p><strong>Timestamp:</strong> 2025-10-15T21:12:34Z</p>
              </div>
            </section>
            <section>
              <h2 className="text-xl font-semibold mb-4">Assurance Metrics Snapshot</h2>
              <MetricDashboard section="assurance" />
            </section>
          </main>
        );
      case "historian":
        return (
          <main className="px-4 py-6">
            <LicenseHeader />
            <h2 className="text-xl font-semibold mb-4">Historian Logs</h2>
            <div className="bg-white p-4 rounded shadow">
              {/* Defensive rendering */}
              {Historian ? <Historian /> : <p className="text-sm text-red-600">Historian component failed to load.</p>}
            </div>
          </main>
        );
      case "baseline":
        return (
          <main className="px-4 py-6">
            <LicenseHeader />
            <BaselineTolerances />
          </main>
        );
      case "config":
        return (
          <main className="px-4 py-6">
            <LicenseHeader />
            <h2 className="text-xl font-semibold mb-4">Model Configuration</h2>
            <ModelConfigForm />
          </main>
        );
      case "license":
        return (
          <main className="px-4 py-6 space-y-4">
            <LicenseHeader />
            <section>
              <h2 className="text-xl font-semibold mb-2">License Details</h2>
              <p className="text-sm"><strong>Current Level:</strong> {licenseInfo?.level || "basic"}</p>
              <p className="text-sm">
                <strong>Upgrade Info:</strong>{" "}
                {licenseInfo?.level === "premium"
                  ? "You are on a premium license. Thank you!"
                  : "Upgrade to premium to unlock full assurance features."}
              </p>
            </section>
            {licenseInfo?.level === "basic" && (
              <section>
                <h2 className="text-xl font-semibold mb-2">Upgrade to Premium</h2>
                <p className="text-sm mb-2">
                  Scan the QR code below to upgrade your license via Bitcoin.
                </p>
                <img
                  src="/bitcoin_qr.png"
                  alt="Pay via Bitcoin QR"
                  className="h-32 w-auto border rounded"
                />
              </section>
            )}
          </main>
        );
      default:
        return <main className="px-4 py-6">Invalid tab selected.</main>;
    }
  };

  const tabs = [
    { key: "grafanaMetrics", label: "Real-Time Metrics" },
    { key: "metrics", label: "Assurance Label" },
    { key: "historian", label: "Historian" },
    { key: "baseline", label: "Baseline & Tolerances" },
    { key: "config", label: "Model Configuration" },
    { key: "license", label: "License" },
  ];

  return (
    <div className="min-h-screen bg-[#F5F5F5] text-gray-900">
      <header className="px-4 py-3 bg-[#003865] shadow">
        <div className="flex items-center justify-between">
          <div className="w-40 h-10 overflow-hidden">
            <img
              src="/AIA_BB_Logo_horiz_FIN.png"
              alt="AI Assurance Logo"
              style={{ height: "112px", width: "auto", maxWidth: "560px" }}
            />
          </div>
        </div>
        <nav className="flex gap-4 mt-4 flex-wrap">
          {tabs.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-3 py-1 rounded ${
                activeTab === key ? "bg-purple-700 text-white" : "bg-purple-500 text-white"
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>
      {TabContent()}
    </div>
  );
}

export default App;
