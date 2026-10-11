import datetime
from typing import List, Optional, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class UserPrincipal(BaseModel):
    """Authenticated user context extracted from validated bearer token."""
    sub: str
    email: str
    name: str = ""
    roles: List[str] = Field(default_factory=list)

    def has_role(self, role: str) -> bool:
        if "admin" in self.roles:
            return True
        return role in self.roles


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    user: UserPrincipal


class SlideContent(BaseModel):
    header: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)
    callout: Optional[str] = None
    metric_label: Optional[str] = None
    metric_value: Optional[str] = None
    chart_series: Optional[List[Dict[str, Any]]] = None
    table_columns: Optional[List[str]] = None
    table_rows: Optional[List[List[str]]] = None
    transition: Optional[str] = "fade"
    animation_type: Optional[str] = "appear"


class SlideSchema(BaseModel):
    id: Optional[str] = None
    slide_index: int
    title: str
    layout_type: str
    content: SlideContent
    notes: Optional[str] = None
    created_at: Optional[datetime.datetime] = None


class PresentationCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    topic: Optional[str] = Field(None, max_length=255)
    raw_content: str = Field(..., min_length=10)
    template_id: str = Field(default="modern-navy")
    aspect_ratio: str = Field(default="16:9")


class PresentationUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    template_id: Optional[str] = None
    aspect_ratio: Optional[str] = None


class PresentationSummaryResponse(BaseModel):
    id: str
    title: str
    topic: Optional[str] = None
    template_id: str
    status: str
    aspect_ratio: str
    slide_count: int
    created_by: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class PresentationDetailResponse(BaseModel):
    id: str
    title: str
    topic: Optional[str] = None
    raw_content: str
    template_id: str
    status: str
    aspect_ratio: str
    created_by: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    slides: List[SlideSchema] = Field(default_factory=list)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    total_pages: int


class DiagnosticItem(BaseModel):
    code: str
    severity: str  # "error", "warning", "info"
    message: str
    slide_index: Optional[int] = None
    element: Optional[str] = None
    suggestion: Optional[str] = None


class SpanGrounding(BaseModel):
    slide_index: int
    claim: str
    matched_source_span: Optional[str] = None
    grounding_confidence: float
    is_grounded: bool


class EvaluationScorecard(BaseModel):
    id: Optional[str] = None
    presentation_id: str
    overall_score: float
    grounding_score: float
    balance_score: float
    pacing_score: float
    consistency_score: float
    status: str
    diagnostics: List[DiagnosticItem] = Field(default_factory=list)
    span_groundings: List[SpanGrounding] = Field(default_factory=list)
    summary: str


class NarrationCue(BaseModel):
    slide_index: int
    slide_title: str
    start_time_seconds: float
    duration_seconds: float
    speech_text: str
    pause_after_seconds: float = 0.5


class NarrationPlanResponse(BaseModel):
    id: Optional[str] = None
    presentation_id: str
    total_duration_seconds: float
    estimated_words: int
    voice_id: str
    target_wpm: int
    cues: List[NarrationCue]


class TemplateTheme(BaseModel):
    id: str
    name: str
    description: str
    primary_color: str
    secondary_color: str
    background_color: str
    font_heading: str
    font_body: str
    aspect_ratios: List[str]
    is_custom: bool = False
    layout_count: Optional[int] = None


class CustomTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    filename: str
    layout_count: int
    aspect_ratio: str
    created_at: datetime.datetime


class AdvisoryRequest(BaseModel):
    query_type: str = Field(default="executive_review")
    custom_instructions: Optional[str] = None


class AdvisoryResponse(BaseModel):
    provider: str
    model: str
    advice: str
    grounded_references: List[str]
    is_advisory: bool = True
