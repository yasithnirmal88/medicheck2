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
