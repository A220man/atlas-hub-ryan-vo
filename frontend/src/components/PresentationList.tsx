import React, { useState, useEffect, useCallback } from "react";
import { PresentationSummary } from "../types/index.ts";
import { apiClient } from "../api/client.ts";
import { useAuth } from "../context/AuthContext.tsx";

interface PresentationListProps {
  onSelectPresentation: (id: string) => void;
  onOpenCreate: () => void;
}

export const PresentationList: React.FC<PresentationListProps> = ({
  onSelectPresentation,
  onOpenCreate,
}) => {
  const { hasRole } = useAuth();
  const [presentations, setPresentations] = useState<PresentationSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [topicFilter, setTopicFilter] = useState<string>("");

  const loadPresentations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.listPresentations({
        search: searchTerm || undefined,
        topic: topicFilter || undefined,
      });
      setPresentations(res.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load presentations");
    } finally {
      setLoading(false);
    }
  }, [searchTerm, topicFilter]);

  useEffect(() => {
    loadPresentations();
  }, [loadPresentations]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this presentation?")) {
      return;
    }
    try {
      await apiClient.deletePresentation(id);
      setPresentations((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      alert(err instanceof Error ? err.message : "Deletion failed");
    }
  };

  return (
    <div className="presentation-list-container">
      <div className="list-header">
        <div>
          <h2>Presentation Decks</h2>
          <p className="subtitle">
            Synthesized structured slide graphs with span-level attribution integrity
          </p>
        </div>
        {hasRole("analyst") && (
          <button className="btn btn-primary" onClick={onOpenCreate}>
            + New Presentation
          </button>
        )}
      </div>

      <div className="filter-bar">
        <input
          type="text"
          className="search-input"
          placeholder="Search by presentation title..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <input
          type="text"
          className="search-input"
          placeholder="Filter by topic or domain..."
          value={topicFilter}
          onChange={(e) => setTopicFilter(e.target.value)}
        />
      </div>

      {loading && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading presentations from persistent store...</p>
        </div>
      )}

      {error && (
        <div className="error-banner">
          <p>Error: {error}</p>
          <button className="btn btn-outline btn-sm" onClick={loadPresentations}>
            Retry
          </button>
        </div>
      )}

      {!loading && !error && presentations.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <h3>No Presentations Found</h3>
          <p>
            Synthesize a native PowerPoint presentation from technical notes, papers, or markdown specs.
          </p>
          {hasRole("analyst") && (
            <button className="btn btn-primary" onClick={onOpenCreate}>
              Synthesize First Presentation
            </button>
          )}
        </div>
      )}

      {!loading && presentations.length > 0 && (
        <div className="deck-grid">
          {presentations.map((deck) => (
            <div
              key={deck.id}
              className="deck-card"
              onClick={() => onSelectPresentation(deck.id)}
            >
              <div className="deck-card-header">
                <span className="badge badge-template">{deck.template_id}</span>
                <span className={`badge badge-status badge-${deck.status}`}>
                  {deck.status}
                </span>
              </div>
              <h3 className="deck-title">{deck.title}</h3>
              <p className="deck-topic">{deck.topic || "General Technical Overview"}</p>
              <div className="deck-meta">
                <span>📑 {deck.slide_count} slides</span>
                <span>📐 {deck.aspect_ratio}</span>
                <span>👤 {deck.created_by.split("@")[0]}</span>
              </div>
              <div className="deck-card-footer">
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => onSelectPresentation(deck.id)}
                >
                  View Studio
                </button>
                {hasRole("analyst") && (
                  <button
                    className="btn btn-danger-outline btn-sm"
                    onClick={(e) => handleDelete(e, deck.id)}
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
