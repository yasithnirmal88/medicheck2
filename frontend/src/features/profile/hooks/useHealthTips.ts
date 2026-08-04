import { useMemo } from 'react'
import type { WizardState } from '../types/wizard'

interface HealthTip {
  icon: string
  color: 'teal' | 'amber' | 'red' | 'blue'
  text: string
}

export function useHealthTips(state: WizardState): HealthTip[] {
  return useMemo(() => {
    const tips: HealthTip[] = []
    const l = state.lifestyle
    const n = state.nutrition
    const _mh = state.conditions
    const _fh = state.family_history
    const _lr = state.lifestyle_risks
    const _env = state.environment
    const _occ = state.occupation
    const _trav = state.travel

    if (l.smoking === 'current') {
      tips.push({ icon: 'alert', color: 'red', text: 'Current smoking significantly increases cardiovascular and respiratory risk. Consider a cessation plan.' })
    } else if (l.smoking === 'former') {
      tips.push({ icon: 'check', color: 'teal', text: 'Former smoker — your body is already recovering. Staying smoke-free continues to reduce risk over time.' })
    }

    if (l.alcohol === 'heavy') {
      tips.push({ icon: 'alert', color: 'red', text: 'Heavy alcohol consumption is linked to liver disease, hypertension, and increased cancer risk.' })
    } else if (l.alcohol === 'moderate') {
      tips.push({ icon: 'info', color: 'amber', text: 'Moderate drinking — consider reducing further for optimal health outcomes.' })
    }

    const caffeine = Number(l.caffeine_intake) || 0
    if (caffeine > 5) {
      tips.push({ icon: 'alert', color: 'amber', text: `High caffeine intake (${caffeine} cups/day) may cause sleep disruption and anxiety.` })
    }

    const screenTime = Number(l.screen_time) || 0
    if (screenTime > 8) {
      tips.push({ icon: 'alert', color: 'amber', text: `Excessive screen time (${screenTime}h/day) can strain eyes and affect sleep.` })
    }

    const water = Number(n.water_intake) || 0
    if (water < 6) {
      tips.push({ icon: 'info', color: 'blue', text: `Low water intake (${water} glasses/day). Aim for at least 6-8 glasses daily.` })
    }

    if (n.fast_food_frequency === 'daily') {
      tips.push({ icon: 'alert', color: 'red', text: 'Daily fast food is associated with higher calorie, sodium, and unhealthy fat intake.' })
    } else if (n.fast_food_frequency === 'weekly') {
      tips.push({ icon: 'info', color: 'amber', text: 'Weekly fast food is manageable, but try to cook more meals at home.' })
    }

    const fruit = Number(n.fruit_intake) || 0
    if (fruit < 2) {
      tips.push({ icon: 'info', color: 'blue', text: `Low fruit intake (${fruit} servings/day). Aim for 2-3 servings.` })
    }

    const veg = Number(n.vegetable_intake) || 0
    if (veg < 3) {
      tips.push({ icon: 'info', color: 'blue', text: `Low vegetable intake (${veg} servings/day). Aim for 3-5 servings.` })
    }

    if (n.sugar_intake === 'high') {
      tips.push({ icon: 'alert', color: 'amber', text: 'High sugar intake increases risk of obesity, type 2 diabetes, and dental issues.' })
    }

    if (n.salt_intake === 'high') {
      tips.push({ icon: 'alert', color: 'amber', text: 'High salt intake can raise blood pressure. Consider reducing processed food.' })
    }

    if (lr.seatbelt_use === 'never') {
      tips.push({ icon: 'alert', color: 'red', text: 'Never wearing a seatbelt significantly increases injury risk in accidents.' })
    }

    if (lr.sun_exposure === 'high' || lr.sun_exposure === 'very_high') {
      tips.push({ icon: 'alert', color: 'amber', text: 'High sun exposure increases skin cancer risk. Use sunscreen (SPF 30+).' })
    }

    if (lr.driving_habits === 'risky') {
      tips.push({ icon: 'alert', color: 'red', text: 'Risky driving habits detected. Consider defensive driving courses.' })
    }

    if (lr.firearms === 'yes_unstored') {
      tips.push({ icon: 'alert', color: 'red', text: 'Unsecured firearms pose serious safety risks. Store securely.' })
    }

    if (env.air_pollution === 'high') {
      tips.push({ icon: 'alert', color: 'amber', text: 'High air pollution exposure can affect respiratory and cardiovascular health.' })
    }

    if (env.mold_exposure === 'confirmed') {
      tips.push({ icon: 'alert', color: 'red', text: 'Confirmed mold exposure is a serious health risk. Address moisture issues.' })
    }

    if (env.chemical_exposure === 'industrial' || env.chemical_exposure === 'agricultural') {
      tips.push({ icon: 'alert', color: 'amber', text: 'Chemical exposure detected. Ensure proper protective measures and health check-ups.' })
    }

    const workStress = Number(occ.work_stress) || 0
    if (workStress >= 4) {
      tips.push({ icon: 'alert', color: 'amber', text: `High work stress (${workStress}/5). Prioritize self-care and stress management.` })
    }

    if (occ.work_environment === 'hazardous') {
      tips.push({ icon: 'alert', color: 'red', text: 'Hazardous work environment. Ensure all safety protocols are followed.' })
    }

    if (occ.night_shifts === true) {
      tips.push({ icon: 'info', color: 'blue', text: 'Night shift work can disrupt circadian rhythm. Prioritize sleep hygiene.' })
    }

    if (occ.heavy_lifting === 'frequent' || occ.heavy_lifting === 'daily') {
      tips.push({ icon: 'info', color: 'blue', text: 'Frequent heavy lifting. Ensure proper technique and ergonomic adjustments.' })
    }

    if (occ.travel_frequency === 'frequent' || occ.travel_frequency === 'constant') {
      tips.push({ icon: 'info', color: 'blue', text: 'Frequent travel can disrupt sleep and diet. Stay hydrated and maintain routines.' })
    }

    const countries = Array.isArray(trav.countries_visited) ? (trav.countries_visited as string[]).join(', ') : (trav.countries_visited as string) ?? ''
    const tropical = Array.isArray(trav.tropical_regions) ? (trav.tropical_regions as string[]).join(', ') : (trav.tropical_regions as string) ?? ''
    if (countries.length > 0 || tropical.length > 0) {
      tips.push({ icon: 'info', color: 'blue', text: 'International travel history noted. Ensure vaccinations are up to date.' })
    }

    return tips
  }, [state])
}