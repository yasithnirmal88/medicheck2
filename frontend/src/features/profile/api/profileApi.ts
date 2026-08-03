import api from '@/lib/api'

export async function fetchProfile() {
  const { data } = await api.get('/profiles/me')
  return data
}

export async function savePersonalInfo(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await api.post('/profiles/me/personal', payload)
  return data
}

export async function saveLifestyle(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await api.post('/profiles/me/lifestyle', payload)
  return data
}

export async function saveNutrition(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await api.post('/profiles/me/nutrition', payload)
  return data
}

export async function fetchCompletion() {
  const { data } = await api.get('/profiles/me/completion')
  return data
}

export async function listProfileVersions() {
  const { data } = await api.get('/profiles/me/versions')
  return data
}

export async function previewVersion(version: number) {
  const { data } = await api.get(`/profiles/me/versions/${version}`)
  return data
}

export async function restoreVersion(version: number) {
  const { data } = await api.post(`/profiles/me/versions/${version}/restore`)
  return data
}

export async function listMeasurements(): Promise<Record<string, unknown>[]> {
  const { data } = await api.get('/profiles/me/measurements')
  return data
}

export async function addMeasurement(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await api.post('/profiles/me/measurements', payload)
  return data
}

export async function listMedicalHistory() {
  const { data } = await api.get('/profiles/me/medical')
  return data
}

export async function addMedicalHistory(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await api.post('/profiles/me/medical', payload)
  return data
}

export async function listMedications() {
  const { data } = await api.get('/profiles/me/medications')
  return data
}

export async function addMedication(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await api.post('/profiles/me/medications', payload)
  return data
}

export async function listSurgeries() {
  const { data } = await api.get('/profiles/me/surgeries')
  return data
}

export async function addSurgery(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await api.post('/profiles/me/surgeries', payload)
  return data
}

export async function listFamily() {
  const { data } = await api.get('/profiles/me/family')
  return data
}

export async function addFamily(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await api.post('/profiles/me/family', payload)
  return data
}

export async function listAllergies() {
  const { data } = await api.get('/profiles/me/allergies')
  return data
}

export async function addAllergy(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await api.post('/profiles/me/allergies', payload)
  return data
}

export async function listImmunizations() {
  const { data } = await api.get('/profiles/me/immunizations')
  return data
}

export async function addImmunization(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await api.post('/profiles/me/immunizations', payload)
  return data
}

export type ProfileApiReturn = {
  personal: Record<string, unknown>
}

export function mapPersonalFromWizard(personal: {
  first_name: string
  middle_name: string
  last_name: string
  date_of_birth: string
  gender: string
  blood_group: string
  nationality: string
  ethnicity: string
  country: string
  state: string
  city: string
  marital_status: string
  education_level: string
  occupation: string
  industry: string
  preferred_language: string
  email: string
  phone: string
  emergency_contact: string
  emergency_phone: string
  relationship: string
}): Record<string, unknown> {
  const fullName = [personal.first_name, personal.middle_name, personal.last_name].filter(Boolean).join(' ').trim()
  return {
    full_name: fullName || undefined,
    date_of_birth: personal.date_of_birth || undefined,
    sex: personal.gender || undefined,
    blood_group: personal.blood_group || undefined,
    nationality: personal.nationality || undefined,
    country: personal.country || undefined,
    state: personal.state || undefined,
    city: personal.city || undefined,
    preferred_language: personal.preferred_language || undefined,
    emergency_contact: personal.emergency_contact
      ? {
          name: personal.emergency_contact,
          phone: personal.emergency_phone,
          relationship: personal.relationship,
        }
      : undefined,
    occupation: personal.occupation || undefined,
    industry: personal.industry || undefined,
    education_level: personal.education_level || undefined,
    marital_status: personal.marital_status || undefined,
  }
}