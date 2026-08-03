export type SectionKey =
  | 'personal_info'
  | 'lifestyle'
  | 'nutrition'
  | 'medical_history'
  | 'medications'
  | 'surgeries'
  | 'family_history'
  | 'allergies'
  | 'immunizations'
  | 'measurements'
  | 'lab_reports'

export interface ProfileCompletion {
  overall: number
  completed: number
  total: number
  sections: Record<SectionKey, boolean>
}

export interface PersonalInfo {
  full_name?: string
  date_of_birth?: string
  sex?: string
  height_cm?: number
  weight_kg?: number
  blood_group?: string
  nationality?: string
  country?: string
  state?: string
  city?: string
  preferred_language?: string
  emergency_contact?: string
  occupation?: string
  industry?: string
  education_level?: string
  marital_status?: string
  children_count?: number
}

export interface Profile {
  id: string
  user_id: string
  draft: boolean
  metadata?: Record<string, unknown> | null
  personal_info?: PersonalInfo
  created_at: string
  updated_at: string
}

export type SessionStatus = 'in_progress' | 'paused' | 'completed' | 'cancelled'

export interface SessionProgress {
  session_id: string
  current_section?: string
  completed_questions: number
  total_questions: number
  answered_questions: number
  skipped_questions: number
  estimated_time_remaining?: number
  completion_percentage: number
}

export interface QuestionnaireSession {
  id: string
  status: SessionStatus
  questionnaire_template_id?: string
  current_question?: unknown
  progress?: SessionProgress | null
  started_at?: string
  completed_at?: string
  created_at?: string
  updated_at?: string
}

export type RiskCategory =
  | 'Normal'
  | 'Monitor'
  | 'Needs Attention'
  | 'Recommend Screening'
  | 'Urgent Medical Review'

export interface BodySystemAssessment {
  id: string
  assessment_id: string
  body_system_id: string
  category: RiskCategory
  score?: string
  notes?: string
  created_at?: string
}

export interface GeneratedAdvice {
  id: string
  assessment_id: string
  recommendation_id?: string
  category?: string
  text: string
  created_at?: string
}

export interface HealthReport {
  id: string
  session_id: string
  user_id: string
  summary?: string
  created_at: string
  body_systems?: BodySystemAssessment[]
  advices?: GeneratedAdvice[]
}

export type MeasurementType = 'weight' | 'blood_pressure' | 'heart_rate' | string

export interface Measurement {
  id: string
  profile_id: string
  type: MeasurementType
  value: number | string
  unit?: string
  recorded_at: string
  notes?: string
}

export interface LabReport {
  id: string
  profile_id?: string
  test_name: string
  value?: number
  unit?: string
  reference_range?: string
  laboratory?: string
  date?: string
  notes?: string
  created_at?: string
  deleted_at?: string
}

export interface GeneratedRecommendation {
  id: string
  recommendation_id?: string
  source?: string
  notes?: string
  created_at?: string
}

export interface GeneratedScreening {
  id: string
  name: string
  reason?: string
  created_at?: string
}

export interface GeneratedLabTest {
  id: string
  laboratory_test_id: string
  reason?: string
  created_at?: string
}

export interface AssessmentResult {
  id: string
  session_id?: string
  user_id?: string
  summary?: string
  confidence_score?: number
  created_at?: string
  generated_recommendations?: GeneratedRecommendation[]
  generated_screenings?: GeneratedScreening[]
  generated_laboratory_tests?: GeneratedLabTest[]
  explanations?: { text?: string }[]
}

export interface QuestionnaireTemplate {
  id: string
  title?: string
  name?: string
  description?: string
}