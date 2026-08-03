import api from '@/lib/api'

export const fetchReports = async (limit = 50, offset = 0) => {
  const res = await api.get('/report', { params: { limit, offset } })
  return res.data
}

export const compareReports = async (id1: string, id2: string) => {
  const res = await api.get(`/report/compare/${id1}/${id2}`)
  return res.data
}
