import api from '@/lib/api'
import type {
  HealthReport,
  LabReport,
  Measurement,
  Profile,
  ProfileCompletion,
  QuestionnaireSession,
} from '../types'

export async function fetchProfile(): Promise<Profile> {
  const { data } = await api.get<Profile>('/profiles/me')
  return data
}

export async function fetchCompletion(): Promise<ProfileCompletion> {
  const { data } = await api.get<ProfileCompletion>('/profiles/me/completion')
  return data
}

export async function fetchSessions(): Promise<QuestionnaireSession[]> {
  const { data } = await api.get<QuestionnaireSession[]>('/questionnaires/sessions')
  return data
}

export async function fetchReports(limit = 25): Promise<HealthReport[]> {
  // Backend route is GET /report/ (trailing slash); using the exact path avoids
  // a 307 redirect round-trip on every dashboard load.
  const { data } = await api.get<HealthReport[]>('/report/', { params: { limit } })
  return data
}

export async function fetchReportBySession(sessionId: string): Promise<HealthReport> {
  const { data } = await api.get<HealthReport>(`/report/${sessionId}`)
  return data
}

export async function fetchMeasurements(): Promise<Measurement[]> {
  const { data } = await api.get<Measurement[]>('/profiles/me/measurements')
  return data
}

export async function fetchLabReports(): Promise<LabReport[]> {
  const { data } = await api.get<LabReport[]>('/profiles/me/lab-reports')
  return data
}