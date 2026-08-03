import React from 'react'
import { AlertTriangle, CheckCircle, Info, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Tip {
  icon: React.ReactNode
  color: 'teal' | 'amber' | 'red' | 'blue'
  text: string
}

function tipColor(color: Tip['color']) {
  switch (color) {
    case 'teal':
      return 'border-teal-200 bg-teal-50 text-teal-800 dark:border-teal-800 dark:bg-teal-900/20 dark:text-teal-200'
    case 'amber':
      return 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-200'
    case 'red':
      return 'border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-900/20 dark:text-red-200'
    case 'blue':
      return 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-200'
  }
}

function iconColor(color: Tip['color']) {
  switch (color) {
    case 'teal': return 'text-teal-500'
    case 'amber': return 'text-amber-500'
    case 'red': return 'text-red-500'
    case 'blue': return 'text-blue-500'
  }
}

interface HealthTipsProps {
  lifestyle?: unknown
  nutrition?: unknown
  medicalHistory?: unknown
  familyHistory?: unknown
  lifestyleRisks?: unknown
  environment?: unknown
  occupation?: unknown
  travel?: unknown
}

export function HealthTips({ lifestyle, nutrition, medicalHistory, familyHistory, lifestyleRisks, environment, occupation, travel }: HealthTipsProps) {
  const tips = React.useMemo<Tip[]>(() => {
    const result: Tip[] = []
    if (!lifestyle && !nutrition && !medicalHistory && !familyHistory && !lifestyleRisks && !environment && !occupation && !travel) return result

    const l = (lifestyle ?? {}) as Record<string, unknown>
    const n = (nutrition ?? {}) as Record<string, unknown>
    const mh = (medicalHistory ?? {}) as Record<string, unknown>
    const fh = (familyHistory ?? {}) as Record<string, unknown>
    const lr = (lifestyleRisks ?? {}) as Record<string, unknown>
    const env = (environment ?? {}) as Record<string, unknown>
    const occ = (occupation ?? {}) as Record<string, unknown>
    const trav = (travel ?? {}) as Record<string, unknown>

    if (l.smoking === 'current') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Current smoking significantly increases cardiovascular and respiratory risk. Consider a cessation plan.' })
    } else if (l.smoking === 'former') {
      result.push({ icon: <CheckCircle className="h-4 w-4" />, color: 'teal', text: 'Former smoker — your body is already recovering. Staying smoke-free continues to reduce risk over time.' })
    }

    if (l.alcohol === 'heavy') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Heavy alcohol consumption is linked to liver disease, hypertension, and increased cancer risk.' })
    } else if (l.alcohol === 'moderate') {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'amber', text: 'Moderate drinking — consider reducing further for optimal health outcomes.' })
    }

    const caffeine = Number(l.caffeine_intake) || 0
    if (caffeine > 5) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: `High caffeine intake (${caffeine} cups/day) may cause sleep disruption and anxiety. Consider reducing.` })
    }

    const screenTime = Number(l.screen_time) || 0
    if (screenTime > 8) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: `Excessive screen time (${screenTime}h/day) can strain eyes and affect sleep. Take regular breaks.` })
    }

    const water = Number(n.water_intake) || 0
    if (water < 6) {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: `Low water intake (${water} glasses/day). Aim for at least 6-8 glasses daily for optimal hydration.` })
    }

    if (n.fast_food_frequency === 'daily') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Daily fast food is associated with higher calorie, sodium, and unhealthy fat intake. Consider meal prepping.' })
    } else if (n.fast_food_frequency === 'weekly') {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'amber', text: 'Weekly fast food is manageable, but try to cook more meals at home for better nutrition control.' })
    }

    const fruit = Number(n.fruit_intake) || 0
    if (fruit < 2) {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: `Low fruit intake (${fruit} servings/day). Fruits provide essential vitamins and fiber — aim for 2-3 servings.` })
    }

    const veg = Number(n.vegetable_intake) || 0
    if (veg < 3) {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: `Low vegetable intake (${veg} servings/day). Vegetables are rich in micronutrients — aim for 3-5 servings.` })
    }

    if (n.sugar_intake === 'high') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: 'High sugar intake increases risk of obesity, type 2 diabetes, and dental issues.' })
    }

    if (n.salt_intake === 'high') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: 'High salt intake can raise blood pressure. Consider reducing processed food and adding herbs for flavor.' })
    }

    const diet = n.diet_type as string
    if (diet === 'vegan' || diet === 'vegetarian') {
      result.push({ icon: <Zap className="h-4 w-4" />, color: 'teal', text: `${diet === 'vegan' ? 'Vegan' : 'Vegetarian'} diets can be nutritious — ensure adequate B12, iron, and protein intake.` })
    }

    const conditions = (mh.conditions as string[]) ?? []
    if (conditions.includes('hypertension')) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Hypertension detected — monitor blood pressure regularly and limit sodium intake.' })
    }
    if (conditions.includes('diabetes')) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: 'Diabetes noted — regular blood sugar monitoring and dietary management are important.' })
    }
    if (conditions.includes('heart_disease')) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Heart disease history — regular cardiac check-ups and a heart-healthy lifestyle are essential.' })
    }
    if (conditions.includes('cancer')) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Cancer history — ensure regular follow-ups and screening as recommended by your doctor.' })
    }
    if (conditions.includes('stroke')) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Stroke history — manage risk factors like blood pressure, cholesterol, and avoid smoking.' })
    }
    const surgeriesCount = Number(mh.surgeries_count) || 0
    if (surgeriesCount > 3) {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: `Multiple surgeries (${surgeriesCount}) — keep detailed medical records and inform your doctor.` })
    }
    const hospitalAdmissions = Number(mh.hospital_admissions) || 0
    if (hospitalAdmissions > 5) {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: `Frequent hospital admissions (${hospitalAdmissions}) — consider a care coordination plan.` })
    }
    const organTransplants = Number(mh.organ_transplants) || 0
    if (organTransplants > 0) {
      result.push({ icon: <Zap className="h-4 w-4" />, color: 'teal', text: `Organ transplant history (${organTransplants}) — ensure regular immunosuppression monitoring.` })
    }

    const familyDiseases = (fh.diseases as string[]) ?? []
    if (familyDiseases.length > 0) {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: `Family history of ${familyDiseases.join(', ')} — consider proactive screening and preventive measures.` })
    }

    const exerciseDays = Number(l.exercise_days) || 0
    if (exerciseDays < 3) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: `Low exercise frequency (${exerciseDays} days/week). Aim for at least 150 minutes of moderate activity per week.` })
    }

    const stepCount = Number(l.daily_step_count) || 0
    if (stepCount < 5000 && stepCount > 0) {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: `Low daily step count (${stepCount}). Try to reach 7,000-10,000 steps for cardiovascular health.` })
    }

    const sleepHours = Number(l.avg_sleep_hours) || 0
    if (sleepHours < 6) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: `Insufficient sleep (${sleepHours}h). Aim for 7-9 hours for optimal recovery and cognitive function.` })
    } else if (sleepHours > 9) {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'amber', text: `Excessive sleep (${sleepHours}h). Consistently sleeping too much may indicate underlying issues.` })
    }

    const stressLevel = Number(l.stress_level) || 0
    if (stressLevel >= 4) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: `High stress level (${stressLevel}/5). Consider stress management techniques like meditation or exercise.` })
    }

    const burnoutRisk = Number(l.burnout_risk) || 0
    if (burnoutRisk >= 3) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'High burnout risk detected. Prioritize rest, set boundaries, and consider professional support.' })
    }

    const mood = l.mood as string
    if (mood === 'low' || mood === 'very_low') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: `Low mood reported. Regular physical activity and social connection can help improve mood.` })
    }

    if (lr.seatbelt_use === 'never') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Never wearing a seatbelt significantly increases injury risk in accidents. Always buckle up.' })
    } else if (lr.seatbelt_use === 'sometimes') {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'amber', text: 'Inconsistent seatbelt use — make it a habit to buckle up every time for safety.' })
    }

    if (lr.sun_exposure === 'high' || lr.sun_exposure === 'very_high') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: 'High sun exposure increases skin cancer risk. Use sunscreen (SPF 30+) and protective clothing.' })
    }

    if (lr.driving_habits === 'risky') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Risky driving habits detected. Consider defensive driving courses and always follow traffic laws.' })
    }

    if (lr.firearms === 'yes_unstored') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Unsecured firearms pose serious safety risks, especially in households with children. Store securely.' })
    }

    if (lr.substance_exposure === 'chemical' || lr.substance_exposure === 'biological' || lr.substance_exposure === 'radiation') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: 'Occupational substance exposure detected. Ensure proper protective equipment and follow safety protocols.' })
    }

    if (env.air_pollution === 'high') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: 'High air pollution exposure can affect respiratory and cardiovascular health. Consider indoor air purification.' })
    }

    if (env.mold_exposure === 'confirmed') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Confirmed mold exposure is a serious health risk. Address moisture issues and consider professional remediation.' })
    } else if (env.mold_exposure === 'suspected') {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'amber', text: 'Suspected mold exposure — consider testing and addressing moisture sources in your home.' })
    }

    if (env.chemical_exposure === 'industrial' || env.chemical_exposure === 'agricultural') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: 'Industrial or agricultural chemical exposure — ensure proper protective measures and regular health check-ups.' })
    }

    if (env.noise_pollution === 'high' || (typeof env.noise_pollution === 'number' && env.noise_pollution >= 7)) {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: 'High noise pollution can impact hearing and stress levels. Consider noise-canceling solutions.' })
    }

    const workStress = Number(occ.work_stress) || 0
    if (workStress >= 4) {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'amber', text: `High work stress (${workStress}/5). Chronic stress affects both mental and physical health — prioritize self-care.` })
    }

    if (occ.work_environment === 'hazardous') {
      result.push({ icon: <AlertTriangle className="h-4 w-4" />, color: 'red', text: 'Hazardous work environment detected. Ensure all safety protocols are followed and use proper PPE.' })
    }

    if (occ.night_shifts === 'regular' || occ.night_shifts === 'rotating') {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: 'Night shift work can disrupt circadian rhythm. Prioritize sleep hygiene and regular health monitoring.' })
    }

    if (occ.heavy_lifting === 'frequent' || occ.heavy_lifting === 'daily') {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: 'Frequent heavy lifting — ensure proper technique and consider ergonomic adjustments to prevent injury.' })
    }

    if (occ.travel_frequency === 'frequent' || occ.travel_frequency === 'constant') {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: 'Frequent travel can disrupt sleep and diet patterns. Stay hydrated and maintain healthy routines on the road.' })
    }

    const countries = (trav.countries_visited as string) ?? ''
    const tropical = (trav.tropical_regions as string) ?? ''
    if (countries.length > 0 || tropical.length > 0) {
      result.push({ icon: <Info className="h-4 w-4" />, color: 'blue', text: 'International travel history noted. Ensure vaccinations are up to date and monitor for travel-related illnesses.' })
    }

    return result
  }, [lifestyle, nutrition, medicalHistory, familyHistory, lifestyleRisks, environment, occupation, travel])

  if (tips.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
        <p className="text-sm text-slate-500 dark:text-slate-400">Complete your health sections to see personalized insights.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-2">
        <Zap className="h-4 w-4 text-blue-500" />
        Health Insights
      </h3>
      {tips.map((tip, i) => (
        <div key={i} className={cn('rounded-xl border p-3 text-sm flex items-start gap-2', tipColor(tip.color))}>
          <span className={cn('mt-0.5 shrink-0', iconColor(tip.color))}>{tip.icon}</span>
          <span>{tip.text}</span>
        </div>
      ))}
    </div>
  )
}