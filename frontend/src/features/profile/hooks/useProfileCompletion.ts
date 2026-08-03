import { useMemo } from 'react'
import { fieldSpecs } from '../wizard/fieldSpecs'
import type { WizardState, SectionKey } from '../types/wizard'

export function useProfileCompletion(state: WizardState) {
  const sections = useMemo(() => {
    let totalFields = 0
    let filledFields = 0
    const sectionDetails: Record<string, { filled: number; total: number; pct: number }> = {}

    for (const key of Object.keys(fieldSpecs) as SectionKey[]) {
      const specs = fieldSpecs[key]
      if (specs.length === 0) {
        sectionDetails[key] = { filled: 0, total: 0, pct: 0 }
        continue
      }
      const value = state[key]
      if (Array.isArray(value)) {
        const count = value.length
        sectionDetails[key] = { filled: count, total: count, pct: count > 0 ? 100 : 0 }
        totalFields += count
        filledFields += count
        continue
      }
      const record = (value as unknown as Record<string, unknown>) ?? {}
      let filled = 0
      let total = 0
      for (const spec of specs) {
        if (spec.kind === 'checkbox') {
          total++
          if (record[spec.name]) filled++
          continue
        }
        if (spec.optional) continue
        total++
        const val = record[spec.name]
        const hasValue =
          val !== undefined &&
          val !== null &&
          val !== '' &&
          (typeof val !== 'string' || (val as string).trim() !== '') &&
          !(Array.isArray(val) && (val as unknown[]).length === 0)
        if (hasValue) filled++
      }
      totalFields += total
      filledFields += filled
      sectionDetails[key] = {
        filled,
        total,
        pct: total > 0 ? Math.round((filled / total) * 100) : 0,
      }
    }

    const overallPct = totalFields > 0 ? Math.round((filledFields / totalFields) * 100) : 0
    return { sections: sectionDetails, totalFields, filledFields, overallPct }
  }, [state])

  return sections
}