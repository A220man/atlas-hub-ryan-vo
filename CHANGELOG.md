# Changelog

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — 2026-10-30

### Completed
- Narration audio WAV download fully implemented and tested
  - Frontend API client: `downloadNarrationAudio()` and `downloadSlideAudio()` methods
  - NarrationStudio UI: "Download Audio (WAV)" button in stats banner, per-slide WAV buttons in cues table
  - Backend endpoints: `GET /presentations/{id}/narration/audio` and `GET /presentations/{id}/narration/slides/{slide_index}/audio`
  - All backend tests pass (22/22)
  - All frontend tests pass (6/6)

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- Expose narration audio WAV download in the NarrationStudio UI (full deck + per-slide),
  with API client methods, backend integration tests, and frontend test coverage.
- Backend integration test coverage for per-slide audio endpoints.
- Frontend test coverage for per-slide audio download button in cues table.
- Narration service unit test for per-slide audio synthesis.

All notable changes to atlas-hub-ryan-vo are documented in this file.

## [1.0.0] - 2026-10-10

### Added
- Document and topic ingestion engine with hierarchical chunking and intent classification.
- Deterministic slide graph synthesis producing multi-layout slide decks (Hero, Problem-Solution, Architecture, Benchmark Metrics, Comparison, Conclusion).
- Native PowerPoint (`.pptx`) export compiler supporting OpenXML shapes, tables, charts, transitions, and speaker notes.
- Attribution Guard verifying span-level grounding of presentation claims against source documents with fail-closed diagnostics and cross-platform reliability.
- Multi-dimensional presentation quality evaluation engine scoring factual grounding, visual density balance, narrative pacing, and terminology consistency.
- Audio narration planner calculating speaker note pacing, speech duration, pause markers, and subtitle timeline exports.
- Multi-provider LLM advisory integration supporting OpenAI-compatible, Anthropic, Gemini, and Ollama with offline heuristic fallback.
- OIDC authorization code authentication with Keycloak and SAML identity brokering support, role-based access control, and development demo mode.
- Modern React and TypeScript dashboard with interactive slide previews, attribution inspection, scorecard analysis, and export workflows.