import api from '@/lib/api'
import type {
  AIExplanationResponse,
  AIQualityStatus,
  KeyFinding,
  LiteracyLevel,
  RecommendationExplanation,
  RetrievedEvidenceContext,
  SourceBreakdownItem,
} from '@/api'

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

// ---- AI explanation types (Phase 1/2/7) ----
//
// These now alias the generated models from the backend OpenAPI schema rather
// than duplicating them by hand, which is what let the hand-written copies drift
// (e.g. the old `AIRetrievedEvidence` was missing `publication_year`).
//
// The local names are kept so existing components keep importing unchanged.
export type AIKeyFinding = KeyFinding
export type AIRecommendationExplanation = RecommendationExplanation
export type AIRetrievedEvidence = RetrievedEvidenceContext
export type AISourceBreakdownItem = SourceBreakdownItem
export type AIExplanation = AIExplanationResponse
export type { AIQualityStatus, LiteracyLevel }

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
