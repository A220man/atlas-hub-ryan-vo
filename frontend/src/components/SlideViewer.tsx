import React, { useState } from "react";
import { Slide } from "../types/index.ts";

interface SlideViewerProps {
  slides: Slide[];
  templateId: string;
}

export const SlideViewer: React.FC<SlideViewerProps> = ({ slides, templateId }) => {
  const [currentIdx, setCurrentIdx] = useState<number>(0);

  if (!slides || slides.length === 0) {
    return (
      <div className="empty-state">
        <p>No slides in this presentation deck.</p>
      </div>
    );
  }

  const slide = slides[currentIdx] || slides[0];
  const total = slides.length;

  return (
    <div className="slide-viewer-container">
      {/* Slide Navigation Header */}
      <div className="viewer-toolbar">
        <div className="slide-nav-controls">
          <button
            className="btn btn-outline btn-sm"
            disabled={currentIdx === 0}
            onClick={() => setCurrentIdx((prev) => Math.max(0, prev - 1))}
          >
            &larr; Prev
          </button>
          <span className="slide-counter">
            Slide {currentIdx + 1} of {total}
          </span>
          <button
            className="btn btn-outline btn-sm"
            disabled={currentIdx === total - 1}
            onClick={() => setCurrentIdx((prev) => Math.min(total - 1, prev + 1))}
          >
            Next &rarr;
          </button>
        </div>
        <div className="slide-archetype-badges">
          <span className="badge badge-archetype">{slide.layout_type}</span>
          <span className="badge badge-template">{templateId}</span>
          {slide.content.transition && (
            <span className="badge badge-transition">⮀ {slide.content.transition}</span>
          )}
        </div>
      </div>

      {/* Visual Slide Canvas */}
      <div className={`slide-canvas template-${templateId} layout-${slide.layout_type}`}>
        <div className="canvas-header">
          {slide.content.header && (
            <div className="canvas-eyebrow">{slide.content.header}</div>
          )}
          <h2 className="canvas-title">{slide.title}</h2>
        </div>

        <div className="canvas-body">
          {slide.layout_type === "metrics_chart" && (
            <div className="metrics-layout">
              <div className="metric-stat-card">
                <div className="metric-val">{slide.content.metric_value || "96.8%"}</div>
                <div className="metric-lbl">{slide.content.metric_label || "Attribution Accuracy"}</div>
              </div>
              {slide.content.chart_series && (
                <div className="chart-bars-container">
                  <div className="chart-title">Data Series (OpenXML Chart)</div>
                  {slide.content.chart_series.map((item, i) => (
                    <div key={i} className="bar-row">
                      <span className="bar-label">{item.category}</span>
                      <div className="bar-track">
                        <div
                          className="bar-fill"
                          style={{ width: `${Math.min(100, Math.max(10, item.value))}%` }}
                        ></div>
                      </div>
                      <span className="bar-val">{item.value}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {slide.layout_type === "comparison_grid" && slide.content.table_columns && (
            <div className="table-preview-wrapper">
              <table className="comparison-table">
                <thead>
                  <tr>
                    {slide.content.table_columns.map((col, cIdx) => (
                      <th key={cIdx}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {slide.content.table_rows?.map((row, rIdx) => (
                    <tr key={rIdx}>
                      {row.map((cell, cellIdx) => (
                        <td key={cellIdx}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Bullet Points */}
          <ul className="canvas-bullets">
            {slide.content.bullets.map((bullet, bIdx) => (
              <li key={bIdx} className="bullet-item">
                <span className="bullet-dot">•</span>
                <span>{bullet}</span>
              </li>
            ))}
          </ul>

          {slide.content.callout && (
            <div className="canvas-callout">
              <strong>Takeaway:</strong> {slide.content.callout}
            </div>
          )}
        </div>
      </div>

      {/* Speaker Notes Drawer */}
      <div className="speaker-notes-box">
        <div className="notes-header">
          <span className="notes-icon">🎙️</span>
          <strong>Speaker Notes & Narration Script:</strong>
        </div>
        <p className="notes-text">{slide.notes || "No notes authored for this slide."}</p>
      </div>

      {/* Slide Thumbnails Rail */}
      <div className="thumbnail-rail">
        {slides.map((s, idx) => (
          <div
            key={idx}
            className={`thumbnail-card ${idx === currentIdx ? "active" : ""}`}
            onClick={() => setCurrentIdx(idx)}
          >
            <div className="thumb-num">{idx + 1}</div>
            <div className="thumb-title">{s.title}</div>
            <div className="thumb-type">{s.layout_type}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
