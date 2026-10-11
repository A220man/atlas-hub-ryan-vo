from app.services.document_parser import DocumentParser
from app.services.slide_synthesizer import SlideSynthesizer, SlideGraphNode
from app.services.evaluation_engine import EvaluationEngine
from app.models.schemas import SlideContent


def test_evaluation_engine_generates_comprehensive_scorecard():
    """Verify that evaluation engine calculates 4-pillar metrics and summary."""
    parser = DocumentParser()
    synthesizer = SlideSynthesizer()
    engine = EvaluationEngine()

    raw_doc = (
        "# Model Alignment Evaluation\n\n"
        "## Methodology\n"
        "- Document spans are indexed with character start and end offsets.\n"
        "- Slide claims are cross-checked against indexed token spans.\n\n"
        "## Empirical Results\n"
        "- Grounding accuracy is 95.5%.\n"
        "- Evaluation latency is 45 ms.\n"
    )

    doc_result = parser.parse(raw_doc)
    slides = synthesizer.synthesize(doc_result)

    scorecard = engine.evaluate(slides, doc_result, presentation_id="test-p1")

    assert scorecard.overall_score >= 0.0
    assert scorecard.grounding_score >= 60.0
    assert scorecard.balance_score > 0.0
    assert scorecard.pacing_score > 0.0
    assert scorecard.consistency_score > 0.0
    assert scorecard.status in {"passed", "flagged"}
    assert "Overall Score" in scorecard.summary


def test_evaluation_engine_detects_high_density_slide():
    """Verify that slides with excessive words trigger EVAL_HIGH_DENSITY diagnostic."""
    parser = DocumentParser()
    engine = EvaluationEngine()

    doc_result = parser.parse("# Summary\nShort reference content.")

    dense_slide = SlideGraphNode(
        index=0,
        title="Excessively Wordy Slide",
        layout_type="architecture_process",
        content=SlideContent(
            bullets=[
                "This is an extremely detailed paragraph designed to simulate high textual density on a single presentation slide without appropriate visual chunking or bullet brevity.",
                "In addition to the previous sentence this second bullet contains extensive operational descriptions and repetitive architectural explanations that overwhelm audience cognitive load.",
                "Finally a third redundant statement reinforces the verbosity problem and pushes the total word count well beyond the sixty word readability threshold."
            ]
        ),
        speaker_notes="Wordy notes.",
    )

    scorecard = engine.evaluate([dense_slide], doc_result)
    density_diags = [d for d in scorecard.diagnostics if d.code == "EVAL_HIGH_DENSITY"]
    assert len(density_diags) > 0
    assert density_diags[0].slide_index == 0
