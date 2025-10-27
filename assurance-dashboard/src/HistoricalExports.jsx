import { useEffect, useState } from "react";

function HistoricalExports({ modelId }) {
  const [files, setFiles] = useState([]);

  useEffect(() => {
    fetch(`/v1/exports?model_id=${modelId}`)
      .then(res => res.json())
      .then(data => setFiles(data.files || []));
  }, [modelId]);

  const downloadFile = (filename) => {
    fetch(`/v1/exports/download?model_id=${modelId}&filename=${filename}`)
      .then(res => res.blob())
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
      });
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Historical Exports</h2>
      {files.length === 0 ? (
        <p>No historical files found.</p>
      ) : (
        <table className="table-auto w-full">
          <thead>
            <tr>
              <th className="text-left">Filename</th>
              <th className="text-left">Download</th>
            </tr>
          </thead>
          <tbody>
            {files.map(file => (
              <tr key={file}>
                <td>{file}</td>
                <td>
                  <button
                    className="bg-blue-500 text-white px-3 py-1 rounded"
                    onClick={() => downloadFile(file)}
                  >
                    Download
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default HistoricalExports;
