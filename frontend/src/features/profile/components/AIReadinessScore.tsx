import React from 'react'
import { Sparkles, TrendingUp, AlertTriangle, Info } from 'lucide-react'
import type { WizardState } from '@/features/profile/types/wizard'

interface AIReadinessScoreProps {
  state: WizardState
}

export function AIReadinessScore({ state }: AIReadinessScoreProps) {
  const { score, insights } = React.useMemo(() => {
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
    const bodyFields = [body.height_cm, body.weight_kg, body.blood_pressure_systolic, body.blood_pressure_diastolic]
    maxPoints += bodyFields.length
    points += bodyFields.filter((v) => v && v.trim() !== '').length

    const lifestyle = state.lifestyle
    const lifestyleFields = [lifestyle.smoking, lifestyle.alcohol, lifestyle.caffeine_intake, lifestyle.daily_water_intake]
    maxPoints += lifestyleFields.length
    points += lifestyleFields.filter((v) => v && v.trim() !== '').length

    const nutrition = state.nutrition
    const nutritionFields = [nutrition.diet_type, nutrition.meals_per_day, nutrition.fruit_intake, nutrition.vegetable_intake]
    maxPoints += nutritionFields.length
    points += nutritionFields.filter((v) => v && v.trim() !== '').length

    maxPoints += 4
    points += state.conditions.length > 0 ? 1 : 0
    points += state.family_history.length > 0 ? 1 : 0
    points += state.medications.length > 0 ? 1 : 0
    points += state.allergies.length > 0 ? 1 : 0

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

    const insightList: string[] = []
    if (personal.first_name && personal.last_name && !personal.email) {
      insightList.push('Add your email for AI-powered health insights')
    }
    if (body.height_cm && body.weight_kg && !body.waist_cm) {
      insightList.push('Add waist circumference for BMI and metabolic analysis')
    }
    if (lifestyle.smoking === 'current') {
      insightList.push('Smoking status recorded — AI can provide cessation resources')
    }
    if (nutrition.diet_type && !nutrition.supplements) {
      insightList.push('Add supplements for personalized nutrition analysis')
    }
    if (state.conditions.length > 0 && state.family_history.length === 0) {
      insightList.push('Add family history for better risk assessment')
    }
    if (emergency.primary_name && !emergency.insurance_provider) {
      insightList.push('Add insurance provider for complete emergency profile')
    }
    if (!consents.ai_consent) {
      insightList.push('Enable AI consent for personalized health analysis')
    }

    return { score: pct, insights: insightList }
  }, [state])

  const getColor = (pct: number) => {
    if (pct >= 80) return 'emerald'
    if (pct >= 50) return 'amber'
    return 'red'
  }

  const color = getColor(score)

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="h-5 w-5 text-blue-500" />
        <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">AI Readiness Score</h3>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative">
          <svg className="h-20 w-20 -rotate-90" viewBox="0 0 36 36">
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="#E2E8F0"
              strokeWidth="3"
              className="dark:stroke-slate-700"
            />
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke={color === 'emerald' ? '#10B981' : color === 'amber' ? '#EFA44' : '#EF4444'}
              strokeWidth="3"
              strokeDasharray={`${score}, 100`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold text-slate-800 dark:text-slate-100">{score}%</span>
          </div>
        </div>

        <div className="flex-1 space-y-2">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {score >= 80
              ? 'Your profile is well-prepared for AI analysis'
              : score >= 50
                ? 'Your profile is partially ready — add more data for better insights'
                : 'Your profile needs more data for AI analysis'}
          </p>
          <div className="flex items-center gap-1">
            {score >= 80 ? (
              <TrendingUp className="h-4 w-4 text-emerald-500" />
            ) : score >= 50 ? (
              <TrendingUp className="h-4 w-4 text-amber-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-red-500" />
            )}
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {score >= 80 ? 'Ready for analysis' : score >= 50 ? 'Partial readiness' : 'Needs more data'}
            </span>
          </div>
        </div>
      </div>

      {insights.length > 0 && (
        <div className="mt-4 border-t border-slate-200 pt-4 dark:border-slate-700">
          <h4 className="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">
            Suggestions
          </h4>
          <ul className="space-y-2">
            {insights.map((insight, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-400">
                <Info className="mt-0.5 h-3 w-3 shrink-0 text-blue-500" />
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}