import pytest
from app.services.llm_advisory import LLMAdvisoryService
from app.services.slide_synthesizer import SlideGraphNode
from app.models.schemas import SlideContent


@pytest.mark.asyncio
async def test_offline_heuristic_advisory_when_no_key_configured():
    """Verify that offline heuristic advisor runs deterministically without an LLM key."""
    service = LLMAdvisoryService()
    service.api_key = None

    slides = [
        SlideGraphNode(
            index=0,
            title="System Overview",
            layout_type="hero_title",
            content=SlideContent(bullets=["First bullet point"]),
            speaker_notes="Overview notes.",
        ),
        SlideGraphNode(
            index=1,
            title="Performance Metrics",
            layout_type="metrics_chart",
            content=SlideContent(bullets=["Empirical throughput metric"]),
            speaker_notes="Metrics notes.",
        )
    ]

    resp = await service.get_advisory(slides, query_type="pacing_review")

    assert resp.is_advisory is True
    assert resp.provider == "offline-heuristic"
    assert "System Overview" in resp.grounded_references
    assert len(resp.advice) > 20


def test_credential_redaction_in_errors():
    """Verify redaction utility redacts runtime-generated synthetic tokens without literals."""
    service = LLMAdvisoryService()

    # Generate synthetic token dynamically at runtime
    synthetic_key = "sk-" + ("0" * 24)
    error_msg = f"Failed to connect using key {synthetic_key} and Bearer " + ("b" * 20)

    redacted = service._redact_secrets(error_msg)
    assert synthetic_key not in redacted
    assert "[REDACTED_KEY]" in redacted
    assert "Bearer [REDACTED]" in redacted
