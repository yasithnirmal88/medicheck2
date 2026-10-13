/**
 * Phase 11 — Governed AI Care Coordination & Equity Intelligence.
 *
 * API layer for AI-assisted CHW operational suggestions, equity intelligence,
 * SDG narratives, and the human-review workflow.
 *
 * INVARIANT: AI is an operational/explanation layer ONLY. It never determines
 * clinical priority, severity, probability, urgency, or diagnosis. All
 * population outputs are de-identified + k-anonymity-suppressed. AI never
 * self-publishes — only a human reviewer may approve/reject/edit/publish.
 */
import api from '@/lib/api'

// ── Operational CHW suggestions ───────────────────────────────────────

export type OperationalReasonCode =
  | 'overdue'
  | 'missing_follow_up'
  | 'aged_referral'
  | 'appointment_window'
  | 'unresolved_admin'
  | 'unsuccessful_contact'
  | 'facility_unresponsive'
  | 'offline_pending_sync'
  | 'no_outstanding_flags'

export type ReviewStatus =
  | 'generated'
  | 'pending_review'
  | 'approved'
  | 'rejected'
  | 'edited'
  | 'published'

export type InsightQualityStatus =
  | 'valid'
  | 'insufficient_data'
  | 'validation_failed'
  | 'provider_unavailable'
  | 'review_required'
  | 'rejected'

export interface OperationalSuggestion {
  task_id: string
  operational_reason_codes: OperationalReasonCode[]
  explanation: string
  operational_priority_score: number
  confidence: number
  requires_human_review: boolean
}

export interface OperationalSuggestionRecord {
  id: string
  chw_user_id: string
  task_id: string
  operational_reason_codes: string[]
  explanation: string
  operational_priority_score: number
  requires_human_review: boolean
  provider: string
  model: string
  prompt_version: string
  quality_status: string
  quality_reason: string | null
  review_status: ReviewStatus
  reviewer_id: string | null
  reviewer_comment: string | null
  edited_output: string | null
  approved_at: string | null
  created_at: string | null
}

export interface OperationalSuggestionBatchResponse {
  available: boolean
  suggestions: OperationalSuggestion[]
  provider: string
  model: string
  prompt_version: string
  quality_status: InsightQualityStatus
  quality_reason: string | null
  transparency_notice: string
  records: OperationalSuggestionRecord[]
}

export const generateOperationalSuggestions =
  async (): Promise<OperationalSuggestionBatchResponse> => {
    const { data } = await api.post<OperationalSuggestionBatchResponse>(
      '/ai-care-coordination/suggestions'
    )
    return data
  }

export const fetchOperationalSuggestions =
  async (): Promise<OperationalSuggestionRecord[]> => {
    const { data } = await api.get<OperationalSuggestionRecord[]>(
      '/ai-care-coordination/suggestions'
    )
    return data
  }

// ── Equity intelligence ───────────────────────────────────────────────

export interface EquityFinding {
  statement: string
  metric_labels: string[]
}

export interface EquityInterpretation {
  interpretation: string
  is_observed: boolean
}

export interface EquityInsightOutput {
  observed_findings: EquityFinding[]
  possible_interpretations: EquityInterpretation[]
  limitations: string
  requires_human_review: boolean
}

export interface PopulationInsightRecord {
  id: string
  insight_type: 'equity' | 'sdg_narrative'
  target: string | null
  period_start: string | null
  period_end: string | null
  narrative: string
  observed_findings: unknown[] | null
  possible_interpretations: unknown[] | null
  limitations: string | null
  requires_human_review: boolean
  provider: string
  model: string
  prompt_version: string
  quality_status: string
  quality_reason: string | null
  review_status: ReviewStatus
  reviewer_id: string | null
  reviewer_comment: string | null
  edited_output: string | null
  approved_at: string | null
  created_at: string | null
}

export interface EquityInsightResponse {
  available: boolean
  insight: EquityInsightOutput | null
  record: PopulationInsightRecord | null
  provider: string
  prompt_version: string
  quality_status: InsightQualityStatus
  quality_reason: string | null
  transparency_notice: string
}

export interface EquityInsightParams {
  start_date?: string
  end_date?: string
}

export const generateEquityInsight = async (
  params?: EquityInsightParams
): Promise<EquityInsightResponse> => {
  const { data } = await api.post<EquityInsightResponse>(
    '/ai-equity/equity-insight',
    null,
    { params }
  )
  return data
}

export const fetchEquityInsights =
  async (): Promise<PopulationInsightRecord[]> => {
    const { data } = await api.get<PopulationInsightRecord[]>(
      '/ai-equity/equity-insight'
    )
    return data
  }

// ── SDG narratives ────────────────────────────────────────────────────

export interface SdgNarrativeOutput {
  target: string
  reporting_period: string | null
  population_scope: string
  metrics_used: string[]
  observed_trends: string[]
  limitations: string
  possible_operational_interpretation: string
  requires_human_review: boolean
}

export interface SdgNarrativeResponse {
  available: boolean
  narratives: SdgNarrativeOutput[]
  records: PopulationInsightRecord[]
  provider: string
  prompt_version: string
  quality_status: InsightQualityStatus
  quality_reason: string | null
  transparency_notice: string
}

export const generateSdgNarratives = async (
  params?: EquityInsightParams
): Promise<SdgNarrativeResponse> => {
  const { data } = await api.post<SdgNarrativeResponse>(
    '/ai-equity/sdg-narratives',
    null,
    { params }
  )
  return data
}

export const fetchSdgNarratives =
  async (): Promise<PopulationInsightRecord[]> => {
    const { data } = await api.get<PopulationInsightRecord[]>(
      '/ai-equity/sdg-narratives'
    )
    return data
  }

// ── Human review workflow ─────────────────────────────────────────────

export type ReviewAction = 'approve' | 'reject' | 'edit'

export interface ReviewRequest {
  action: ReviewAction
  reviewer_comment?: string
  edited_output?: string
}

export interface InsightReviewResponse {
  id: string
  insight_type: 'operational' | 'equity' | 'sdg_narrative'
  review_status: ReviewStatus
  reviewer_id: string
  reviewer_comment: string | null
  edited_output: string | null
  approved_at: string | null
}

export const reviewOperationalSuggestion = async (
  suggestionId: string,
  req: ReviewRequest
): Promise<InsightReviewResponse> => {
  const { data } = await api.post<InsightReviewResponse>(
    `/ai-equity/review/operational/${suggestionId}`,
    req
  )
  return data
}

export const publishOperationalSuggestion = async (
  suggestionId: string
): Promise<InsightReviewResponse> => {
  const { data } = await api.post<InsightReviewResponse>(
    `/ai-equity/review/operational/${suggestionId}/publish`
  )
  return data
}

export const reviewPopulationInsight = async (
  insightId: string,
  req: ReviewRequest
): Promise<InsightReviewResponse> => {
  const { data } = await api.post<InsightReviewResponse>(
    `/ai-equity/review/population/${insightId}`,
    req
  )
  return data
}

export const publishPopulationInsight = async (
  insightId: string
): Promise<InsightReviewResponse> => {
  const { data } = await api.post<InsightReviewResponse>(
    `/ai-equity/review/population/${insightId}/publish`
  )
  return data
}
