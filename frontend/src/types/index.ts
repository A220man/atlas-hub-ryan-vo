export interface UserPrincipal {
  sub: string;
  email: string;
  name: string;
  roles: string[];
}

export interface SlideContent {
  header?: string;
  bullets: string[];
  callout?: string;
  metric_label?: string;
  metric_value?: string;
  chart_series?: Array<{ category: string; value: number }>;
  table_columns?: string[];
  table_rows?: string[][];
  transition?: string;
  animation_type?: string;
}

export interface Slide {
  id?: string;
  slide_index: number;
  title: string;
  layout_type: string;
  content: SlideContent;
  notes?: string;
  created_at?: string;
}

export interface PresentationSummary {
  id: string;
  title: string;
  topic?: string;
  template_id: string;
  status: string;
  aspect_ratio: string;
  slide_count: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface PresentationDetail {
  id: string;
  title: string;
  topic?: string;
  raw_content: string;
  template_id: string;
  status: string;
  aspect_ratio: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  slides: Slide[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}

export interface DiagnosticItem {
  code: string;
  severity: "error" | "warning" | "info";
  message: string;
  slide_index?: number;
  element?: string;
  suggestion?: string;
}

export interface SpanGrounding {
  slide_index: number;
  claim: string;
  matched_source_span?: string;
  grounding_confidence: number;
  is_grounded: boolean;
}

export interface EvaluationScorecard {
  id?: string;
  presentation_id: string;
  overall_score: number;
  grounding_score: number;
  balance_score: number;
  pacing_score: number;
  consistency_score: number;
  status: string;
  diagnostics: DiagnosticItem[];
  span_groundings: SpanGrounding[];
  summary: string;
}

export interface NarrationCue {
  slide_index: number;
  slide_title: string;
  start_time_seconds: number;
  duration_seconds: number;
  speech_text: string;
  pause_after_seconds: number;
}

export interface NarrationPlan {
  id?: string;
  presentation_id: string;
  total_duration_seconds: number;
  estimated_words: number;
  voice_id: string;
  target_wpm: number;
  cues: NarrationCue[];
}

export interface TemplateTheme {
  id: string;
  name: string;
  description: string;
  primary_color: string;
  secondary_color: string;
  background_color: string;
  font_heading: string;
  font_body: string;
  aspect_ratios: string[];
}

export interface AdvisoryResponse {
  provider: string;
  model: string;
  advice: string;
  grounded_references: string[];
  is_advisory: boolean;
}
