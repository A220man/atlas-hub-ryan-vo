import React, { useState, useEffect, useCallback } from "react";
import { PresentationDetail as IPresentationDetail, EvaluationScorecard, NarrationPlan, AdvisoryResponse } from "../types/index.ts";
import { apiClient } from "../api/client.ts";
import { SlideViewer } from "./SlideViewer.tsx";
import { AttributionGuardView } from "./AttributionGuardView.tsx";
import { EvaluationScorecardView } from "./EvaluationScorecardView.tsx";
import { NarrationStudio } from "./NarrationStudio.tsx";

interface PresentationDetailProps {
  presentationId: string;
  onBack: () => void;
}

export const PresentationDetail: React.FC<PresentationDetailProps> = ({ presentationId, onBack }) => {
  const [deck, setDeck] = useState<IPresentationDetail | null>(null);
  const [scorecard, setScorecard] = useState<EvaluationScorecard | null>(null);
  const [narrationPlan, setNarrationPlan] = useState<NarrationPlan | null>(null);
  const [advisory, setAdvisory] = useState<AdvisoryResponse | null>(null);

  const [activeTab, setActiveTab] = useState<"slides" | "attribution" | "evaluation" | "narration" | "advisory">("slides");
  const [loading, setLoading] = useState(true);
  const [evalLoading, setEvalLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [advisoryLoading, setAdvisoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const pres = await apiClient.getPresentation(presentationId);
      setDeck(pres);
      try { setScorecard(await apiClient.getEvaluation(presentationId)); } catch {}
      try { setNarrationPlan(await apiClient.getNarration(presentationId)); } catch {}
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load deck");
    } finally {
      setLoading(false);
    }
  }, [presentationId]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleRunEvaluation = async () => {
    setEvalLoading(true);
    try {
      const sc = await apiClient.runEvaluation(presentationId);
      setScorecard(sc);
      if (deck) setDeck({ ...deck, status: `evaluated-${sc.status}` });
    } catch (err) {
      alert(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setEvalLoading(false);
    }
  };

  const handleExportPptx = async () => {
    if (!deck) return;
    setExporting(true);
    try {
      const blob = await apiClient.exportPptx(deck.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${deck.title.toLowerCase().replace(/\s+/g, "_")}.pptx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExporting(false);
    }
  };

  const handleRequestAdvisory = async () => {
    setAdvisoryLoading(true);
    try {
      setAdvisory(await apiClient.requestAdvisory(presentationId, "executive_review"));
    } catch (err) {
      alert(err instanceof Error ? err.message : "Advisory failed");
    } finally {
      setAdvisoryLoading(false);
    }
  };

  if (loading) return <div className="loading-state"><p>Loading presentation studio...</p></div>;
  if (error || !deck) return <div className="error-banner"><p>{error || "Deck not found"}</p><button className="btn btn-outline btn-sm" onClick={onBack}>Back</button></div>;

  return (
    <div className="presentation-detail-container">
      <div className="detail-banner">
        <div className="banner-left">
          <button className="btn btn-outline btn-sm" onClick={onBack}>&larr; Back to Decks</button>
          <div className="banner-titles">
            <h2>{deck.title}</h2>
            <div className="banner-meta">
              <span>Domain: {deck.topic || "Technical"}</span>
              <span>Template: {deck.template_id}</span>
              <span>Canvas: {deck.aspect_ratio}</span>
              <span className={`badge badge-status badge-${deck.status}`}>{deck.status}</span>
            </div>
          </div>
        </div>
        <div className="banner-right">
          <button className="btn btn-success" onClick={handleExportPptx} disabled={exporting}>
            {exporting ? "Generating..." : "📥 Download PowerPoint (.pptx)"}
          </button>
        </div>
      </div>

      <div className="studio-tabs">
        <button className={`tab-btn ${activeTab === "slides" ? "active" : ""}`} onClick={() => setActiveTab("slides")}>
          🖥️ Slides ({deck.slides.length})
        </button>
        <button className={`tab-btn ${activeTab === "attribution" ? "active" : ""}`} onClick={() => setActiveTab("attribution")}>
          🛡️ Attribution Guard {scorecard ? `(${scorecard.grounding_score}%)` : ""}
        </button>
        <button className={`tab-btn ${activeTab === "evaluation" ? "active" : ""}`} onClick={() => setActiveTab("evaluation")} >
          📈 Scorecard {scorecard ? `(${scorecard.overall_score})` : ""}
        </button>
        <button className={`tab-btn ${activeTab === "narration" ? "active" : ""}`} onClick={() => setActiveTab("narration")}>
          🎙️ Narration {narrationPlan ? `(${narrationPlan.cues.length})` : ""}
        </button>
        <button className={`tab-btn ${activeTab === "advisory" ? "active" : ""}`} onClick={() => setActiveTab("advisory")}>
          💡 AI Advisory
        </button>
      </div>

      <div className="studio-panel">
        {activeTab === "slides" && <SlideViewer slides={deck.slides} templateId={deck.template_id} />}
        {activeTab === "attribution" && <AttributionGuardView scorecard={scorecard} onRunEvaluation={handleRunEvaluation} loading={evalLoading} />}
        {activeTab === "evaluation" && <EvaluationScorecardView scorecard={scorecard} onRunEvaluation={handleRunEvaluation} loading={evalLoading} />}
        {activeTab === "narration" && <NarrationStudio presentationId={deck.id} narrationPlan={narrationPlan} onPlanGenerated={setNarrationPlan} />}
        {activeTab === "advisory" && (
          <div className="advisory-panel">
            <div className="advisory-header-card">
              <h3>Presentation Strategic Advisory</h3>
              <p>Advisory analysis grounded in verified presentation records.</p>
              <button className="btn btn-primary btn-sm" onClick={handleRequestAdvisory} disabled={advisoryLoading}>
                {advisoryLoading ? "Analyzing..." : "Run Advisory Review"}
              </button>
            </div>
            {advisory && (
              <div className="advisory-result-card" style={{ marginTop: "1rem" }}>
                <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
                  <span className="badge badge-template">Provider: {advisory.provider}</span>
                  <span className="badge badge-status">Model: {advisory.model}</span>
                </div>
                <pre style={{ background: "#f8fafc", padding: "1rem", borderRadius: "6px", whiteSpace: "pre-wrap" }}>{advisory.advice}</pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
