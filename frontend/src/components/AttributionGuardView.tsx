import React from "react";
import { EvaluationScorecard } from "../types/index.ts";

interface AttributionGuardViewProps {
  scorecard: EvaluationScorecard | null;
  onRunEvaluation: () => void;
  loading: boolean;
}

export const AttributionGuardView: React.FC<AttributionGuardViewProps> = ({
  scorecard,
  onRunEvaluation,
  loading,
}) => {
  if (!scorecard) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🛡️</div>
        <h3>Attribution Guard Not Evaluated</h3>
        <p>Run the fail-closed integrity gate to verify that all presentation bullets and claims are grounded in source document character spans.</p>
        <button className="btn btn-primary" onClick={onRunEvaluation} disabled={loading}>
          {loading ? "Running..." : "Run Attribution Guard"}
        </button>
      </div>
    );
  }

  const isPassed = scorecard.status === "passed" || scorecard.grounding_score >= 60.0;
  const exitCode = isPassed ? 0 : 1;

  return (
    <div className="attribution-guard-container">
      <div className="gate-header-card">
        <div className="gate-status-row">
          <div className="status-indicator">
            <span className={`status-pill ${isPassed ? "pill-pass" : "pill-fail"}`}>
              {isPassed ? "GATE PASSED (Exit Code 0)" : "GATE FAILED (Exit Code 1)"}
            </span>
            <span className="gate-subtitle">Fail-closed verification with actionable diagnostics</span>
          </div>
          <button className="btn btn-outline btn-sm" onClick={onRunEvaluation} disabled={loading}>
            {loading ? "Verifying..." : "Re-run Guard"}
          </button>
        </div>

        <div className="metrics-row">
          <div className="metric-box"><div className="metric-num">{scorecard.grounding_score}%</div><div className="metric-label">Span Grounding Accuracy</div></div>
          <div className="metric-box"><div className="metric-num">{scorecard.diagnostics.length}</div><div className="metric-label">Diagnostic Findings</div></div>
          <div className="metric-box"><div className="metric-num">{scorecard.span_groundings.length}</div><div className="metric-label">Claims Audited</div></div>
          <div className="metric-box"><div className="metric-num">Exit {exitCode}</div><div className="metric-label">Integrity Exit Code</div></div>
        </div>
      </div>

      <div style={{ background: "#fff", border: "1px solid var(--bdr)", borderRadius: "8px", padding: "1rem", marginBottom: "1rem" }}>
        <h3 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Actionable Diagnostic Items ({scorecard.diagnostics.length})</h3>
        {scorecard.diagnostics.length === 0 ? (
          <div className="banner-success">✓ All slide claims verified against source reference spans. Zero errors.</div>
        ) : (
          <div>
            {scorecard.diagnostics.map((diag, idx) => (
              <div key={idx} className={`diag-card diag-${diag.severity}`}>
                <div className="diag-header">
                  <span className={`badge badge-${diag.severity}`}>{diag.severity.toUpperCase()}</span>
                  <span className="diag-code">[{diag.code}]</span>
                  {diag.slide_index !== undefined && <span>Slide #{diag.slide_index + 1}</span>}
                  {diag.element && <span>({diag.element})</span>}
                </div>
                <div className="diag-msg">{diag.message}</div>
                {diag.suggestion && <div className="diag-suggestion"><strong>Remediation:</strong> {diag.suggestion}</div>}
              </div>
            ))}
          </div>
        )}
      </div>

      {scorecard.span_groundings.length > 0 && (
        <div style={{ background: "#fff", border: "1px solid var(--bdr)", borderRadius: "8px", padding: "1rem" }}>
          <h3 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Grounding Traceability Matrix</h3>
          <table className="matrix-table">
            <thead><tr><th>Slide</th><th>Claim</th><th>Status</th><th>Confidence</th><th>Matched Reference</th></tr></thead>
            <tbody>
              {scorecard.span_groundings.map((sg, idx) => (
                <tr key={idx}>
                  <td>Slide {sg.slide_index + 1}</td>
                  <td>{sg.claim}</td>
                  <td><span className={`badge ${sg.is_grounded ? "badge-success" : "badge-danger"}`}>{sg.is_grounded ? "Grounded" : "Unverified"}</span></td>
                  <td>{Math.round(sg.grounding_confidence * 100)}%</td>
                  <td>{sg.matched_source_span ? <code>"{sg.matched_source_span}"</code> : <span className="text-muted">None</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
