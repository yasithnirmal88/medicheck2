/**
 * Shape of the deterministic clinical report returned by
 * ``GET /report/{sessionId}`` (see backend ``HealthAssessmentModel``).
 *
 * Every field here is produced by the deterministic Clinical Decision Support
 * Engine / ReportService. The frontend must render ONLY these values and must
 * never substitute fabricated numbers.
 */
export interface ReportBodySystem {
  id: string
  body_system_id?: string | null
  category?: string | null
  /** Stored as a string float by the backend. */
  score?: string | null
  notes?: string | null
}

export interface ReportCondition {
  id: string
  condition_id?: string | null
  /** Stored as a string float by the backend. */
  score?: string | null
  /** Human label such as "Strong", "Moderate", "Weak" (or null). */
  confidence?: string | null
  notes?: string | null
}

export interface ReportAdvice {
  id: string
  recommendation_id?: string | null
  category?: string | null
  text?: string | null
}

export interface ReportLifestyle {
  id: string
  /** JSON stringified lifestyle snapshot (or null). */
  data?: string | null
}

export interface ReportDetail {
  id?: string
  session_id?: string
  user_id?: string
  summary?: string | null
  created_at?: string | null
  body_systems?: ReportBodySystem[] | null
  conditions?: ReportCondition[] | null
  advices?: ReportAdvice[] | null
  lifestyle?: ReportLifestyle[] | null
}
