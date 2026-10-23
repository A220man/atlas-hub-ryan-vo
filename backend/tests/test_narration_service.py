from app.services.slide_synthesizer import SlideGraphNode
from app.services.narration_service import NarrationService
from app.models.schemas import SlideContent


def test_narration_service_computes_speech_timeline():
    """Verify speech timing calculations and WebVTT caption generation."""
    service = NarrationService()

    slides = [
        SlideGraphNode(
            index=0,
            title="Introduction to Atlas Hub",
            layout_type="hero_title",
            content=SlideContent(bullets=["Welcome everyone to the briefing."]),
            speaker_notes="Welcome everyone. Today we review native slide generation and attribution guardrails.",
        ),
        SlideGraphNode(
            index=1,
            title="Core Performance Benchmarks",
            layout_type="metrics_chart",
            content=SlideContent(bullets=["Throughput is 94 tokens per second."]),
            speaker_notes="On this slide we inspect empirical throughput and low-latency response times.",
        )
    ]

    plan = service.generate_plan(slides, presentation_id="pres-123", voice_id="neutral-presenter", target_wpm=140)

    assert plan.total_duration_seconds > 0
    assert plan.estimated_words > 0
    assert len(plan.cues) == 2
    assert plan.cues[0].start_time_seconds == 0.0
    assert plan.cues[1].start_time_seconds > plan.cues[0].duration_seconds

    # Test WebVTT export
    vtt = service.export_webvtt(plan.cues)
    assert vtt.startswith("WEBVTT")
    assert "-->" in vtt
    assert "[Introduction to Atlas Hub]" in vtt

    # Test full deck audio synthesis
    audio = service.synthesize_audio(plan.cues)
    assert len(audio) > 100
    assert audio.startswith(b"RIFF")

    # Test per-slide audio synthesis
    slide_audio = service.synthesize_slide_audio(plan.cues[0])
    assert len(slide_audio) > 100
    assert slide_audio.startswith(b"RIFF")
