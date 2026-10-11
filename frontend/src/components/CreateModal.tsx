import React, { useState } from "react";
import { apiClient } from "../api/client.ts";

interface CreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (presentationId: string) => void;
}

const SAMPLE_DOCUMENT = `# Multi-Modal Alignment & Slide Synthesis Engine

## Problem Formulation & Challenges
- Traditional AI slide generation produces hallucinated statistics without source grounding.
- Static image exports lack client-side PowerPoint editability and native shape geometry.

## Empirical Performance Benchmarks
- Span grounding verification accuracy is 96.8% on technical corpora.
- End-to-end synthesis latency is 240 ms per 6-slide deck.

## Deployment Roadmap
- Enterprise Keycloak OIDC integration with SAML broker support.`;

export const CreateModal: React.FC<CreateModalProps> = ({
  isOpen,
  onClose,
  onCreated,
}) => {
  const [title, setTitle] = useState<string>("Multi-Modal Slide Synthesis Engine");
  const [topic, setTopic] = useState<string>("AI/ML developer tools");
  const [rawContent, setRawContent] = useState<string>(SAMPLE_DOCUMENT);
  const [templateId, setTemplateId] = useState<string>("modern-navy");
  const [aspectRatio, setAspectRatio] = useState<string>("16:9");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !rawContent.trim()) {
      setError("Title and document content are required.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const pres = await apiClient.createPresentation({
        title,
        topic,
        raw_content: rawContent,
        template_id: templateId,
        aspect_ratio: aspectRatio,
      });
      onCreated(pres.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to synthesize presentation.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleLoadSample = () => {
    setTitle("Multi-Modal Slide Synthesis Engine");
    setTopic("AI/ML developer tools");
    setRawContent(SAMPLE_DOCUMENT);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Synthesize Native Presentation</h3>
          <button className="btn-close" onClick={onClose}>&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {error && <div className="error-banner">{error}</div>}

          <div className="form-group">
            <label htmlFor="deck-title">Deck Title</label>
            <input
              id="deck-title"
              type="text"
              className="text-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Distributed Model Quality Architecture"
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group flex-1">
              <label htmlFor="deck-topic">Topic / Domain</label>
              <input
                id="deck-topic"
                type="text"
                className="text-input"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. AI/ML developer tools"
              />
            </div>
            <div className="form-group flex-1">
              <label htmlFor="deck-template">Design Template</label>
              <select
                id="deck-template"
                className="select-input"
                value={templateId}
                onChange={(e) => setTemplateId(e.target.value)}
              >
                <option value="modern-navy">Modern Navy (High Contrast)</option>
                <option value="emerald-clean">Emerald Clean (Fresh)</option>
                <option value="slate-minimal">Slate Minimal (Graphite)</option>
              </select>
            </div>
            <div className="form-group flex-1">
              <label htmlFor="deck-aspect">Aspect Ratio</label>
              <select
                id="deck-aspect"
                className="select-input"
                value={aspectRatio}
                onChange={(e) => setAspectRatio(e.target.value)}
              >
                <option value="16:9">16:9 Widescreen</option>
                <option value="4:3">4:3 Standard</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <div className="label-row">
              <label htmlFor="deck-content">Document / Topic Specification (Markdown)</label>
              <button
                type="button"
                className="btn-link"
                onClick={handleLoadSample}
              >
                Load Sample Document
              </button>
            </div>
            <textarea
              id="deck-content"
              className="textarea-input"
              rows={9}
              value={rawContent}
              onChange={(e) => setRawContent(e.target.value)}
              placeholder="# Introduction&#10;&#10;## Key Architecture Challenges..."
              required
            />
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-outline"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? "Synthesizing Slides..." : "Generate Slide Graph"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
