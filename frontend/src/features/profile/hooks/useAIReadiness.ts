import { useMemo } from 'react'
import type { WizardState } from '../types/wizard'

export function useAIReadiness(state: WizardState) {
  const score = useMemo(() => {
    let points = 0
    let maxPoints = 0

    const personal = state.personal
    const personalFields = [
      personal.first_name,
      personal.last_name,
      personal.date_of_birth,
      personal.gender,
      personal.country,
      personal.email,
      personal.phone,
    ]
    maxPoints += personalFields.length
    points += personalFields.filter((v) => v && v.trim() !== '').length

    const body = state.body
    const bodyFields = [
      body.height_cm,
      body.weight_kg,
      body.blood_pressure_systolic,
      body.blood_pressure_diastolic,
    ]
    maxPoints += bodyFields.length
    points += bodyFields.filter((v) => v && v.trim() !== '').length

    const lifestyle = state.lifestyle
    const lifestyleFields = [
      lifestyle.smoking,
      lifestyle.alcohol,
      lifestyle.caffeine_intake,
      lifestyle.daily_water_intake,
    ]
    maxPoints += lifestyleFields.length
    points += lifestyleFields.filter((v) => v && v.trim() !== '').length

    const nutrition = state.nutrition
    const nutritionFields = [
      nutrition.diet_type,
      nutrition.meals_per_day,
      nutrition.fruit_intake,
      nutrition.vegetable_intake,
    ]
    maxPoints += nutritionFields.length
    points += nutritionFields.filter((v) => v && v.trim() !== '').length

    const conditions = state.conditions
    maxPoints += 1
    points += conditions.length > 0 ? 1 : 0

    const familyHistory = state.family_history
    maxPoints += 1
    points += familyHistory.length > 0 ? 1 : 0

    const medications = state.medications
    maxPoints += 1
    points += medications.length > 0 ? 1 : 0

    const allergies = state.allergies
    maxPoints += 1
    points += allergies.length > 0 ? 1 : 0

    const emergency = state.emergency
    const emergencyFields = [emergency.primary_name, emergency.primary_phone, emergency.primary_relationship]
    maxPoints += emergencyFields.length
    points += emergencyFields.filter((v) => v && v.trim() !== '').length

    const consents = state.consents
    maxPoints += 3
    points += consents.terms_accepted ? 1 : 0
    points += consents.ai_consent ? 1 : 0
    points += consents.research_consent ? 1 : 0

    const pct = maxPoints > 0 ? Math.round((points / maxPoints) * 100) : 0

    const insights = []
    if (personal.first_name && personal.last_name && !personal.email) {
      insights.push('Add your email for AI-powered health insights')
    }
    if (body.height_cm && body.weight_kg && !body.waist_cm) {
      insights.push('Add waist circumference for BMI and metabolic analysis')
    }
    if (lifestyle.smoking === 'current') {
      insights.push('Smoking status recorded — AI can provide cessation resources')
    }
    if (nutrition.diet_type && !nutrition.supplements) {
      insights.push('Add supplements for personalized nutrition analysis')
    }
    if (conditions.length > 0 && familyHistory.length === 0) {
      insights.push('Add family history for better risk assessment')
    }
    if (emergency.primary_name && !emergency.insurance_provider) {
      insights.push('Add insurance provider for complete emergency profile')
    }
    if (!consents.ai_consent) {
      insights.push('Enable AI consent for personalized health analysis')
    }

    return { score: pct, maxScore: 100, insights }
  }, [state])

  return score
}