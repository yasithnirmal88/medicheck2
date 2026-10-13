import { describe, it, expect } from 'vitest'
import { createDefaultState, normalizeUnanswered } from '../defaults'

describe('normalizeUnanswered', () => {
  it('fills unanswered option questions with their none/no/never default', () => {
    const state = createDefaultState()
    const normalized = normalizeUnanswered(state)

    expect(normalized.lifestyle.smoking).toBe('never')
    expect(normalized.lifestyle.drug_use).toBe('never')
    expect(normalized.sleep.sleep_apnea).toBe('no')
    expect(normalized.sleep.night_awakenings).toBe('none')
    expect(normalized.women_health.pcos).toBe('no')
    expect(normalized.men_health.prostate_issues).toBe('no')
    expect(normalized.men_health.urinary_symptoms).toBe('none')
    expect(normalized.environment.mold_exposure).toBe('no')
  })

  it('keeps answered questions untouched', () => {
    const state = createDefaultState()
    state.lifestyle.smoking = 'current'
    state.sleep.sleep_apnea = 'diagnosed'
    state.women_health.pcos = 'suspected'

    const normalized = normalizeUnanswered(state)

    expect(normalized.lifestyle.smoking).toBe('current')
    expect(normalized.sleep.sleep_apnea).toBe('diagnosed')
    expect(normalized.women_health.pcos).toBe('suspected')
  })

  it('does not apply none values to numeric, text, or rating fields', () => {
    const state = createDefaultState()
    const normalized = normalizeUnanswered(state)

    expect(normalized.body.height_cm).toBe('')
    expect(normalized.lifestyle.caffeine_intake).toBe('')
    expect(normalized.sleep.sleep_quality).toBe('')
    expect(normalized.travel.vaccinations_required).toBe('')
  })

  it('does not mutate the original state', () => {
    const state = createDefaultState()
    normalizeUnanswered(state)
    expect(state.sleep.sleep_apnea).toBe('')
  })

  it('leaves empty option lists alone when no none value exists', () => {
    const state = createDefaultState()
    const normalized = normalizeUnanswered(state)
    expect(normalized.physical_activity.exercise_types).toEqual([])
    expect(normalized.occupation.work_environment).toBe('')
  })
})