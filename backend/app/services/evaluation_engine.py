from typing import List, Tuple
from app.services.slide_synthesizer import SlideGraphNode
from app.services.document_parser import DocumentParseResult
from app.services.attribution_guard import AttributionGuard
from app.models.schemas import EvaluationScorecard, DiagnosticItem


class EvaluationEngine:
    def __init__(self):
        self.attribution_guard = AttributionGuard()

    def evaluate(self, slides: List[SlideGraphNode], doc_result: DocumentParseResult, presentation_id: str = "pres-eval") -> EvaluationScorecard:
        attr_result = self.attribution_guard.verify(slides, doc_result)
        grounding_score = attr_result.grounding_score
        balance_score, balance_diags = self._evaluate_balance(slides)
        pacing_score, pacing_diags = self._evaluate_pacing(slides)
        consistency_score, consistency_diags = self._evaluate_consistency(slides)

        all_diagnostics = list(attr_result.diagnostics) + balance_diags + pacing_diags + consistency_diags
        overall_score = round(0.40 * grounding_score + 0.25 * balance_score + 0.20 * pacing_score + 0.15 * consistency_score, 1)
        status_str = "passed" if (overall_score >= 70.0 and attr_result.is_valid) else "flagged"
        summary = f"Evaluation {status_str.upper()}: Overall Score {overall_score}/100. Grounding: {grounding_score}%, Balance: {balance_score}%, Pacing: {pacing_score}%, Consistency: {consistency_score}%."

        return EvaluationScorecard(
            presentation_id=presentation_id,
            overall_score=overall_score,
            grounding_score=grounding_score,
            balance_score=balance_score,
            pacing_score=pacing_score,
            consistency_score=consistency_score,
            status=status_str,
            diagnostics=all_diagnostics,
            span_groundings=attr_result.span_mappings,
            summary=summary,
        )

    def _evaluate_balance(self, slides: List[SlideGraphNode]) -> Tuple[float, List[DiagnosticItem]]:
        diags: List[DiagnosticItem] = []
        scores: List[float] = []
        for node in slides:
            word_count = sum(len(b.split()) for b in node.content.bullets)
            bullet_count = len(node.content.bullets)
            slide_score = 100.0
            if word_count > 60:
                slide_score -= min(40.0, (word_count - 60) * 1.5)
                diags.append(DiagnosticItem(code="EVAL_HIGH_DENSITY", severity="warning", slide_index=node.index, element="content", message=f"Slide #{node.index} has high textual density ({word_count} words).", suggestion="Condense bullets."))
            if bullet_count > 5:
                slide_score -= 20.0
                diags.append(DiagnosticItem(code="EVAL_EXCESSIVE_BULLETS", severity="warning", slide_index=node.index, element="bullets", message=f"Slide #{node.index} has {bullet_count} bullets (max 5).", suggestion="Split content."))
            scores.append(max(0.0, slide_score))
        return round(sum(scores) / len(scores) if scores else 100.0, 1), diags

    def _evaluate_pacing(self, slides: List[SlideGraphNode]) -> Tuple[float, List[DiagnosticItem]]:
        diags: List[DiagnosticItem] = []
        if len(slides) < 2:
            return 90.0, diags
        word_counts = [sum(len(b.split()) for b in s.content.bullets) for s in slides]
        pacing_score = 100.0
        for i in range(1, len(slides)):
            diff = abs(word_counts[i] - word_counts[i - 1])
            if diff > 45:
                pacing_score -= 10.0
                diags.append(DiagnosticItem(code="EVAL_PACING_SPIKE", severity="info", slide_index=slides[i].index, element="pacing", message=f"Pacing spike between #{slides[i-1].index} and #{slides[i].index} ({diff} words).", suggestion="Balance content."))
        return max(50.0, round(pacing_score, 1)), diags

    def _evaluate_consistency(self, slides: List[SlideGraphNode]) -> Tuple[float, List[DiagnosticItem]]:
        diags: List[DiagnosticItem] = []
        if not slides:
            return 100.0, diags
        title_cases = [sum(1 for w in s.title.split() if w and w[0].isupper()) / max(1, len(s.title.split())) >= 0.7 for s in slides]
        majority = sum(title_cases) > (len(slides) / 2)
        inconsistent = [s.index for idx, (tc, s) in enumerate(zip(title_cases, slides)) if tc != majority and len(s.title.split()) > 2]
        if inconsistent:
            diags.append(DiagnosticItem(code="EVAL_TITLE_STYLE_DRIFT", severity="info", slide_index=inconsistent[0], element="title", message=f"Inconsistent heading capitalization on slide(s) {inconsistent}.", suggestion="Standardize title casing."))
        return max(60.0, round(100.0 - (len(inconsistent) * 8.0), 1)), diags
