from app.services.document_parser import DocumentParser
from app.services.slide_synthesizer import SlideSynthesizer


def test_slide_synthesizer_creates_balanced_slide_graph():
    """Verify that synthesizer converts document sections into multi-layout slide archetypes."""
    parser = DocumentParser()
    synthesizer = SlideSynthesizer()

    sample_doc = (
        "# AI Slide Generation Architecture\n\n"
        "## Problem Formulation\n"
        "- High latency in manual deck formatting.\n"
        "- Unverified AI presentations generate phantom citations.\n\n"
        "## System Pipeline\n"
        "- Document ingestion stage converts text into semantic spans.\n"
        "- Synthesis compiler maps archetypes deterministically.\n\n"
        "## Empirical Performance\n"
        "- Accuracy is 96.2% on benchmark datasets.\n"
        "- P99 Latency is 180 ms per slide.\n\n"
        "## Strategic Roadmap\n"
        "- Production integration with enterprise Keycloak SSO.\n"
        "- Support audio narration timelines and WebVTT captions.\n"
    )

    doc_result = parser.parse(sample_doc)
    slides = synthesizer.synthesize(doc_result)

    assert len(slides) >= 4
    # First slide must be hero_title
    assert slides[0].layout_type == "hero_title"
    assert slides[0].index == 0

    # Verify archetypes are represented
    layout_types = {s.layout_type for s in slides}
    assert "hero_title" in layout_types
    assert "problem_solution" in layout_types
    assert "metrics_chart" in layout_types or "architecture_process" in layout_types

    # Verify speaker notes are populated
    for slide in slides:
        assert slide.speaker_notes is not None
        assert len(slide.speaker_notes) > 10
        assert slide.content is not None


def test_slide_synthesizer_pads_short_documents():
    """Verify that short or single-paragraph inputs still produce a cohesive minimal deck."""
    parser = DocumentParser()
    synthesizer = SlideSynthesizer()

    short_doc = "Atlas Hub converts raw text into PowerPoint decks."
    doc_result = parser.parse(short_doc, fallback_title="Atlas Hub")
    slides = synthesizer.synthesize(doc_result)

    assert len(slides) >= 3
    assert slides[0].layout_type == "hero_title"
    assert slides[-1].layout_type == "conclusion_roadmap"
