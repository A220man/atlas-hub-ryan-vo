import re
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class DocumentSpan(BaseModel):
    span_id: str
    start_char: int
    end_char: int
    section_title: str
    text: str
    is_claim: bool = False
    metric_value: Optional[str] = None


class ParsedSection(BaseModel):
    section_index: int
    title: str
    content: str
    intent: str
    bullets: List[str] = Field(default_factory=list)
    metrics: List[Dict[str, str]] = Field(default_factory=list)
    spans: List[DocumentSpan] = Field(default_factory=list)


class DocumentParseResult(BaseModel):
    document_title: str
    total_characters: int
    sections: List[ParsedSection]
    all_spans: List[DocumentSpan]


class DocumentParser:
    INTENT_KEYWORDS = {
        "problem": ["problem", "challenge", "bottleneck", "issue", "limitation", "latency", "failure"],
        "architecture": ["architecture", "design", "methodology", "pipeline", "framework", "approach", "engine"],
        "metrics": ["benchmark", "result", "evaluation", "performance", "throughput", "accuracy", "speed", "%", "ms"],
        "comparison": ["comparison", "vs", "versus", "tradeoff", "baseline", "alternative"],
        "conclusion": ["conclusion", "summary", "roadmap", "future", "takeaway", "recommendation"],
    }
    METRIC_PATTERN = re.compile(r'(?P<label>[A-Za-z0-9_\-\s]{3,25}?)\s*(?:is|was|of|:|=)\s*(?P<val>[0-9]+(?:\.[0-9]+)?(?:\s*(?:%|ms|s|x|kb|mb|gb|tokens/s|queries/s|fps))?)', re.IGNORECASE)

    def parse(self, raw_text: str, fallback_title: str = "Presentation Overview") -> DocumentParseResult:
        cleaned = raw_text.strip()
        lines = cleaned.splitlines()
        doc_title = fallback_title
        for line in lines:
            l = line.strip()
            if l.startswith("# "):
                doc_title = l.lstrip("# ").strip()
                break
            elif l and not l.startswith("#"):
                doc_title = l[:60].strip()
                break

        sections: List[ParsedSection] = []
        all_spans: List[DocumentSpan] = []
        header_splits = re.split(r'\n(?=#{1,3}\s+)', cleaned)
        if len(header_splits) <= 1:
            header_splits = [p.strip() for p in cleaned.split("\n\n") if p.strip()]

        char_offset = 0
        for idx, block in enumerate(header_splits):
            block_str = block.strip()
            if not block_str:
                continue
            block_start = cleaned.find(block_str, char_offset)
            if block_start == -1:
                block_start = char_offset
            block_end = block_start + len(block_str)
            char_offset = block_end

            b_lines = [l.strip() for l in block_str.splitlines() if l.strip()]
            sec_title = re.sub(r'^#{1,3}\s*', '', b_lines[0] if b_lines else f"Section {idx + 1}").strip()
            bullets: List[str] = []
            for line in b_lines[1:]:
                if line.startswith(("-", "*", "•", "1.", "2.", "3.", "4.")):
                    cb = re.sub(r'^(?:[-*•]|\d+\.)\s*', '', line).strip()
                    if cb:
                        bullets.append(cb)
            if not bullets and len(b_lines) > 1:
                sentences = re.split(r'(?<=[.!?])\s+', " ".join(b_lines[1:]))
                bullets = [s.strip() for s in sentences if len(s.strip()) > 15][:5]

            sec_intent = self._classify_intent(sec_title, block_str, idx, len(header_splits))
            metrics_found: List[Dict[str, str]] = []
            for match in self.METRIC_PATTERN.finditer(block_str):
                lbl, val = match.group("label").strip(), match.group("val").strip()
                if lbl and val and len(lbl) > 2:
                    metrics_found.append({"label": lbl, "value": val})

            section_spans: List[DocumentSpan] = []
            s_span = DocumentSpan(span_id=f"span-{idx}-0", start_char=block_start, end_char=block_end, section_title=sec_title, text=block_str, is_claim=bool(metrics_found or bullets))
            section_spans.append(s_span)
            all_spans.append(s_span)

            for b_idx, b_text in enumerate(bullets):
                b_start = block_str.find(b_text)
                act_start = block_start + (b_start if b_start != -1 else 0)
                b_span = DocumentSpan(span_id=f"span-{idx}-{b_idx + 1}", start_char=act_start, end_char=act_start + len(b_text), section_title=sec_title, text=b_text, is_claim=True)
                section_spans.append(b_span)
                all_spans.append(b_span)

            sections.append(ParsedSection(section_index=idx, title=sec_title, content=block_str, intent=sec_intent, bullets=bullets, metrics=metrics_found, spans=section_spans))

        return DocumentParseResult(document_title=doc_title, total_characters=len(cleaned), sections=sections, all_spans=all_spans)

    def _classify_intent(self, title: str, block: str, index: int, total_blocks: int) -> str:
        if index == 0:
            return "title"
        if index == total_blocks - 1 and total_blocks > 2:
            return "conclusion"
        combined = f"{title} {block}".lower()
        scores = {intent: sum(1 for kw in kws if kw in combined) for intent, kws in self.INTENT_KEYWORDS.items()}
        best = max(scores, key=lambda k: scores[k])
        return best if scores[best] > 0 else "architecture"
