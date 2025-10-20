import { useState, useEffect } from "react";
import axios from "axios";
import MetricDashboard from "./MetricDashboard";
import ViolationDashboard from "./ViolationDashboard";

function App() {
  const [activeTab, setActiveTab] = useState("metrics");
  const [licenseInfo, setLicenseInfo] = useState(null);

  useEffect(() => {
    axios
      .get("http://localhost:8000/v1/license/status")
      .then((res) => setLicenseInfo(res.data))
      .catch(() =>
        setLicenseInfo({
          status: "inactive",
          level: "basic",
          txid: "N/A",
          checked_at: null,
          expires_at: null,
        })
      );
  }, []);

  const LicenseBanner = () => {
    if (!licenseInfo) return null;

    const isActive = licenseInfo.status === "active";
    const bannerColor = isActive
      ? "bg-green-100 border-green-500"
      : "bg-red-100 border-red-500";
    const icon = isActive ? "✅" : "❌";
    const level = licenseInfo.level || "basic";

    let countdownText = "Expiration date not available";
    if (licenseInfo.expires_at) {
      const now = new Date();
      const expires = new Date(licenseInfo.expires_at);
      const diffDays = Math.ceil((expires - now) / (1000 * 60 * 60 * 24));
      countdownText =
        diffDays > 0
          ? `${diffDays} day${diffDays !== 1 ? "s" : ""} remaining`
          : "Expired";
    }

    return (
      <div className={`px-4 py-2 mb-4 border-l-4 ${bannerColor} text-sm`}>
        <p className="text-lg font-semibold">
          <strong>License Level:</strong> {level}
        </p>
        <p className="text-lg font-semibold">
          {icon} <strong>License Status:</strong> {licenseInfo.status}
        </p>
        <p>
          <strong>TXID:</strong> {licenseInfo.txid}
        </p>
        <p>
          <strong>Checked At:</strong>{" "}
          {licenseInfo.checked_at
            ? new Date(licenseInfo.checked_at).toLocaleString()
            : "N/A"}
        </p>
        <p>
          <strong>Expires In:</strong>{" "}
          <span className={countdownText === "Expired" ? "text-red-600" : ""}>
            {countdownText}
          </span>
        </p>
        <p className="mt-2 italic text-gray-700">
          Basic license is free. Premium unlocks full assurance features.
        </p>
      </div>
    );
  };

  const LicenseTab = () => {
    const level = licenseInfo?.level || "basic";

    return (
      <main className="px-4 py-6 space-y-4">
        <LicenseBanner />
        <section>
          <h2 className="text-xl font-semibold mb-2">License Details</h2>
          <p className="text-sm">
            <strong>Current Level:</strong> {level}
          </p>
          <p className="text-sm">
            <strong>Upgrade Info:</strong>{" "}
            {level === "premium"
              ? "You are on a premium license. Thank you!"
              : "Upgrade to premium to unlock full assurance features."}
          </p>
        </section>

        {level === "basic" && (
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
  };

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
        <section className="mt-4">
          <LicenseBanner />
        </section>
        <nav className="flex gap-4 mt-2">
          <button
            onClick={() => setActiveTab("metrics")}
            className={`text-white px-3 py-1 rounded ${
              activeTab === "metrics" ? "bg-blue-700" : "bg-blue-500"
            }`}
          >
            Metrics
          </button>
          <button
            onClick={() => setActiveTab("violations")}
            className={`text-white px-3 py-1 rounded ${
              activeTab === "violations" ? "bg-blue-700" : "bg-blue-500"
            }`}
          >
            Violations
          </button>
          <button
            onClick={() => setActiveTab("license")}
            className={`text-white px-3 py-1 rounded ${
              activeTab === "license" ? "bg-blue-700" : "bg-blue-500"
            }`}
          >
            License
          </button>
        </nav>
      </header>

      {activeTab === "metrics" && (
        <main className="px-4 py-6 space-y-6">
          <section>
            <h2 className="text-xl font-semibold">Latest Assurance Label</h2>
            <div className="space-y-1 text-sm">
              <p>
                <strong>TxID:</strong> demo-001
              </p>
              <p>
                <strong>Model:</strong> BridgeTypeModel-v1
              </p>
              <p>
                <strong>Prediction:</strong> safe
              </p>
              <p>
                <strong>Timestamp:</strong> 2025-10-15T21:12:34Z
              </p>
            </div>
          </section>
          <section>
            <h2 className="text-xl font-semibold mb-4">Composite Scores</h2>
            <MetricDashboard section="scores" />
          </section>
          <section>
            <h2 className="text-xl font-semibold mb-4">Metric Breakdown</h2>
            <MetricDashboard section="metrics" />
          </section>
        </main>
      )}

      {activeTab === "violations" && (
        <main className="px-4 py-6">
          <ViolationDashboard />
        </main>
      )}

      {activeTab === "license" && <LicenseTab />}
    </div>
  );
}

export default App;
