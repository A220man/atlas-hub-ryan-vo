from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role, UserPrincipal
from app.models.presentation import Presentation, Slide, get_presentation_or_404
from app.models.schemas import AdvisoryRequest, AdvisoryResponse
from app.services.slide_synthesizer import SlideGraphNode
from app.services.llm_advisory import LLMAdvisoryService

router = APIRouter(prefix="/presentations", tags=["AI Advisory"])
advisory_service = LLMAdvisoryService()


def _get_slide_nodes(presentation: Presentation) -> list[SlideGraphNode]:
    """Convert DB slides to SlideGraphNode for advisory service."""
    return [
        SlideGraphNode(
            index=s.slide_index,
            title=s.title,
            layout_type=s.layout_type,
            content=None,  # Advisory doesn't need full content
            speaker_notes=s.notes,
        )
        for s in sorted(presentation.slides, key=lambda s: s.slide_index)
    ]


@router.post("/{presentation_id}/advisory", response_model=AdvisoryResponse)
async def request_advisory(
    presentation_id: str,
    request: AdvisoryRequest,
    db: Session = Depends(get_db),
    current_user: UserPrincipal = Depends(require_role("analyst")),
):
    """Generate strategic advisory analysis for a presentation."""
    pres = get_presentation_or_404(db, presentation_id)
    slide_nodes = _get_slide_nodes(pres)

    if not slide_nodes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Presentation has no slides to analyze",
        )

    result = await advisory_service.get_advisory(
        slides=slide_nodes,
        query_type=request.query_type,
        custom_instructions=request.custom_instructions,
    )
    return result

