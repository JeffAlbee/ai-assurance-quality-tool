function ViolationSummary({ violations }) {
  if (!violations.length) return null;
  const latest = violations[0]?.timestamp || "—";

  return (
    <div className="mb-4 text-sm text-gray-700">
      <p><strong>Total Entries:</strong> {violations.length}</p>
      <p><strong>Latest Timestamp:</strong> {latest}</p>
    </div>
  );
}

export default ViolationSummary;
