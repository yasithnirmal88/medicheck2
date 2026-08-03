import { sectionSchemas } from '../wizard/schemas'
import type { SectionKey, WizardState } from '../types/wizard'

export function validateSection(key: SectionKey, data: unknown): { valid: boolean; errors: string[] } {
  const schema = sectionSchemas[key]
  if (!schema) return { valid: true, errors: [] }
  const result = schema.safeParse(data)
  if (result.success) return { valid: true, errors: [] }
  const errors = result.error.issues.map((i) => i.message)
  return { valid: false, errors }
}

export function validateField(key: SectionKey, fieldName: string, value: unknown): string[] {
  const schema = sectionSchemas[key]
  if (!schema) return []
  const result = schema.safeParse({ [fieldName]: value })
  if (result.success) return []
  const fieldError = result.error.issues.find((i) => i.path[0] === fieldName)
  return fieldError ? [fieldError.message] : []
}

export function getMissingFields(state: WizardState): Record<SectionKey, string[]> {
  const missing: Record<SectionKey, string[]> = {}
  for (const key of Object.keys(sectionSchemas) as SectionKey[]) {
    const schema = sectionSchemas[key]
    if (!schema) continue
    const data = state[key]
    const result = schema.safeParse(data)
    if (!result.success) {
      const fieldErrors = result.error.issues.map((i) => i.path.join('.'))
      missing[key] = fieldErrors
    }
  }
  return missing
}

export function isSectionComplete(key: SectionKey, state: WizardState): boolean {
  const schema = sectionSchemas[key]
  if (!schema) return true
  const result = schema.safeParse(state[key])
  return result.success
}

export function getOverallCompletion(state: WizardState): number {
  const sections = Object.keys(sectionSchemas) as SectionKey[]
  const completed = sections.filter((key) => isSectionComplete(key, state))
  return sections.length > 0 ? Math.round((completed.length / sections.length) * 100) : 0
}