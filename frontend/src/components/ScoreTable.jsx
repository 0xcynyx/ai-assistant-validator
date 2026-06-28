import React from "react";

export default function ScoreTable({ scores = [] }) {
  if (!scores.length) return null;

  return (
    <section style={{ background: "white", border: "1px solid #d4d1ca", borderRadius: 16, padding: 16 }}>
      <h3 style={{ marginTop: 0 }}>Final scores</h3>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #ece8e0" }}>
            <th style={{ padding: 8 }}>Case</th>
            <th style={{ padding: 8 }}>Score</th>
            <th style={{ padding: 8 }}>Status</th>
          </tr>
        </thead>
        <tbody>
          {scores.map((score) => (
            <tr key={score.case_id} style={{ borderBottom: "1px solid #f3efe8" }}>
              <td style={{ padding: 8 }}>{score.case_id}</td>
              <td style={{ padding: 8 }}>{score.score}</td>
              <td style={{ padding: 8 }}>{score.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
