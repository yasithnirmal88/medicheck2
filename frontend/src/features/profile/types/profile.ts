export type PersonalInfo = {
  full_name: string
  date_of_birth?: string | null
  sex?: string | null
  height_cm?: number | null
  weight_kg?: number | null
  blood_group?: string | null
  nationality?: string | null
  country?: string | null
  state?: string | null
  city?: string | null
  preferred_language?: string | null
  emergency_contact?: Record<string, unknown> | null
  occupation?: string | null
  industry?: string | null
  education_level?: string | null
  marital_status?: string | null
  children_count?: number | null
}

export type HealthProfile = {
  id: string
  user_id: string
  draft: boolean
  metadata?: Record<string, unknown>
  personal_info?: PersonalInfo | null
}
