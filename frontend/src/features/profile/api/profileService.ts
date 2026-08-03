import api from '@/lib/api'

export const fetchMyProfile = async () => {
  const resp = await api.get('/profiles/me')
  return resp.data
}

export const savePersonalInfo = async (payload: any) => {
  const resp = await api.post('/profiles/me/personal', payload)
  return resp.data
}

export const listProfileVersions = async () => {
  const resp = await api.get('/profiles/me/versions')
  return resp.data
}
