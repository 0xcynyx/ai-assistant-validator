import React from "react";

export default function ReportViewer({ report = "" }) {
  if (!report) return null;

  return (
    <section style={{ background: "white", border: "1px solid #d4d1ca", borderRadius: 16, padding: 16 }}>
      <h3 style={{ marginTop: 0 }}>Markdown report</h3>
      <pre style={{ whiteSpace: "pre-wrap", background: "#f8f6f0", padding: 12, borderRadius: 10, overflowX: "auto" }}>{report}</pre>
    </section>
  );
}
