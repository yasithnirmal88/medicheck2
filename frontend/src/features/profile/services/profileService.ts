import { api } from '@/lib/api'
import type { WizardState } from '../types/wizard'
import { mapMainPersonalFromWizard } from '../api/profileApi'

const PROFILE_ENDPOINT = '/profiles/me'
const LIFESTYLE_ENDPOINT = '/profiles/me/lifestyle'
const NUTRITION_ENDPOINT = '/profiles/me/nutrition'
const COMPLETION_ENDPOINT = '/profiles/me/completion'

export async function fetchProfileData(): Promise<WizardState> {
  const response = await api.get(PROFILE_ENDPOINT)
  return response.data
}

export async function saveProfileData(data: WizardState): Promise<WizardState> {
  const payload = mapMainPersonalFromWizard(data)
  const response = await api.post(PROFILE_ENDPOINT, payload)
  return response.data
}

export async function saveLifestyleData(data: WizardState['lifestyle']): Promise<void> {
  await api.post(LIFESTYLE_ENDPOINT, data)
}

export async function saveNutritionData(data: WizardState['nutrition']): Promise<void> {
  await api.post(NUTRITION_ENDPOINT, data)
}

export async function fetchCompletionData(): Promise<{
  completion_percentage: number
  sections_completed: string[]
  missing_sections: string[]
}> {
  const response = await api.get(COMPLETION_ENDPOINT)
  return response.data
}

export async function saveDraftData(data: Partial<WizardState>): Promise<void> {
  const draftKey = 'medicheck-profile-draft-v1'
  const existing = localStorage.getItem(draftKey)
  const merged = existing ? { ...JSON.parse(existing), ...data } : data
  localStorage.setItem(draftKey, JSON.stringify(merged))
}

export function loadDraftData(): Partial<WizardState> | null {
  const draftKey = 'medicheck-profile-draft-v1'
  const raw = localStorage.getItem(draftKey)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function clearDraftData(): void {
  const draftKey = 'medicheck-profile-draft-v1'
  localStorage.removeItem(draftKey)
}

export function hasUnsavedChanges(currentState: WizardState): boolean {
  const draft = loadDraftData()
  if (!draft) return true
  return JSON.stringify(currentState) !== JSON.stringify(draft)
}