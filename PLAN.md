# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

advisory-api-endpoint

## Roadmap

### narration-audio-download — Expose narration audio WAV download in the frontend studio

Status: done

Acceptance:
- Frontend API client has a downloadNarrationAudio method calling /api/presentations/{id}/narration/audio
- Frontend API client has a downloadSlideAudio method calling /api/presentations/{id}/narration/slides/{slide_index}/audio
- NarrationStudio UI has a Download Audio (WAV) button in the stats banner
- NarrationStudio cues table has a per-slide WAV download button in an Audio column
- Backend integration test asserts audio export endpoint returns valid WAV bytes
- Frontend test verifies audio download button triggers API client call
- All existing tests continue to pass

Implementation: `frontend/src/api/client.ts`, `frontend/src/components/NarrationStudio.tsx`, `frontend/src/index.css`

Tests: `backend/tests/test_api_integration.py`, `frontend/src/test/NarrationStudio.test.tsx`

### advisory-api-endpoint — Implement AI Advisory API endpoint for presentation strategic review

Status: done

Acceptance:
- Backend API has POST /api/presentations/{id}/advisory endpoint
- Endpoint uses LLMAdvisoryService with offline heuristic fallback
- Endpoint requires analyst role
- Frontend AI Advisory tab calls the new API endpoint
- All existing tests continue to pass

Implementation: `backend/app/api/advisory.py`, `backend/app/api/templates.py`, `backend/app/main.py`

Tests: `backend/tests/test_llm_advisory.py`, `backend/tests/test_api_integration.py`

