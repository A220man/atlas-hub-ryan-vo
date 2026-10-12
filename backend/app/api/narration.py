import json
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user, require_role, UserPrincipal
from app.core.audit import log_audit_event
from app.models.presentation import Presentation, NarrationPlan, get_presentation_or_404
from app.models.schemas import NarrationPlanResponse, NarrationCue, SlideContent
from app.services.narration_service import NarrationService

router = APIRouter(prefix="/presentations", tags=["Narration & Audio Planning"])
narration_service = NarrationService()


class GenerateNarrationRequest(BaseModel):
    voice_id: str = Field(default="neutral-presenter")
    target_wpm: int = Field(default=140, ge=80, le=240)


def _get_pres_and_plan(presentation_id: str, db: Session):
    pres = get_presentation_or_404(db, presentation_id)
    plan = db.query(NarrationPlan).filter(NarrationPlan.presentation_id == presentation_id).order_by(desc(NarrationPlan.created_at)).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"No narration plan exists for presentation '{presentation_id}'.")
    return pres, plan


@router.post("/{presentation_id}/narration", response_model=NarrationPlanResponse)
def generate_narration_plan(
    presentation_id: str,
    req: GenerateNarrationRequest,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(require_role("analyst")),
):
    pres = get_presentation_or_404(db, presentation_id)
    slide_nodes = pres.to_slide_nodes()

    plan_resp = narration_service.generate_plan(slides=slide_nodes, presentation_id=pres.id, voice_id=req.voice_id, target_wpm=req.target_wpm)
    plan = NarrationPlan(
        presentation_id=pres.id,
        total_duration_seconds=plan_resp.total_duration_seconds,
        estimated_words=plan_resp.estimated_words,
        voice_id=req.voice_id,
        target_wpm=plan_resp.target_wpm,
        cues_json=json.dumps([c.model_dump() for c in plan_resp.cues], ensure_ascii=False),
    )
    db.add(plan)
    log_audit_event(db=db, user_id=current_user.email, action="GENERATE_NARRATION_PLAN", resource_type="presentation", resource_id=pres.id, details={"duration_seconds": plan_resp.total_duration_seconds, "voice_id": req.voice_id})
    db.commit()
    db.refresh(plan)
    plan_resp.id = plan.id
    return plan_resp


@router.get("/{presentation_id}/narration", response_model=NarrationPlanResponse)
def get_narration_plan(
    presentation_id: str,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
):
    _, plan = _get_pres_and_plan(presentation_id, db)
    cues = [NarrationCue.model_validate(c) for c in json.loads(plan.cues_json)]
    return NarrationPlanResponse(
        id=plan.id,
        presentation_id=plan.presentation_id,
        total_duration_seconds=plan.total_duration_seconds,
        estimated_words=plan.estimated_words,
        voice_id=plan.voice_id,
        target_wpm=plan.target_wpm,
        cues=cues,
    )


@router.get("/{presentation_id}/narration/vtt")
def export_narration_vtt(
    presentation_id: str,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
):
    pres, plan = _get_pres_and_plan(presentation_id, db)
    cues = [NarrationCue.model_validate(c) for c in json.loads(plan.cues_json)]
    filename = f"{pres.title.lower().replace(' ', '_')[:32]}_narration.vtt"
    return Response(content=narration_service.export_webvtt(cues), media_type="text/vtt", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/{presentation_id}/narration/audio")
def export_narration_audio(
    presentation_id: str,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
):
    pres, plan = _get_pres_and_plan(presentation_id, db)
    cues = [NarrationCue.model_validate(c) for c in json.loads(plan.cues_json)]
    audio_bytes = narration_service.synthesize_audio(cues, voice_id=plan.voice_id)
    filename = f"{pres.title.lower().replace(' ', '_')[:32]}_narration.wav"
    return Response(content=audio_bytes, media_type="audio/wav", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/{presentation_id}/narration/slides/{slide_index}/audio")
def export_slide_audio(
    presentation_id: str,
    slide_index: int,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(get_current_user),
):
    _, plan = _get_pres_and_plan(presentation_id, db)
    cues = [NarrationCue.model_validate(c) for c in json.loads(plan.cues_json)]
    matching = [c for c in cues if c.slide_index == slide_index]
    if not matching:
        raise HTTPException(status_code=404, detail=f"No cue found for slide {slide_index}")
    audio_bytes = narration_service.synthesize_slide_audio(matching[0], voice_id=plan.voice_id)
    return Response(content=audio_bytes, media_type="audio/wav", headers={"Content-Disposition": f'inline; filename="slide_{slide_index}.wav"'})
