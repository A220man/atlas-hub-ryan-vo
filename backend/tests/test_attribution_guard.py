from app.services.attribution_guard import AttributionGuard
from app.services.document_parser import DocumentParser, DocumentParseResult
from app.services.slide_synthesizer import SlideSynthesizer, SlideGraphNode
from app.models.schemas import SlideContent


def test_attribution_guard_passes_for_grounded_presentation():
    """Verify that slides synthesized directly from source text pass the integrity gate."""
    parser = DocumentParser()
    synthesizer = SlideSynthesizer()
    guard = AttributionGuard()

    raw_doc = (
        "# Model Quality Evaluation\n\n"
        "## Architecture Overview\n"
        "- The pipeline processes document chunks hierarchically.\n"
        "- Deterministic slide graphs prevent hallucinated metrics.\n\n"
        "## Empirical Benchmarks\n"
        "- Throughput is 94.6 tokens/s on benchmark hardware.\n"
        "- Latency is 120 ms end-to-end.\n"
    )

    doc_result = parser.parse(raw_doc)
    slides = synthesizer.synthesize(doc_result)

    result = guard.verify(slides, doc_result)

    assert result.is_valid is True
    assert result.exit_code == 0
    assert result.grounding_score >= 60.0
    assert result.total_claims > 0
    assert result.grounded_claims > 0
    assert len(result.span_mappings) > 0


def test_attribution_guard_fails_closed_with_actionable_diagnostics_on_hallucination():
    """Directly verifies resolution to Issue 311: fail-closed with actionable diagnostics."""
    parser = DocumentParser()
    guard = AttributionGuard()

    raw_doc = "# Distributed Cache\nSystem uses LRU cache with Redis backend."
    doc_result = parser.parse(raw_doc)

    # Construct an ungrounded slide with fabricated metrics and claims
    fabricated_slide = SlideGraphNode(
        index=1,
        title="Unverified Claims",
        layout_type="metrics_chart",
        content=SlideContent(
            bullets=[
                "Quantum teleportation protocol accelerates neural transfer by 999x.",
                "Zero-point energy module powers edge nodes indefinitely."
            ],
            metric_value="999x",
        ),
        speaker_notes="Fabricated statements not supported by document.",
    )

    result = guard.verify([fabricated_slide], doc_result)

    # Fail closed: must return exit_code 1
    assert result.is_valid is False
    assert result.exit_code == 1

    # Actionable diagnostic guarantee (no silent exit)
    assert len(result.diagnostics) > 0
    claim_diags = [d for d in result.diagnostics if d.code == "ATTR_UNGROUNDED_CLAIM"]
    assert len(claim_diags) > 0
    first_diag = claim_diags[0]
    assert first_diag.slide_index == 1
    assert first_diag.suggestion is not None
    assert len(first_diag.message) > 10


def test_attribution_guard_handles_empty_document():
    """Verify fail-closed behavior when input document is empty."""
    guard = AttributionGuard()
    empty_result = DocumentParseResult(
        document_title="Empty Doc",
        total_characters=0,
        sections=[],
        all_spans=[],
    )

    result = guard.verify([], empty_result)
    assert result.is_valid is False
    assert result.exit_code == 1
    assert any(d.code == "ATTR_DOC_EMPTY" for d in result.diagnostics)


def test_language_drift_detection():
    """Verify detection of mixed CJK and Latin terminology (Issue 304 / Issue 302)."""
    parser = DocumentParser()
    guard = AttributionGuard()

    raw_doc = "# Bilingual Specification\nTest document for multi-lingual terminology audit."
    doc_result = parser.parse(raw_doc)

    mixed_slide = SlideGraphNode(
        index=2,
        title="Architecture Pipeline 架构流水线",
        layout_type="architecture_process",
        content=SlideContent(
            header="Core Engine 核心引擎",
            bullets=[
                "Pipeline executes deterministic stages: 计划会话完成 proceed.",
                "Review design spec before rendering: 重新排版 and beautify."
            ]
        ),
        speaker_notes="Mixed language notes.",
    )

    result = guard.verify([mixed_slide], doc_result, enforce_single_language=True)
    lang_diags = [d for d in result.diagnostics if d.code == "ATTR_LANG_MIXED"]
    assert len(lang_diags) > 0
    assert lang_diags[0].slide_index == 2
    assert "CJK glyphs detected" in lang_diags[0].message
