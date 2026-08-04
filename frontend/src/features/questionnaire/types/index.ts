export interface BodySystem {
  id: string
  code: string
  name: string
  description: string | null
  icon: string | null
  color_hex: string | null
  is_active: boolean
}

export interface QuestionOption {
  id: string
  code: string
  text: string
  value: string
  score_value: number | null
  severity: string | null
  color_hex: string | null
  display_order: number
}

export interface ValidationRules {
  min?: number
  max?: number
  step?: number
  min_length?: number
  max_length?: number
  min_selections?: number
  max_selections?: number
  allowed_types?: string[]
  max_size_mb?: number
  past_only?: boolean
  future_only?: boolean
  unit?: string
  decimal_places?: number
  search?: boolean
}

export interface Question {
  id: string
  code: string
  text: string
  description: string | null
  tooltip: string | null
  question_type: QuestionType
  is_required: boolean
  validation_rules: ValidationRules | null
  order_index: number
  difficulty: number | null
  status: string
  body_system_id: string | null
  question_group_id: string | null
  options: QuestionOption[]
}

export type QuestionType =
  | 'single_choice'
  | 'multiple_choice'
  | 'yes_no'
  | 'numeric'
  | 'decimal'
  | 'slider'
  | 'date'
  | 'time'
  | 'dropdown'
  | 'multi_select'
  | 'free_text'
  | 'search'
  | 'file_upload'

export interface QuestionGroup {
  id: string
  code: string
  name: string
  description: string | null
  display_order: number
}

export interface QuestionnaireTemplate {
  id: string
  code: string
  name: string
  description: string | null
  estimated_time_minutes: number | null
  is_active: boolean
  body_system_id: string | null
  target_audience: string | null
}

export interface SessionProgress {
  current_section: string | null
  completed_questions: number
  total_questions: number
  answered_questions: number
  skipped_questions: number
  completion_percentage: number
  estimated_time_remaining: number | null
}

export interface AssessmentSession {
  id: string
  status: 'in_progress' | 'paused' | 'completed' | 'cancelled'
  current_question: Question | null
  progress: SessionProgress
  questionnaire_template_id: string
  created_at: string
  updated_at: string
}

export interface SaveAnswerRequest {
  question_id: string
  response_value: Record<string, unknown>
  time_taken_seconds?: number
}

export interface AnswerResponse {
  next_question: Question | null
  is_complete: boolean
  session_id: string
}

export interface QuestionFilters {
  body_system_id?: string
  question_group_id?: string
  difficulty?: number
  status?: string
  question_type?: QuestionType
  page?: number
  per_page?: number
}
