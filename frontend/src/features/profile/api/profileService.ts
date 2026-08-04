import api from '@/lib/api'

interface PersonalInfoPayload {
  full_name?: string
  date_of_birth?: string
  gender?: string
  phone?: string
  address?: string
  emergency_contact?: string
  [key: string]: unknown
}

export const fetchMyProfile = async () => {
  const resp = await api.get('/profiles/me')
  return resp.data
}

export const savePersonalInfo = async (payload: PersonalInfoPayload) => {
  const resp = await api.post('/profiles/me/personal', payload)
  return resp.data
}

export const listProfileVersions = async () => {
  const resp = await api.get('/profiles/me/versions')
  return resp.data
}
