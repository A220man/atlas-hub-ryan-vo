import base64
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role, UserPrincipal
from app.core.audit import log_audit_event
from app.models.presentation import Presentation, CustomTemplate
from app.models.schemas import TemplateTheme, CustomTemplateResponse, AdvisoryRequest, AdvisoryResponse, SlideContent
from app.services.slide_synthesizer import SlideGraphNode
from app.services.llm_advisory import LLMAdvisoryService
from app.services.pptx_compiler import PPTXCompiler
router = APIRouter(tags=['Templates & Advisory'])
llm_service = LLMAdvisoryService()
pptx_compiler = PPTXCompiler()
BUILTIN_TEMPLATES: List[TemplateTheme] = [TemplateTheme(id='modern-navy', name='Modern Navy', description='Corporate deep blue with cyan accents.', primary_color='#0E1E40', secondary_color='#0072CE', background_color='#F8F9FA', font_heading='Calibri', font_body='Calibri', aspect_ratios=['16:9', '4:3'], is_custom=False), TemplateTheme(id='emerald-clean', name='Emerald Clean', description='Contemporary emerald with amber callouts.', primary_color='#0A3D2E', secondary_color='#10956B', background_color='#F6FAF8', font_heading='Segoe UI', font_body='Segoe UI', aspect_ratios=['16:9', '4:3'], is_custom=False), TemplateTheme(id='slate-minimal', name='Slate Minimal', description='Monochrome graphite for technical briefs.', primary_color='#1E293B', secondary_color='#475569', background_color='#FFFFFF', font_heading='Arial', font_body='Arial', aspect_ratios=['16:9', '4:3'], is_custom=False)]

@router.get('/templates', response_model=List[TemplateTheme])
def list_templates(db: Session=Depends(get_db)):
    """List supported design themes and custom uploaded .pptx templates."""
    results = list(BUILTIN_TEMPLATES)
    customs = db.query(CustomTemplate).order_by(CustomTemplate.created_at.desc()).all()
    for c in customs:
        results.append(TemplateTheme(id=c.id, name=f'{c.name} (Custom)', description=c.description or f'Custom .pptx template ({c.filename})', primary_color='#1E293B', secondary_color='#2563EB', background_color='#FFFFFF', font_heading='Calibri', font_body='Calibri', aspect_ratios=[c.aspect_ratio], is_custom=True, layout_count=c.layout_count))
    return results

@router.post('/templates/upload', response_model=CustomTemplateResponse)
async def upload_custom_template(file: UploadFile=File(...), name: str=Form(None), description: str=Form(None), db: Session=Depends(get_db), current_user: UserPrincipal=Depends(require_role('analyst'))):
    """Upload and ingest a custom .pptx PowerPoint template."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail='Empty template file provided.')
    try:
        info = pptx_compiler.ingest_template(content, file.filename or 'template.pptx')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Invalid .pptx template: {str(e)}')
    tmpl_name = (name or '').strip() or (file.filename or 'Custom Template').replace('.pptx', '').replace('_', ' ').title()
    custom = CustomTemplate(name=tmpl_name, description=description or f'Custom uploaded template {file.filename}', filename=file.filename or 'template.pptx', content_b64=base64.b64encode(content).decode('ascii'), layout_count=info['layout_count'], aspect_ratio=info['aspect_ratio'], uploaded_by=current_user.email)
    db.add(custom)
    log_audit_event(db=db, user_id=current_user.email, action='UPLOAD_CUSTOM_TEMPLATE', resource_type='template', resource_id=custom.id, details={'name': custom.name, 'layout_count': custom.layout_count})
    db.commit()
    db.refresh(custom)
    return CustomTemplateResponse(id=custom.id, name=custom.name, description=custom.description, filename=custom.filename, layout_count=custom.layout_count, aspect_ratio=custom.aspect_ratio, created_at=custom.created_at)

@router.delete('/templates/{template_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_template(template_id: str, db: Session=Depends(get_db), current_user: UserPrincipal=Depends(require_role('analyst'))):
    tmpl = db.query(CustomTemplate).filter(CustomTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail=f"Custom template '{template_id}' not found.")
    db.delete(tmpl)
    db.commit()
    return None

@router.post('/presentations/{presentation_id}/advisory', response_model=AdvisoryResponse)
async def request_advisory(presentation_id: str, req: AdvisoryRequest, db: Session=Depends(get_db), current_user: UserPrincipal=Depends(require_role('analyst'))):
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Presentation '{presentation_id}' not found.")
    slide_nodes = [SlideGraphNode(index=s.slide_index, title=s.title, layout_type=s.layout_type, content=SlideContent.model_validate_json(s.content_json), speaker_notes=s.notes or '') for s in pres.slides]
    return await llm_service.get_advisory(slides=slide_nodes, query_type=req.query_type, custom_instructions=req.custom_instructions)
