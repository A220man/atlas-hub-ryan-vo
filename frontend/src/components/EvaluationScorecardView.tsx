import React from "react";
import { EvaluationScorecard } from "../types/index.ts";

interface EvaluationScorecardViewProps {
  scorecard: EvaluationScorecard | null;
  onRunEvaluation: () => void;
  loading: boolean;
}

export const EvaluationScorecardView: React.FC<EvaluationScorecardViewProps> = ({
  scorecard,
  onRunEvaluation,
  loading,
}) => {
  if (!scorecard) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📈</div>
        <h3>No Quality Scorecard Available</h3>
        <p>Run the 4-pillar evaluation to measure grounding, balance, pacing, and terminology consistency.</p>
        <button
          className="btn btn-primary"
          onClick={onRunEvaluation}
          disabled={loading}
        >
          {loading ? "Evaluating..." : "Run Quality Evaluation"}
        </button>
      </div>
    );
  }

  return (
    <div className="scorecard-container">
      {/* Overall Score Banner */}
      <div className="score-summary-banner">
        <div className="score-circle">
          <span className="score-big">{scorecard.overall_score}</span>
          <span className="score-out-of">/ 100</span>
        </div>
        <div className="score-details">
          <h2>Presentation Quality Scorecard</h2>
          <p className="score-summary-text">{scorecard.summary}</p>
          <div className="score-status-row">
            <span className={`badge ${scorecard.status === "passed" ? "badge-success" : "badge-warning"}`}>
              STATUS: {scorecard.status.toUpperCase()}
            </span>
            <button
              className="btn btn-outline btn-sm"
              onClick={onRunEvaluation}
              disabled={loading}
            >
              {loading ? "Re-evaluating..." : "Re-run Evaluation"}
            </button>
          </div>
        </div>
      </div>

      {/* 4 Pillars Grid */}
      <div className="pillars-grid">
        <div className="pillar-card">
          <div className="pillar-header">
            <h4>Span Grounding</h4>
            <span className="pillar-weight">40% weight</span>
          </div>
          <div className="pillar-score">{scorecard.grounding_score}%</div>
          <p className="pillar-desc">Verifies factual containment against indexed source document spans.</p>
          <div className="pillar-meter">
            <div className="meter-fill" style={{ width: `${scorecard.grounding_score}%` }}></div>
          </div>
        </div>

        <div className="pillar-card">
          <div className="pillar-header">
            <h4>Cognitive Balance</h4>
            <span className="pillar-weight">25% weight</span>
          </div>
          <div className="pillar-score">{scorecard.balance_score}%</div>
          <p className="pillar-desc">Audits textual density, word count per slide, and visual weight distribution.</p>
          <div className="pillar-meter">
            <div className="meter-fill" style={{ width: `${scorecard.balance_score}%` }}></div>
          </div>
        </div>

        <div className="pillar-card">
          <div className="pillar-header">
            <h4>Narrative Pacing</h4>
            <span className="pillar-weight">20% weight</span>
          </div>
          <div className="pillar-score">{scorecard.pacing_score}%</div>
          <p className="pillar-desc">Measures information velocity and density variance across sequential slides.</p>
          <div className="pillar-meter">
            <div className="meter-fill" style={{ width: `${scorecard.pacing_score}%` }}></div>
          </div>
        </div>

        <div className="pillar-card">
          <div className="pillar-header">
            <h4>Terminology Audit</h4>
            <span className="pillar-weight">15% weight</span>
          </div>
          <div className="pillar-score">{scorecard.consistency_score}%</div>
          <p className="pillar-desc">Checks heading capitalization consistency and cross-lingual translation drift.</p>
          <div className="pillar-meter">
            <div className="meter-fill" style={{ width: `${scorecard.consistency_score}%` }}></div>
          </div>
        </div>
      </div>

      {/* Findings Breakdown */}
      <div className="findings-section">
        <h3>Evaluation Findings ({scorecard.diagnostics.length})</h3>
        {scorecard.diagnostics.length === 0 ? (
          <div className="banner banner-success">
            All 4 quality dimensions scored within optimal thresholds.
          </div>
        ) : (
          <div className="findings-list">
            {scorecard.diagnostics.map((diag, i) => (
              <div key={i} className={`finding-row severity-${diag.severity}`}>
                <span className={`badge badge-${diag.severity}`}>{diag.severity}</span>
                <span className="finding-msg">{diag.message}</span>
                {diag.suggestion && (
                  <span className="finding-sugg">👉 {diag.suggestion}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
