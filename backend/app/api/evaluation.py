import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import get_current_user, require_role, UserPrincipal
from app.core.audit import log_audit_event
from app.models.presentation import Presentation, EvaluationReport, get_presentation_or_404
from app.models.schemas import EvaluationScorecard, SlideContent, DiagnosticItem
from app.services.document_parser import DocumentParser
from app.services.evaluation_engine import EvaluationEngine

router = APIRouter(prefix="/presentations", tags=["Evaluation & Attribution Guard"])
eval_engine = EvaluationEngine()
doc_parser = DocumentParser()


@router.post("/{presentation_id}/evaluate", response_model=EvaluationScorecard)
def run_evaluation(
    presentation_id: str,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(require_role("analyst")),
):
    pres = get_presentation_or_404(db, presentation_id)
    doc_result = doc_parser.parse(pres.raw_content, fallback_title=pres.title)
    slide_nodes = pres.to_slide_nodes()
    scorecard = eval_engine.evaluate(slide_nodes, doc_result, presentation_id=pres.id)
    report = EvaluationReport(
        presentation_id=pres.id,
        overall_score=scorecard.overall_score,
        grounding_score=scorecard.grounding_score,
        balance_score=scorecard.balance_score,
        pacing_score=scorecard.pacing_score,
        consistency_score=scorecard.consistency_score,
        status=scorecard.status,
        diagnostics_json=json.dumps([d.model_dump() for d in scorecard.diagnostics], ensure_ascii=False),
    )
    db.add(report)
    pres.status = f"evaluated-{scorecard.status}"
    log_audit_event(
        db=db,
        user_id=current_user.email,
        action="EVALUATE_PRESENTATION",
        resource_type="presentation",
        resource_id=pres.id,
        details={"overall_score": scorecard.overall_score, "status": scorecard.status},
    )
    db.commit()
    db.refresh(report)
    scorecard.id = report.id
    return scorecard


@router.get("/{presentation_id}/evaluation", response_model=EvaluationScorecard)
def get_latest_evaluation(
    presentation_id: str,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
):
    pres = get_presentation_or_404(db, presentation_id)

    report = db.query(EvaluationReport).filter(EvaluationReport.presentation_id == presentation_id).order_by(desc(EvaluationReport.created_at)).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No evaluation scorecard exists for presentation '{presentation_id}'.")

    diagnostics = [DiagnosticItem.model_validate(d) for d in json.loads(report.diagnostics_json)]
    summary = f"Evaluation {report.status.upper()}: Score {report.overall_score}/100. Grounding: {report.grounding_score}%, Balance: {report.balance_score}%, Pacing: {report.pacing_score}%, Consistency: {report.consistency_score}%."

    return EvaluationScorecard(
        id=report.id,
        presentation_id=report.presentation_id,
        overall_score=report.overall_score,
        grounding_score=report.grounding_score,
        balance_score=report.balance_score,
        pacing_score=report.pacing_score,
        consistency_score=report.consistency_score,
        status=report.status,
        diagnostics=diagnostics,
        span_groundings=[],
        summary=summary,
    )
