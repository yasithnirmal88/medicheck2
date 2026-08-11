import api from '@/lib/api'

export const fetchProfile = async () => {
  const res = await api.get('/profiles/me')
  return res.data
}

export const fetchCompletion = async () => {
  const res = await api.get('/profiles/me/completion')
  return res.data
}

export const fetchSessions = async () => {
  const res = await api.get('/questionnaires/sessions')
  return res.data
}

export const fetchSession = async (id: string) => {
  const res = await api.get(`/questionnaires/sessions/${id}`)
  return res.data
}

export const fetchReportBySession = async (sessionId: string) => {
  const res = await api.get(`/report/${sessionId}`)
  return res.data
}

export const generateReport = async (sessionId: string) => {
  const res = await api.post('/report/generate', { session_id: sessionId })
  return res.data
}

export interface AIKeyFinding {
  title: string
  explanation: string
  source_indicator_ids: string[]
  evidence_ids?: string[]
}

export interface AIRecommendationExplanation {
  recommendation_id: string
  explanation: string
  evidence_ids?: string[]
}

export interface AIRetrievedEvidence {
  id: string
  title: string
  source?: string | null
  url?: string | null
  evidence_level?: string | null
  summary?: string | null
  excerpt?: string
  relevance?: number
  retrieval_tier?: number
  linked_entity_type?: string
  linked_entity_id?: string
}

export interface AISourceBreakdownItem {
  clinical_finding: string
  contributing_answer_refs: string[]
  knowledge_graph_relationship: string
  evidence_ids: string[]
  deterministic_score?: number | null
  trace_id?: string | null
}

export type AIQualityStatus =
  | 'valid'
  | 'fallback'
  | 'validation_failed'
  | 'provider_unavailable'
  | 'evidence_unavailable'

export type LiteracyLevel = 'simple' | 'standard' | 'detailed'

export interface AIExplanation {
  summary: string
  key_findings: AIKeyFinding[]
  severity_explanation: string
  recommendation_explanations: AIRecommendationExplanation[]
  evidence_notes: string[]
  limitations: string
  disclaimer: string
  available: boolean
  prompt_version?: string
  trace_id?: string | null
  retrieved_evidence?: AIRetrievedEvidence[]
  evidence_available?: boolean
  // Phase 7 — personalized communication + transparency + governance.
  language?: string
  literacy_level?: LiteracyLevel
  source_breakdown?: AISourceBreakdownItem[]
  transparency_notice?: string
  quality_status?: AIQualityStatus
  provider?: string
  model?: string
}

export interface ReportExplanationParams {
  language?: string
  literacy_level?: LiteracyLevel
}

export const fetchReportExplanation = async (
  sessionId: string,
  params?: ReportExplanationParams
): Promise<AIExplanation> => {
  const query = new URLSearchParams()
  if (params?.language) query.set('language', params.language)
  if (params?.literacy_level) query.set('literacy_level', params.literacy_level)
  const qs = query.toString()
  const res = await api.post(`/report/${sessionId}/explanation${qs ? `?${qs}` : ''}`)
  return res.data
}

export interface QuestionExplanation {
  question_id: string
  question_text: string
  explanation: string
  linked_indicators: { id: string; name: string; body_system_id?: string | null }[]
  linked_conditions: { id: string; name: string }[]
  evidence: {
    id: string
    title: string
    source?: string | null
    url?: string | null
    evidence_level?: string | null
  }[]
  available: boolean
  language: string
}

export const fetchQuestionExplanation = async (
  sessionId: string,
  questionId: string,
  language = 'en'
): Promise<QuestionExplanation> => {
  const res = await api.get(
    `/report/${sessionId}/question-explanation?question_id=${questionId}&language=${language}`
  )
  return res.data
}
