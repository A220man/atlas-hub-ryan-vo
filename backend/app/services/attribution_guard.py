import re
from typing import List, Tuple
from pydantic import BaseModel, Field
from app.services.document_parser import DocumentParseResult
from app.services.slide_synthesizer import SlideGraphNode
from app.models.schemas import DiagnosticItem, SpanGrounding


class AttributionVerificationResult(BaseModel):
    is_valid: bool
    exit_code: int
    grounding_score: float
    total_claims: int
    grounded_claims: int
    unattributed_claims: int
    diagnostics: List[DiagnosticItem] = Field(default_factory=list)
    span_mappings: List[SpanGrounding] = Field(default_factory=list)


class AttributionGuard:
    CJK_REGEX = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]')
    LATIN_WORD_REGEX = re.compile(r'\b[A-Za-z]{3,}\b')

    def verify(self, slides: List[SlideGraphNode], doc_result: DocumentParseResult, enforce_single_language: bool = True) -> AttributionVerificationResult:
        diagnostics: List[DiagnosticItem] = []
        span_mappings: List[SpanGrounding] = []
        raw_source_text = " ".join(s.content for s in doc_result.sections).lower()
        total_claims = 0
        grounded_claims = 0

        if not doc_result.sections:
            diagnostics.append(DiagnosticItem(code="ATTR_DOC_EMPTY", severity="error", message="Source document contains no parsed sections.", suggestion="Verify input file contains text."))
            return AttributionVerificationResult(is_valid=False, exit_code=1, grounding_score=0.0, total_claims=0, grounded_claims=0, unattributed_claims=0, diagnostics=diagnostics, span_mappings=[])

        for node in slides:
            if not node.title.strip():
                diagnostics.append(DiagnosticItem(code="ATTR_EMPTY_TITLE", severity="error", slide_index=node.index, element="title", message=f"Slide #{node.index} has empty title.", suggestion="Provide a title for this slide."))

            for b_idx, bullet in enumerate(node.content.bullets):
                bullet_str = bullet.strip()
                if not bullet_str:
                    continue
                if node.layout_type == "hero_title":
                    is_grounded, conf, matched_text = True, 1.0, "deck_metadata"
                else:
                    is_grounded, conf, matched_text = self._check_claim_grounding(bullet_str, raw_source_text)

                total_claims += 1
                span_mappings.append(SpanGrounding(slide_index=node.index, claim=bullet_str, matched_source_span=matched_text, grounding_confidence=conf, is_grounded=is_grounded))
                if is_grounded:
                    grounded_claims += 1
                else:
                    diagnostics.append(DiagnosticItem(code="ATTR_UNGROUNDED_CLAIM", severity="error" if conf < 0.25 else "warning", slide_index=node.index, element=f"bullet_{b_idx}", message=f"Slide #{node.index} bullet '{bullet_str[:60]}' lacks source grounding.", suggestion="Rephrase bullet to reference findings."))

            if node.content.metric_value:
                digits = "".join(c for c in node.content.metric_value.lower() if c.isdigit())
                if digits and digits not in raw_source_text:
                    diagnostics.append(DiagnosticItem(code="ATTR_METRIC_MISMATCH", severity="warning", slide_index=node.index, element="metric_value", message=f"Metric '{node.content.metric_value}' on slide #{node.index} not in source.", suggestion="Ensure numbers match source records."))

            if enforce_single_language:
                diagnostics.extend(self._check_language_consistency(node))

        grounding_score = round((grounded_claims / total_claims * 100.0) if total_claims > 0 else 100.0, 1)
        has_blocking = any(d.severity == "error" for d in diagnostics)
        is_valid = not has_blocking and grounding_score >= 60.0

        return AttributionVerificationResult(
            is_valid=is_valid,
            exit_code=0 if is_valid else 1,
            grounding_score=grounding_score,
            total_claims=total_claims,
            grounded_claims=grounded_claims,
            unattributed_claims=total_claims - grounded_claims,
            diagnostics=diagnostics,
            span_mappings=span_mappings,
        )

    def _check_claim_grounding(self, claim: str, raw_source: str) -> Tuple[bool, float, str]:
        claim_clean = claim.lower()
        if claim_clean in raw_source:
            return True, 1.0, claim_clean
        words = set(self.LATIN_WORD_REGEX.findall(claim_clean))
        if not words:
            words = set([t.strip() for t in claim_clean.split() if len(t.strip()) > 2])
        if not words:
            return True, 0.7, "token_fallback"
        source_words = set(self.LATIN_WORD_REGEX.findall(raw_source))
        overlap = words.intersection(source_words)
        ratio = len(overlap) / len(words)
        return (True, round(ratio, 2), " ".join(list(overlap)[:5])) if ratio >= 0.50 else (False, round(ratio, 2), "")

    def _check_language_consistency(self, node: SlideGraphNode) -> List[DiagnosticItem]:
        items: List[DiagnosticItem] = []
        text = f"{node.title} {node.content.header or ''} {' '.join(node.content.bullets)}"
        if bool(self.CJK_REGEX.search(text)) and len(self.LATIN_WORD_REGEX.findall(text)) > 5:
            matches = self.CJK_REGEX.findall(text)
            if len(matches) > 3:
                items.append(DiagnosticItem(code="ATTR_LANG_MIXED", severity="info", slide_index=node.index, element="language_audit", message=f"Slide #{node.index} CJK glyphs detected alongside English copy ({len(matches)} glyphs).", suggestion="Align slide terminology to single locale."))
        return items
