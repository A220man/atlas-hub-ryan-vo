# Atlas Hub — Feature Coverage Inventory

**Product:** atlas-hub-ryan-vo  
**Author:** Ryan Vo (ryandtvo@gmail.com | GitHub: A220man)  
**Reference System:** ppt-master (by Hugo He)  
**Implementation Policy:** Clean-room original implementation, independent architecture, zero copied code or assets.

---

## 1. Core Capabilities & Coverage Matrix

| # | Core Capability | Reference Requirement | Atlas Hub Implementation Path | Acceptance Tests | Status |
|---|---|---|---|---|---|
| 1 | **Document & Topic Ingestion** | Ingest unstructured Markdown/text, extract topics & sections | `backend/app/services/document_parser.py` (`DocumentParser`) | `backend/tests/test_document_parser.py`, `backend/tests/test_api_integration.py` | Complete |
| 2 | **Deterministic Slide Graph Synthesis** | 6 slide archetypes with structured content and speaker notes | `backend/app/services/slide_synthesizer.py` (`SlideSynthesizer`) | `backend/tests/test_slide_synthesizer.py` | Complete |
| 3 | **Native PowerPoint Shapes, Tables & Charts** | OpenXML native shapes, formatted bullet text, tables, category charts | `backend/app/services/pptx_compiler.py` (`PPTXCompiler`) | `backend/tests/test_pptx_compiler.py` | Complete |
| 4 | **Native PowerPoint Transitions & Animations** | Native `<p:transition>` (fade, push, wipe) & `<p:timing>` entrance animations in OpenXML | `backend/app/services/pptx_compiler.py` (`_apply_slide_transition`, `_apply_shape_animations`) | `backend/tests/test_pptx_compiler.py::test_pptx_transitions_and_animations` | Complete |
| 5 | **Audio Narration from Speaker Notes** | Timed speech cues, WPM speech pacing, WebVTT subtitle export, and real PCM WAV audio synthesis | `backend/app/services/narration_service.py` (`NarrationService`), `backend/app/api/narration.py` | `backend/tests/test_narration_service.py` | Complete |
| 6 | **Custom .pptx Template Ingestion & Application** | Upload user `.pptx` template, extract layouts & theme metrics, apply to new presentations | `backend/app/api/templates.py`, `backend/app/services/pptx_compiler.py` (`ingest_template`, `compile_with_template`) | `backend/tests/test_pptx_compiler.py::test_custom_template_ingestion_and_compilation` | Complete |
| 7 | **Attribution Guard & Integrity Gate** | Fail-closed integrity gate with actionable diagnostics on hallucination (Issue #311) | `backend/app/services/attribution_guard.py` (`AttributionGuard`) | `backend/tests/test_attribution_guard.py` | Complete |
| 8 | **Multilingual Neutral Prompts & Terminology** | Neutral language rules, prompt audit, consistent terminology (Issues #304, #302) | `backend/app/services/attribution_guard.py` (`_check_language_consistency`) | `backend/tests/test_attribution_guard.py::test_language_drift_detection` | Complete |
| 9 | **4-Pillar Quality Evaluation Scorecard** | Grounding (40%), Balance (25%), Pacing (20%), Consistency (15%) | `backend/app/services/evaluation_engine.py` (`EvaluationEngine`) | `backend/tests/test_evaluation_engine.py` | Complete |
| 10 | **Reproducible AI/ML Benchmark** | Evaluation engine with in-memory scoring; benchmark corpus not shipped in this repository | `backend/app/services/evaluation_engine.py` (`EvaluationEngine`) | `backend/tests/test_evaluation_engine.py` | Partial |
| 11 | **Provider-Agnostic LLM Advisory** | OpenAI-compatible, Anthropic, Gemini, Ollama adapters with offline deterministic fallback | `backend/app/services/llm_advisory.py` (`LLMAdvisoryService`) | `backend/tests/test_llm_advisory.py` | Complete |
| 12 | **Enterprise OIDC & Keycloak Broker** | OIDC PKCE login, in-memory tokens, SAML broker documentation, RBAC | `backend/app/core/security.py`, `backend/app/api/auth.py`, `frontend/src/context/AuthContext.tsx` | `backend/tests/test_auth.py`, `backend/tests/test_api_integration.py` | Complete |

---

## 2. User Issue Resolutions

### Issue #225: Onboarding & Documentation Usability
- **Problem**: Upstream tools were heavy and lacked step-by-step guidance.
- **Solution**: Atlas Hub provides zero-config local development, clear Docker Compose setup, comprehensive README with Mermaid diagrams, and interactive UI with demo login.
### Issue #311: Attribution Guard Silent Exit 1 on Windows
- **Problem**: Attribution gate exited with code 1 without diagnostics or stdout/stderr on Windows.
- **Solution**: `AttributionGuard` implements explicit fail-closed guarantees with structured diagnostic codes (`ATTR_UNGROUNDED_CLAIM`, `ATTR_METRIC_MISMATCH`, `ATTR_LANG_MIXED`), specific slide numbers, remediation guidance, and cross-platform compatibility without shell dependencies.

### Issue #304 & #302: Multilingual Language Drift & Terminology Inconsistency
- **Problem**: Inconsistent localization dictionaries and ungrounded mixed-script prompts.
- **Solution**: The attribution engine inspects character scripts to detect untranslated language drift (`ATTR_LANG_MIXED`) and enforces consistent vocabulary across UI and slide decks.

---

## 3. Verification & Acceptance Testing

- **Backend Pytest**: `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -v`
- **Frontend Typecheck & Build**: `cd frontend && npm run build`
- **Frontend Vitest**: `cd frontend && npm test`
|- **Reproducible Evaluation**: `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_attribution_guard.py backend/tests/test_evaluation_engine.py -v`
