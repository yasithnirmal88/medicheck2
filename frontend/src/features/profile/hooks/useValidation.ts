import { useCallback, useState } from 'react'
import { sectionSchemas } from '../wizard/schemas'
import type { SectionKey } from '../types/wizard'

interface ValidationResult {
  isValid: boolean
  errors: Record<string, string[]>
}

export function useValidation() {
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  const validateSection = useCallback((key: SectionKey, data: unknown): ValidationResult => {
    const schema = sectionSchemas[key]
    if (!schema) return { isValid: true, errors: {} }
    const result = schema.safeParse(data)
    if (result.success) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
      return { isValid: true, errors: {} }
    }
    const fieldErrors: Record<string, string[]> = {}
    for (const issue of result.error.issues) {
      const path = issue.path.join('.')
      if (!fieldErrors[path]) fieldErrors[path] = []
      fieldErrors[path].push(issue.message)
    }
    setErrors((prev) => ({ ...prev, [key]: Object.values(fieldErrors).flat() }))
    return { isValid: false, errors: fieldErrors }
  }, [])

  const validateField = useCallback(
    (key: SectionKey, fieldName: string, value: unknown): string[] => {
      const schema = sectionSchemas[key]
      if (!schema) return []
      const result = schema.safeParse({ [fieldName]: value })
      if (result.success) return []
      const fieldError = result.error.issues.find((i) => i.path[0] === fieldName)
      return fieldError ? [fieldError.message] : []
    },
    [],
  )

  const touchField = useCallback((key: string) => {
    setTouched((prev) => ({ ...prev, [key]: true }))
  }, [])

  const clearErrors = useCallback((key?: SectionKey) => {
    setErrors((prev) => {
      if (key) {
        const next = { ...prev }
        delete next[key]
        return next
      }
      return {}
    })
  }, [])

  return { validateSection, validateField, touchField, clearErrors, errors, touched }
}