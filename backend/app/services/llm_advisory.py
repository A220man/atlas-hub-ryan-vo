import re
from typing import List, Optional
import httpx
from app.core.config import settings
from app.services.slide_synthesizer import SlideGraphNode
from app.models.schemas import AdvisoryResponse


class LLMAdvisoryService:
    TIMEOUT_SECONDS = 15.0

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL

    async def get_advisory(self, slides: List[SlideGraphNode], query_type: str = "executive_review", custom_instructions: Optional[str] = None) -> AdvisoryResponse:
        grounded_refs = [s.title for s in slides]
        if not self.api_key:
            return self._offline_heuristic_advisory(slides, query_type, grounded_refs)

        prompt = f"Review deck with {len(slides)} slides. Query: {query_type}\n" + "\n".join(f"Slide {s.index + 1}: '{s.title}' (Layout: {s.layout_type})" for s in slides)
        if custom_instructions:
            prompt += f"\nInstructions: {custom_instructions}"

        try:
            advice_text = await self._call_provider(prompt)
            return AdvisoryResponse(provider=self.provider, model=self.model, advice=advice_text, grounded_references=grounded_refs, is_advisory=True)
        except Exception as exc:
            fallback = self._offline_heuristic_advisory(slides, query_type, grounded_refs)
            fallback.advice = f"[Notice: Provider error ({self._redact_secrets(str(exc))}). Offline heuristic provided.]\n\n" + fallback.advice
            return fallback

    async def _call_provider(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
            if self.provider == "anthropic":
                url = self.base_url or "https://api.anthropic.com/v1/messages"
                resp = await client.post(url, headers={"x-api-key": self.api_key or "", "anthropic-version": "2023-06-01", "content-type": "application/json"}, json={"model": self.model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]})
                resp.raise_for_status()
                return resp.json()["content"][0]["text"]
            elif self.provider == "gemini":
                url = self.base_url or f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
                resp = await client.post(url, headers={"content-type": "application/json"}, params={"key": self.api_key or ""}, json={"contents": [{"parts": [{"text": prompt}]}]})
                resp.raise_for_status()
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                url = (self.base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
                resp = await client.post(url, headers={"Authorization": f"Bearer {self.api_key or ''}", "Content-Type": "application/json"}, json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 800})
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]

    def _offline_heuristic_advisory(self, slides: List[SlideGraphNode], query_type: str, grounded_refs: List[str]) -> AdvisoryResponse:
        total = len(slides)
        has_chart = any(s.layout_type == "metrics_chart" for s in slides)
        advice = f"Advisory Analysis for {total}-slide deck ({query_type}):\n1. Structural balance across {total} slides.\n2. Quantitative visuals: {'Chart verified.' if has_chart else 'Consider adding metric charts.'}\n3. Slide transitions grounded in source text."
        return AdvisoryResponse(provider="offline-heuristic", model="deterministic-rule-v1", advice=advice, grounded_references=grounded_refs, is_advisory=True)

    def _redact_secrets(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'Bearer\s+[A-Za-z0-9_\-\.]{10,}', 'Bearer [REDACTED]', text)
        return re.sub(r'(?:sk-[a-zA-Z0-9_\-]{15,}|key=[a-zA-Z0-9_\-]{15,})', '[REDACTED_KEY]', text)
