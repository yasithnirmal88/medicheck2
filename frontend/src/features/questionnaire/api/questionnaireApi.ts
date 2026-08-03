import api from '@/lib/api'
import type {
  QuestionnaireTemplate,
  AssessmentSession,
  AnswerResponse,
  SaveAnswerRequest,
  SessionProgress,
  Question,
  QuestionFilters,
} from '../types'

export const fetchTemplates = async (): Promise<QuestionnaireTemplate[]> => {
  const resp = await api.get('/questionnaires')
  return resp.data
}

export const fetchTemplate = async (id: string): Promise<QuestionnaireTemplate> => {
  const resp = await api.get(`/questionnaires/${id}`)
  return resp.data
}

export const startSession = async (templateId: string): Promise<AssessmentSession> => {
  const resp = await api.post(`/questionnaires/${templateId}/start`)
  return resp.data
}

export const fetchSession = async (sessionId: string): Promise<AssessmentSession> => {
  const resp = await api.get(`/questionnaires/sessions/${sessionId}`)
  return resp.data
}

export const saveAnswer = async (
  sessionId: string,
  data: SaveAnswerRequest
): Promise<AnswerResponse> => {
  const resp = await api.post(`/questionnaires/sessions/${sessionId}/answer`, data)
  return resp.data
}

export const pauseSession = async (sessionId: string): Promise<AssessmentSession> => {
  const resp = await api.post(`/questionnaires/sessions/${sessionId}/pause`)
  return resp.data
}

export const resumeSession = async (sessionId: string): Promise<AssessmentSession> => {
  const resp = await api.post(`/questionnaires/sessions/${sessionId}/resume`)
  return resp.data
}

export const completeSession = async (sessionId: string): Promise<AssessmentSession> => {
  const resp = await api.post(`/questionnaires/sessions/${sessionId}/complete`)
  return resp.data
}

export const fetchProgress = async (sessionId: string): Promise<SessionProgress> => {
  const resp = await api.get(`/questionnaires/sessions/${sessionId}/progress`)
  return resp.data
}

export const fetchSessions = async (): Promise<AssessmentSession[]> => {
  const resp = await api.get('/questionnaires/sessions')
  return resp.data
}

export const fetchQuestions = async (params?: QuestionFilters): Promise<Question[]> => {
  const resp = await api.get('/questions', { params })
  return resp.data
}

export const searchQuestions = async (query: string): Promise<Question[]> => {
  const resp = await api.get('/questions/search', { params: { q: query } })
  return resp.data
}
