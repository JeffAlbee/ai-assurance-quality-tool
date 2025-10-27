import { useState, useEffect } from "react";
import axios from "axios";

function ModelConfigForm() {
  const [activeModels, setActiveModels] = useState([]);
  const [modelName, setModelName] = useState("");
  const [endpoint, setEndpoint] = useState("http://localhost:5000");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios
      .get("/v1/models/active")
      .then((res) => setActiveModels(res.data.models || []))
      .catch(() => setActiveModels([]));
  }, []);

  const testConnection = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${endpoint}/health`);
      if (res.data.status === "ok") {
        setStatus("✅ Connection successful");
      } else {
        setStatus("⚠️ Unexpected response");
      }
    } catch (err) {
      setStatus("❌ Connection failed");
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    try {
      await axios.post("/v1/model/config", {
        model_name: modelName,
        endpoint_url: endpoint,
      });
      setStatus("✅ Configuration saved");
    } catch {
      setStatus("❌ Failed to save configuration");
    }
  };

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold mb-2">Active Models</h2>
        {activeModels.length > 0 ? (
          <ul className="list-disc pl-5 text-sm">
            {activeModels.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-gray-600">No active models found.</p>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">Connect to Model</h2>
        <div className="space-y-2">
          <label className="block text-sm font-medium">Model Name</label>
          <input
            type="text"
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
            list="model-options"
            className="border rounded px-2 py-1 w-full"
            placeholder="Enter or select model name"
          />
          <datalist id="model-options">
            {activeModels.map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>

          <label className="block text-sm font-medium mt-4"> Endpoint URL</label>
          <input
            type="text"
            value={endpoint}
            onChange={(e) => setEndpoint(e.target.value)}
            className="border rounded px-2 py-1 w-full"
            placeholder="http://localhost:5000"
          />

          <div className="flex gap-4 mt-4">
            <button
              onClick={testConnection}
              className="bg-blue-600 text-white px-4 py-1 rounded"
              disabled={loading}
            >
              {loading ? "Testing..." : "Test Connection"}
            </button>
            <button
              onClick={saveConfig}
              className="bg-green-600 text-white px-4 py-1 rounded"
            >
              Save Configuration
            </button>
          </div>

          {status && <p className="text-sm mt-2">{status}</p>}
        </div>
      </section>
    </div>
  );
}

export default ModelConfigForm;
