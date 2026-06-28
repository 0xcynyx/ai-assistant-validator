import React from "react";

export default function ArtifactPanel({ artifacts = {} }) {
  const entries = Object.entries(artifacts || {});
  if (!entries.length) return null;

  return (
    <section style={{ background: "white", border: "1px solid #d4d1ca", borderRadius: 16, padding: 16 }}>
      <h3 style={{ marginTop: 0 }}>Artifacts</h3>
      <ul style={{ margin: 0, paddingLeft: 18 }}>
        {entries.map(([name, path]) => (
          <li key={name} style={{ marginBottom: 6 }}><strong>{name}</strong>: {path}</li>
        ))}
      </ul>
    </section>
  );
}
