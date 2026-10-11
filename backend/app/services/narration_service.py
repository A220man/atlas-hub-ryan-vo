import io
import math
import wave
import struct
from typing import List
from app.services.slide_synthesizer import SlideGraphNode
from app.models.schemas import NarrationCue, NarrationPlanResponse


class NarrationService:
    """Calculates speech pacing, audio timelines, subtitle scripts, and synthesizes audio."""

    VOICE_PROFILES = {
        "neutral-presenter": {"label": "Neutral Presenter", "speed_multiplier": 1.0, "pitch": 160.0},
        "technical-anchor": {"label": "Technical Anchor", "speed_multiplier": 0.95, "pitch": 135.0},
        "executive-brief": {"label": "Executive Briefing", "speed_multiplier": 1.10, "pitch": 180.0},
    }

    def generate_plan(
        self,
        slides: List[SlideGraphNode],
        presentation_id: str,
        voice_id: str = "neutral-presenter",
        target_wpm: int = 140,
    ) -> NarrationPlanResponse:
        cues: List[NarrationCue] = []
        current_time = 0.0
        total_words = 0
        voice_mult = self.VOICE_PROFILES.get(voice_id, {}).get("speed_multiplier", 1.0)
        effective_wpm = max(80, int(target_wpm * voice_mult))

        for node in slides:
            speech_text = node.speaker_notes.strip()
            if not speech_text:
                bullets_joined = " ".join(node.content.bullets)
                speech_text = f"{node.title}. {bullets_joined}"
            words = speech_text.split()
            word_count = len(words)
            total_words += word_count
            duration_seconds = round(max(3.0, (word_count / (effective_wpm / 60.0))), 1)

            cues.append(
                NarrationCue(
                    slide_index=node.index,
                    slide_title=node.title,
                    start_time_seconds=round(current_time, 1),
                    duration_seconds=duration_seconds,
                    speech_text=speech_text,
                    pause_after_seconds=0.8,
                )
            )
            current_time += duration_seconds + 0.8

        return NarrationPlanResponse(
            presentation_id=presentation_id,
            total_duration_seconds=round(current_time, 1),
            estimated_words=total_words,
            voice_id=voice_id,
            target_wpm=effective_wpm,
            cues=cues,
        )

    def synthesize_audio(self, cues: List[NarrationCue], voice_id: str = "neutral-presenter") -> bytes:
        """Synthesize continuous PCM WAV speech audio across all slide cues."""
        pitch = self.VOICE_PROFILES.get(voice_id, {}).get("pitch", 160.0)
        return self._render_wav(cues, pitch)

    def synthesize_slide_audio(self, cue: NarrationCue, voice_id: str = "neutral-presenter") -> bytes:
        """Synthesize PCM WAV speech audio for a single slide cue."""
        pitch = self.VOICE_PROFILES.get(voice_id, {}).get("pitch", 160.0)
        return self._render_wav([cue], pitch)

    def _render_wav(self, cues: List[NarrationCue], pitch: float) -> bytes:
        rate = 22050
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            samples = []
            for cue in cues:
                words = cue.speech_text.split()
                usable_time = max(0.5, cue.duration_seconds - cue.pause_after_seconds)
                word_dur = max(0.18, usable_time / max(1, len(words)))
                for i, word in enumerate(words):
                    n_samples = int(rate * word_dur)
                    f0 = pitch * (1.0 + 0.08 * math.sin(i * 0.9))
                    f1 = 450.0 + (hash(word) % 250)
                    for s in range(n_samples):
                        t = s / rate
                        frac = s / n_samples
                        env = math.sin(frac * math.pi) ** 0.5
                        wave_val = math.sin(2 * math.pi * f0 * t) + 0.4 * math.sin(4 * math.pi * f0 * t) + 0.3 * math.sin(2 * math.pi * f1 * t)
                        if frac < 0.08:
                            wave_val += 0.25 * (1.0 - frac / 0.08)
                        val = int(max(-32767, min(32767, 32767 * 0.45 * env * wave_val)))
                        samples.append(struct.pack("<h", val))
                pause_samples = int(rate * cue.pause_after_seconds)
                samples.extend([struct.pack("<h", 0)] * pause_samples)
            wf.writeframes(b"".join(samples))
        return buf.getvalue()

    def export_webvtt(self, cues: List[NarrationCue]) -> str:
        lines = ["WEBVTT", ""]
        for idx, cue in enumerate(cues):
            start = self._format_timestamp_vtt(cue.start_time_seconds)
            end = self._format_timestamp_vtt(cue.start_time_seconds + cue.duration_seconds)
            lines.append(f"{idx + 1}")
            lines.append(f"{start} --> {end}")
            lines.append(f"[{cue.slide_title}] {cue.speech_text}")
            lines.append("")
        return "\n".join(lines)

    def _format_timestamp_vtt(self, seconds: float) -> str:
        hrs = int(seconds // 3600)
        rem = seconds % 3600
        mins = int(rem // 60)
        secs = rem % 60
        whole_secs = int(secs)
        millis = int((secs - whole_secs) * 1000)
        return f"{hrs:02d}:{mins:02d}:{whole_secs:02d}.{millis:03d}"
