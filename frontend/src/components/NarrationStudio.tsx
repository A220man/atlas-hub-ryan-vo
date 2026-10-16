import React, { useState } from "react";
import { NarrationPlan } from "../types/index.ts";
import { apiClient } from "../api/client.ts";

interface NarrationStudioProps {
  presentationId: string;
  narrationPlan: NarrationPlan | null;
  onPlanGenerated: (plan: NarrationPlan) => void;
}

export const NarrationStudio: React.FC<NarrationStudioProps> = ({
  presentationId,
  narrationPlan,
  onPlanGenerated,
}) => {
  const [voiceId, setVoiceId] = useState("neutral-presenter");
  const [wpm, setWpm] = useState(140);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const plan = await apiClient.generateNarration(presentationId, { voice_id: voiceId, target_wpm: wpm });
      onPlanGenerated(plan);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadVtt = async () => {
    try {
      const text = await apiClient.exportNarrationVtt(presentationId);
      downloadBlob(new Blob([text], { type: "text/vtt" }), `presentation_${presentationId}_captions.vtt`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Download failed");
    }
  };

  const handleDownloadAudio = async () => {
    try {
      const blob = await apiClient.downloadNarrationAudio(presentationId);
      downloadBlob(blob, `presentation_${presentationId}_narration.wav`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Download failed");
    }
  };

  const handleDownloadSlideAudio = async (slideIndex: number) => {
    try {
      const blob = await apiClient.downloadSlideAudio(presentationId, slideIndex);
      downloadBlob(blob, `slide_${slideIndex + 1}_audio.wav`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Download failed");
    }
  };

  return (
    <div className="narration-studio-container">
      <div className="narration-controls-card">
        <div className="controls-row">
          <div className="control-group">
            <label htmlFor="voice-select">Speaker Voice</label>
            <select id="voice-select" className="select-input" value={voiceId} onChange={(e) => setVoiceId(e.target.value)}>
              <option value="neutral-presenter">Neutral Presenter (1.0x)</option>
              <option value="technical-anchor">Technical Anchor (0.95x)</option>
              <option value="executive-brief">Executive Briefing (1.10x)</option>
            </select>
          </div>
          <div className="control-group">
            <label htmlFor="wpm-range">Speech Pace: {wpm} WPM</label>
            <input id="wpm-range" type="range" min="90" max="200" step="5" value={wpm} onChange={(e) => setWpm(Number(e.target.value))} />
          </div>
          <button className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
            {loading ? "Synthesizing..." : "Calculate Narration Timeline"}
          </button>
        </div>
        {error && <div className="error-banner">{error}</div>}
      </div>

      {!narrationPlan && !loading && (
        <div className="empty-state">
          <div className="empty-icon">🎙️</div>
          <h3>No Narration Schedule Generated</h3>
          <p>Generate audio narration cues and WebVTT captions from speaker notes.</p>
        </div>
      )}

      {narrationPlan && (
        <div>
          <div className="narration-stats-banner">
            <div className="stat-item"><span className="stat-label">Duration</span><span className="stat-value">{Math.round(narrationPlan.total_duration_seconds)}s</span></div>
            <div className="stat-item"><span className="stat-label">Words</span><span className="stat-value">{narrationPlan.estimated_words}</span></div>
            <div className="stat-item"><span className="stat-label">Effective Pace</span><span className="stat-value">{narrationPlan.target_wpm} WPM</span></div>
            <div className="stat-item"><span className="stat-label">Voice</span><span className="stat-value">{narrationPlan.voice_id}</span></div>
            <div className="stat-actions">
              <button className="btn btn-outline btn-sm" onClick={handleDownloadAudio}>🎧 Download Audio (WAV)</button>
              <button className="btn btn-outline btn-sm" onClick={handleDownloadVtt}>📥 Export WebVTT</button>
            </div>
          </div>

          <div style={{ background: "#fff", border: "1px solid var(--bdr)", borderRadius: "8px", padding: "1rem" }}>
            <h3 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>Speech Schedule ({narrationPlan.cues.length} Cues)</h3>
            <table className="cues-table">
              <thead><tr><th>Slide</th><th>Start</th><th>Duration</th><th>Transcript</th><th>Audio</th></tr></thead>
              <tbody>
                {narrationPlan.cues.map((cue, idx) => (
                  <tr key={idx}>
                    <td><strong>Slide {cue.slide_index + 1}</strong></td>
                    <td>{cue.start_time_seconds.toFixed(1)}s</td>
                    <td>{cue.duration_seconds.toFixed(1)}s</td>
                    <td>"{cue.speech_text}"</td>
                    <td><button className="btn btn-outline btn-xs" onClick={() => handleDownloadSlideAudio(cue.slide_index)}>⬇️ WAV</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
