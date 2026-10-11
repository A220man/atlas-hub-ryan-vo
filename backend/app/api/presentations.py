import math
import base64
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.core.security import get_current_user, require_role, UserPrincipal
from app.core.audit import log_audit_event
from app.models.presentation import Presentation, Slide, CustomTemplate
from app.models.schemas import PresentationCreateRequest, PresentationUpdateRequest, PresentationSummaryResponse, PresentationDetailResponse, SlideSchema, SlideContent, PaginatedResponse
from app.services.document_parser import DocumentParser
from app.services.slide_synthesizer import SlideSynthesizer, SlideGraphNode
from app.services.pptx_compiler import PPTXCompiler
router = APIRouter(prefix='/presentations', tags=['Presentations'])
document_parser = DocumentParser()
slide_synthesizer = SlideSynthesizer()
pptx_compiler = PPTXCompiler()

def _format_detail(pres: Presentation) -> PresentationDetailResponse:
    slides_resp = [SlideSchema(id=s.id, slide_index=s.slide_index, title=s.title, layout_type=s.layout_type, content=SlideContent.model_validate_json(s.content_json), notes=s.notes, created_at=s.created_at) for s in pres.slides]
    return PresentationDetailResponse(id=pres.id, title=pres.title, topic=pres.topic, raw_content=pres.raw_content, template_id=pres.template_id, status=pres.status, aspect_ratio=pres.aspect_ratio, created_by=pres.created_by, created_at=pres.created_at, updated_at=pres.updated_at, slides=slides_resp)

def _format_summary(p: Presentation) -> PresentationSummaryResponse:
    return PresentationSummaryResponse(id=p.id, title=p.title, topic=p.topic, template_id=p.template_id, status=p.status, aspect_ratio=p.aspect_ratio, slide_count=len(p.slides), created_by=p.created_by, created_at=p.created_at, updated_at=p.updated_at)

@router.post('', response_model=PresentationDetailResponse, status_code=status.HTTP_201_CREATED)
def create_presentation(req: PresentationCreateRequest, db: Session=Depends(get_db), current_user: UserPrincipal=Depends(require_role('analyst'))):
    doc_result = document_parser.parse(req.raw_content, fallback_title=req.title)
    slide_nodes = slide_synthesizer.synthesize(doc_result, template_id=req.template_id)
    pres = Presentation(title=req.title, topic=req.topic or doc_result.document_title, raw_content=req.raw_content, template_id=req.template_id, status='synthesized', aspect_ratio=req.aspect_ratio, created_by=current_user.email)
    db.add(pres)
    db.flush()
    for node in slide_nodes:
        db.add(Slide(presentation_id=pres.id, slide_index=node.index, title=node.title, layout_type=node.layout_type, content_json=node.content.model_dump_json(), notes=node.speaker_notes))
    log_audit_event(db=db, user_id=current_user.email, action='CREATE_PRESENTATION', resource_type='presentation', resource_id=pres.id, details={'slides_count': len(slide_nodes), 'title': req.title})
    db.commit()
    db.refresh(pres)
    return _format_detail(pres)

@router.get('', response_model=PaginatedResponse[PresentationSummaryResponse])
def list_presentations(page: int=Query(default=1, ge=1), size: int=Query(default=10, ge=1, le=100), topic: Optional[str]=Query(default=None), search: Optional[str]=Query(default=None), db: Session=Depends(get_db), current_user: UserPrincipal=Depends(get_current_user)):
    query = db.query(Presentation)
    if topic:
        query = query.filter(Presentation.topic.ilike(f'%{topic}%'))
    if search:
        query = query.filter(Presentation.title.ilike(f'%{search}%'))
    total = query.count()
    total_pages = math.ceil(total / size) if total > 0 else 1
    records = query.order_by(desc(Presentation.created_at)).offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(items=[_format_summary(p) for p in records], total=total, page=page, size=size, total_pages=total_pages)

@router.get('/{presentation_id}', response_model=PresentationDetailResponse)
def get_presentation(presentation_id: str, db: Session=Depends(get_db), current_user: UserPrincipal=Depends(get_current_user)):
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=404, detail=f"Presentation '{presentation_id}' not found.")
    return _format_detail(pres)

@router.put('/{presentation_id}', response_model=PresentationSummaryResponse)
def update_presentation(presentation_id: str, req: PresentationUpdateRequest, db: Session=Depends(get_db), current_user: UserPrincipal=Depends(require_role('analyst'))):
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=404, detail=f"Presentation '{presentation_id}' not found.")
    if req.title:
        pres.title = req.title
    if req.template_id:
        pres.template_id = req.template_id
    if req.aspect_ratio:
        pres.aspect_ratio = req.aspect_ratio
    log_audit_event(db=db, user_id=current_user.email, action='UPDATE_PRESENTATION', resource_type='presentation', resource_id=pres.id, details={'updated_fields': req.model_dump(exclude_unset=True)})
    db.commit()
    db.refresh(pres)
    return _format_summary(pres)

@router.delete('/{presentation_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_presentation(presentation_id: str, db: Session=Depends(get_db), current_user: UserPrincipal=Depends(require_role('analyst'))):
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=404, detail=f"Presentation '{presentation_id}' not found.")
    log_audit_event(db=db, user_id=current_user.email, action='DELETE_PRESENTATION', resource_type='presentation', resource_id=pres.id, details={'title': pres.title})
    db.delete(pres)
    db.commit()
    return None

@router.get('/{presentation_id}/export/pptx')
def export_pptx(presentation_id: str, db: Session=Depends(get_db), current_user: UserPrincipal=Depends(get_current_user)):
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=404, detail=f"Presentation '{presentation_id}' not found.")
    slide_nodes = [SlideGraphNode(index=s.slide_index, title=s.title, layout_type=s.layout_type, content=SlideContent.model_validate_json(s.content_json), speaker_notes=s.notes or '') for s in pres.slides]
    custom_tmpl = db.query(CustomTemplate).filter(CustomTemplate.id == pres.template_id).first()
    custom_bytes = base64.b64decode(custom_tmpl.content_b64) if custom_tmpl else None
    pptx_bytes = pptx_compiler.compile(slide_nodes, template_id=pres.template_id, aspect_ratio=pres.aspect_ratio, custom_template_bytes=custom_bytes)
    filename = f'{pres.title.lower().replace(' ', '_')[:32]}.pptx'
    return Response(content=pptx_bytes, media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation', headers={'Content-Disposition': f'attachment; filename="{filename}"'})
