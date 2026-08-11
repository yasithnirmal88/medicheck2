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
}

export const fetchReportExplanation = async (
  sessionId: string
): Promise<AIExplanation> => {
  const res = await api.post(`/report/${sessionId}/explanation`)
  return res.data
}
