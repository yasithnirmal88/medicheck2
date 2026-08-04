import api from '@/lib/api'

interface LifestylePayload {
  activity_level?: string
  sleep_hours?: number
  stress_level?: string
  smoking_status?: string
  alcohol_use?: string
  exercise_frequency?: string
  [key: string]: unknown
}

interface NutritionPayload {
  diet_type?: string
  food_restrictions?: string[]
  daily_calories?: number
  [key: string]: unknown
}

export const saveLifestyle = async (payload: LifestylePayload) => {
  const resp = await api.post('/profiles/me/lifestyle', payload)
  return resp.data
}

export const saveNutrition = async (payload: NutritionPayload) => {
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
