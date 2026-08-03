import api from '../../../lib/api'

export const listIndicators = async (bodySystemId?: string) => {
  const params = bodySystemId ? { body_system_id: bodySystemId } : {}
  const res = await api.get('/admin/indicators', { params })
  return res.data
}

export const createIndicator = async (payload: any) => {
  const res = await api.post('/admin/indicators', payload)
  return res.data
}

export const listEvidence = async (limit = 50) => {
  const res = await api.get('/admin/evidence', { params: { limit } })
  return res.data
}

export const createEvidence = async (payload: any) => {
  const res = await api.post('/admin/evidence', payload)
  return res.data
}

export const listRecommendations = async (limit = 100) => {
  const res = await api.get('/admin/recommendations', { params: { limit } })
  return res.data
}

export const createRecommendation = async (payload: any) => {
  const res = await api.post('/admin/recommendations', payload)
  return res.data
}

export const listAudit = async (entityType?: string, limit = 100) => {
  const params: any = { limit }
  if (entityType) params.entity_type = entityType
  const res = await api.get('/admin/audit', { params })
  return res.data
}
