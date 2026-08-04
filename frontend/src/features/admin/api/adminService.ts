import api from '../../../lib/api'

interface IndicatorPayload {
  name: string
  body_system_id: string
  description?: string
  [key: string]: unknown
}

interface EvidencePayload {
  indicator_id: string
  source: string
  citation?: string
  [key: string]: unknown
}

interface RecommendationPayload {
  name: string
  description: string
  priority: string
  [key: string]: unknown
}

interface AuditParams {
  limit: number
  entity_type?: string
}

export const listIndicators = async (bodySystemId?: string) => {
  const params = bodySystemId ? { body_system_id: bodySystemId } : {}
  const res = await api.get('/admin/indicators', { params })
  return res.data
}

export const createIndicator = async (payload: IndicatorPayload) => {
  const res = await api.post('/admin/indicators', payload)
  return res.data
}

export const listEvidence = async (limit = 50) => {
  const res = await api.get('/admin/evidence', { params: { limit } })
  return res.data
}

export const createEvidence = async (payload: EvidencePayload) => {
  const res = await api.post('/admin/evidence', payload)
  return res.data
}

export const listRecommendations = async (limit = 100) => {
  const res = await api.get('/admin/recommendations', { params: { limit } })
  return res.data
}

export const createRecommendation = async (payload: RecommendationPayload) => {
  const res = await api.post('/admin/recommendations', payload)
  return res.data
}

export const listAudit = async (entityType?: string, limit = 100) => {
  const params: AuditParams = { limit }
  if (entityType) params.entity_type = entityType
  const res = await api.get('/admin/audit', { params })
  return res.data
}
