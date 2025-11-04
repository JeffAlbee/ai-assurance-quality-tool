function ViolationTable({ violations }) {
  if (!violations.length) {
    return <p className="text-sm text-gray-500">No violations found.</p>;
  }

  return (
    <ul className="space-y-4">
      {violations.map((entry, idx) => (
        <li key={idx} className="border-b pb-2">
          <p className="text-sm font-medium text-gray-700">
            <strong>Timestamp:</strong> {entry?.timestamp || "Unknown"}
          </p>
          <ul className="list-disc ml-4 text-sm text-red-600">
            {Array.isArray(entry?.violations) ? (
              entry.violations.map((v, i) => (
                <li key={i}>
                  {v?.metric || "Unknown"}{" "}
                  {v?.type === "min" ? "below" : "above"} threshold:{" "}
                  {v?.value ?? "?"} vs {v?.threshold ?? "?"}
                </li>
              ))
            ) : (
              <li className="text-gray-500">No violation details</li>
            )}
          </ul>
        </li>
      ))}
    </ul>
  );
}

export default ViolationTable;
