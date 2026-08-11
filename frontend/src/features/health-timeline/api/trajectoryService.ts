import api from '@/lib/api'

// ---- Deterministic trajectory types (mirror backend DTOs) ----

export interface BodySystemPoint {
  body_system_id: string | null
  name: string | null
  score: number | null
  category: string | null
}

export interface LongitudinalAssessmentPoint {
  assessment_id: string
  session_id: string
  trace_id: string | null
  completed_at: string | null
  overall_severity: string | null
  body_systems: BodySystemPoint[]
  activated_indicators: string[]
  possible_conditions: string[]
  recommendations: string[]
}

export interface ChangeEvent {
  scope: string
  ref_id: string | null
  label: string | null
  previous_value: string | null
  current_value: string | null
  previous_score: number | null
  current_score: number | null
  delta: number | null
  trend: string
}

export interface IndicatorChanges {
  new: string[]
  resolved: string[]
  persistent: string[]
}

export interface ConditionChanges {
  new: string[]
  removed: string[]
  persistent: string[]
}

export interface RecommendationChanges {
  new: string[]
  removed: string[]
  persistent: string[]
}

export interface TrajectoryComparison {
  previous: LongitudinalAssessmentPoint
  current: LongitudinalAssessmentPoint
  overall_change: ChangeEvent | null
  body_system_changes: ChangeEvent[]
  indicator_changes: IndicatorChanges
  condition_changes: ConditionChanges
  recommendation_changes: RecommendationChanges
  change_events: ChangeEvent[]
}

export interface HealthTrajectory {
  assessments: LongitudinalAssessmentPoint[]
  comparisons: TrajectoryComparison[]
  sufficient_data: boolean
  summary: string
}

// ---- AI explanation types ----

export interface TrajectoryFinding {
  label: string
  ref_id: string | null
  ref_type: string | null
  explanation: string
  evidence_ids: string[]
}

export interface RetrievedEvidence {
  id: string
  title: string
  source: string | null
  url: string | null
  evidence_level: string | null
  summary: string | null
  [key: string]: unknown
}

export interface LongitudinalExplanation {
  available: boolean
  summary: string
  key_changes: TrajectoryFinding[]
  persistent_findings: TrajectoryFinding[]
  new_findings: TrajectoryFinding[]
  improved_findings: TrajectoryFinding[]
  stable_findings: TrajectoryFinding[]
  important_context: string[]
  evidence_ids: string[]
  prompt_version: string
  trace_ids: string[]
  retrieved_evidence: RetrievedEvidence[]
  evidence_available: boolean
  disclaimer: string
}

export interface ExplanationRequest {
  previous_session_id?: string
  current_session_id?: string
}

export const fetchTrajectory = async (limit = 20): Promise<HealthTrajectory> => {
  const res = await api.get('/trajectory', { params: { limit } })
  return res.data
}

export const fetchTrajectoryExplanation = async (
  req: ExplanationRequest = {}
): Promise<LongitudinalExplanation> => {
  const res = await api.post('/trajectory/explanation', req)
  return res.data
}
