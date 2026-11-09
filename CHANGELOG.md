# Changelog

## 1.7.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.6.0 — work-in-progress checkpoint

### Completed
- AI Advisory API endpoint implemented: `POST /api/presentations/{id}/advisory`
  - Uses LLMAdvisoryService with provider-agnostic support (OpenAI, Anthropic, Gemini, Ollama) and offline heuristic fallback
  - Requires analyst role authorization
  - Frontend AI Advisory tab now connects to working backend endpoint
- All backend tests pass (22/22) including llm_advisory tests
- All frontend tests pass (6/6)

### Known Issues
- Partial code published for continued development. See STATUS.md.


## 1.5.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.5.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.4.0 — work-in-progress checkpoint

Verified narration audio WAV download feature complete and all tests passing:
- All backend tests pass (22/22) including narration audio integration tests
- All frontend tests pass (6/6) including NarrationStudio audio download button tests
- Frontend builds successfully

## 1.3.0 — 2026-10-30

### Completed
- Narration audio WAV download fully implemented and tested
  - Frontend API client: `downloadNarrationAudio()` and `downloadSlideAudio()` methods
  - NarrationStudio UI: "Download Audio (WAV)" button in stats banner, per-slide WAV buttons in cues table
  - Backend endpoints: `GET /presentations/{id}/narration/audio` and `GET /presentations/{id}/narration/slides/{slide_index}/audio`
  - All backend tests pass (22/22)
  - All frontend tests pass (6/6)