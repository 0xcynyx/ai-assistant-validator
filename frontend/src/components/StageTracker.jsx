import React from "react";

export default function StageTracker({ currentStage, stages }) {
  return (
    <section style={{ marginTop: 16, background: "white", border: "1px solid #d4d1ca", borderRadius: 16, padding: 16 }}>
      <h3 style={{ marginTop: 0 }}>Pipeline stages</h3>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {stages.map((stage) => {
          const active = stage === currentStage;
          const done = stages.indexOf(stage) < stages.indexOf(currentStage);
          return (
            <span
              key={stage}
              style={{ padding: "8px 10px", borderRadius: 999, background: active ? "#1f6feb" : done ? "#dff4e8" : "#f1efe8", color: active ? "white" : "#2f2c28", fontSize: 13 }}
            >
              {stage}
            </span>
          );
        })}
      </div>
    </section>
  );
}
