import api from '@/lib/api'

export const saveLifestyle = async (payload: any) => {
  const resp = await api.post('/profiles/me/lifestyle', payload)
  return resp.data
}

export const saveNutrition = async (payload: any) => {
  const resp = await api.post('/profiles/me/nutrition', payload)
  return resp.data
}

export const getProfileCompletion = async () => {
  const resp = await api.get('/profiles/me/completion')
  return resp.data
}

export const previewVersion = async (version: number) => {
  const resp = await api.get(`/profiles/me/versions/${version}`)
  return resp.data
}

export const restoreVersion = async (version: number) => {
  const resp = await api.post(`/profiles/me/versions/${version}/restore`)
  return resp.data
}
