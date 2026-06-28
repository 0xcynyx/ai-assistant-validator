import React, { useState } from "react";

export default function Uploader({ onUpload, busy }) {
  const [selectedFile, setSelectedFile] = useState(null);

  return (
    <section style={{ background: "white", border: "1px solid #d4d1ca", borderRadius: 16, padding: 16 }}>
      <h2 style={{ marginTop: 0, marginBottom: 8 }}>Upload evaluation cases</h2>
      <p style={{ marginTop: 0, color: "#7a7974" }}>
        Upload a JSON file with a list of cases, or use the default repository dataset.
      </p>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
        <input
          type="file"
          accept="application/json"
          onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
        />
        <button
          onClick={() => onUpload(selectedFile)}
          disabled={busy}
          style={{ padding: "10px 14px", borderRadius: 10, border: "none", background: "#1f6feb", color: "white", cursor: busy ? "wait" : "pointer" }}
        >
          {busy ? "Running…" : "Run evaluation"}
        </button>
      </div>
      {selectedFile && <div style={{ marginTop: 8, color: "#3b3a35" }}>Selected: {selectedFile.name}</div>}
    </section>
  );
}
