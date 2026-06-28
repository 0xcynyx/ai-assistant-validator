import React, { useMemo, useState } from "react";
import Uploader from "./components/Uploader";
import StageTracker from "./components/StageTracker";
import ScoreTable from "./components/ScoreTable";
import ArtifactPanel from "./components/ArtifactPanel";
import ReportViewer from "./components/ReportViewer";
import { evaluateCases, fetchReport } from "./api/client";

const stages = [
  "INIT",
  "CASES_LOADED",
  "RULE_CHECKS_COMPLETE",
  "LLM_EVAL_COMPLETE",
  "SCORES_AGGREGATED",
  "REPORT_GENERATED",
  "VALIDATION_COMPLETE",
  "RESULTS_FINALISED",
];

export default function App() {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [report, setReport] = useState("");
  const [error, setError] = useState("");

  const currentStage = useMemo(() => result?.stage || "INIT", [result]);

  const handleUpload = async (file) => {
    setBusy(true);
    setError("");
    try {
      const evalResult = await evaluateCases(file);
      setResult(evalResult);
      const reportMd = await fetchReport();
      setReport(reportMd);
    } catch (e) {
      setError(e?.message || "Unknown error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main style={{ maxWidth: 1200, margin: "0 auto", padding: 24 }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 32 }}>AI Assistant Evaluation MVP</h1>
        <p style={{ color: "#7a7974", marginTop: 8 }}>
          Review policy and quality scores from the backend pipeline with a lightweight local UI.
        </p>
      </header>

      <Uploader onUpload={handleUpload} busy={busy} />
      <StageTracker currentStage={currentStage} stages={stages} />

      {error && (
        <div style={{ marginTop: 16, background: "#fdf0f6", color: "#a12c7b", padding: 16, borderRadius: 12 }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 24, display: "grid", gap: 16 }}>
          <div style={{ background: "white", border: "1px solid #d4d1ca", borderRadius: 16, padding: 16 }}>
            <div><strong>Run ID:</strong> {result.run_id}</div>
            <div><strong>Stage:</strong> {result.stage}</div>
            <div><strong>Mock mode:</strong> {String(result.mock_mode)}</div>
            <div><strong>Validation passed:</strong> {String(result.passed)}</div>
          </div>
          <ScoreTable scores={result.final_scores || []} />
          <ReportViewer report={report} />
          <ArtifactPanel artifacts={result.artifacts || {}} />
        </div>
      )}
    </main>
  );
}
import React, { useMemo, useState } from "react";
import Uploader from "./components/Uploader";
import StageTracker from "./components/StageTracker";
import ScoreTable from "./components/ScoreTable";
import ArtifactPanel from "./components/ArtifactPanel";
import ReportViewer from "./components/ReportViewer";
import { evaluateCases, fetchReport } from "./api/client";

const stages = [
  "INIT",
  "CASES_LOADED",
  "RULE_CHECKS_COMPLETE",
  "LLM_EVAL_COMPLETE",
  "SCORES_AGGREGATED",
  "REPORT_GENERATED",
  "VALIDATION_COMPLETE",
  "RESULTS_FINALISED",
];

export default function App() {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [report, setReport] = useState("");
  const [error, setError] = useState("");

  const currentStage = useMemo(() => result?.stage || "INIT", [result]);

  const handleUpload = async (file) => {
    setBusy(true);
    setError("");
    try {
      const evalResult = await evaluateCases(file);
      setResult(evalResult);
      const reportMd = await fetchReport();
      setReport(reportMd);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Unknown error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main style={{ maxWidth: 1200, margin: "0 auto", padding: 24 }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 32 }}>AI Assistant Evaluation MVP</h1>
        <p style={{ color: "#7a7974", marginTop: 8 }}>
          Backend = FastAPI + LangGraph + RAG + OpenRouter. Frontend = React local reviewer UI.
        </p>
      </header>

      <Uploader onUpload={handleUpload} busy={busy} />
      <StageTracker currentStage={currentStage} stages={stages} />

      {error && (
        <div style={{ marginTop: 16, background: "#fdf0f6", color: "#a12c7b", padding: 16, borderRadius: 12 }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 24, display: "grid", gap: 16 }}>
          <div style={{ background: "white", border: "1px solid #d4d1ca", borderRadius: 16, padding: 16 }}>
            <div><strong>Run ID:</strong> {result.run_id}</div>
            <div><strong>Stage:</strong> {result.stage}</div>
            <div><strong>Mock mode:</strong> {String(result.mock_mode)}</div>
            <div><strong>Validation passed:</strong> {String(result.passed)}</div>
          </div>
          <ScoreTable scores={result.final_scores} />
          <ReportViewer report={report} />
          <ArtifactPanel />
        </div>
      )}
    </main>
  );
}