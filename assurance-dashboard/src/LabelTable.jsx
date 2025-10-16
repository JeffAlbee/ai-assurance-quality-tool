// src/LabelTable.jsx
import { useEffect, useState } from "react";
import axios from "axios";

export default function LabelTable() {
  const [labels, setLabels] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:8000/v1/labels")  // Add this GET endpoint to your Assurance Service
      .then(res => setLabels(res.data))
      .catch(err => console.error("Failed to fetch labels", err));
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">Assurance Labels</h1>
      <table className="table-auto w-full border">
        <thead>
          <tr>
            <th className="border px-2 py-1">TxID</th>
            <th className="border px-2 py-1">Model</th>
            <th className="border px-2 py-1">Prediction</th>
            <th className="border px-2 py-1">Violations</th>
            <th className="border px-2 py-1">Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {labels.map(label => (
            <tr key={label.txid}>
              <td className="border px-2 py-1">{label.txid}</td>
              <td className="border px-2 py-1">{label.model_version}</td>
              <td className="border px-2 py-1">{label.prediction}</td>
              <td className="border px-2 py-1">{label.violations.join(", ")}</td>
              <td className="border px-2 py-1">{label.timestamp}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
