import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ViolationDashboard = () => {
  const [modelId, setModelId] = useState('');
  const [violations, setViolations] = useState([]);

  const fetchViolations = async () => {
    try {
      const res = await axios.get(`http://localhost:8000/v1/violations?model_id=${modelId}`);
      setViolations(res.data);
    } catch (err) {
      console.error("Failed to fetch violations", err);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Violation Log</h2>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={modelId}
          onChange={e => setModelId(e.target.value)}
          placeholder="Enter Model ID"
          className="border px-2 py-1 rounded"
        />
        <button onClick={fetchViolations} className="bg-blue-600 text-white px-4 py-1 rounded">
          Fetch
        </button>
      </div>
      <table className="table-auto w-full border">
        <thead>
          <tr className="bg-gray-100">
            <th className="px-2 py-1 border">Metric</th>
            <th className="px-2 py-1 border">Value</th>
            <th className="px-2 py-1 border">Low</th>
            <th className="px-2 py-1 border">High</th>
            <th className="px-2 py-1 border">Type</th>
            <th className="px-2 py-1 border">User</th>
            <th className="px-2 py-1 border">Time</th>
          </tr>
        </thead>
        <tbody>
          {violations.map(v => (
            <tr key={v.id}>
              <td className="px-2 py-1 border">{v.metric}</td>
              <td className="px-2 py-1 border">{v.value}</td>
              <td className="px-2 py-1 border">{v.baseline_low}</td>
              <td className="px-2 py-1 border">{v.baseline_high}</td>
              <td className="px-2 py-1 border">{v.violation_type}</td>
              <td className="px-2 py-1 border">{v.user}</td>
              <td className="px-2 py-1 border">{new Date(v.timestamp).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ViolationDashboard;
