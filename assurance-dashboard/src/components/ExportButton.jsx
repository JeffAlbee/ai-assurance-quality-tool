function ExportButton({ modelId, violations }) {
  const exportCSV = () => {
    const header = "timestamp,metric,type,value,threshold\n";
    const rows = violations.flatMap(entry =>
      entry.violations.map(v =>
        `${entry.timestamp},${v.metric},${v.type},${v.value},${v.threshold}`
      )
    );
    const blob = new Blob([header + rows.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${modelId}-violations.csv`;
    link.click();
  };

  return (
    <button
      onClick={exportCSV}
      className="mb-4 px-3 py-1 bg-purple-600 text-white rounded text-sm"
    >
      Export CSV
    </button>
  );
}

export default ExportButton;
