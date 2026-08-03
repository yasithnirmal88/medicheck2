export interface Anthropometrics {
  heightCm: number | null
  weightKg: number | null
  waistCm: number | null
  hipCm: number | null
  dob: string | null
}

export interface HealthCalculations {
  age: number | null
  bmi: number | null
  bmiCategory: BmiCategory | null
  waistHipRatio: number | null
  idealWeightRange: { min: number; max: number } | null
}

export type BmiCategory =
  | 'Underweight'
  | 'Normal'
  | 'Overweight'
  | 'Obese'

export function calcAge(dateOfBirth?: string): number | null {
  if (!dateOfBirth) return null
  const dob = new Date(dateOfBirth)
  if (Number.isNaN(dob.getTime())) return null
  const now = new Date()
  let age = now.getFullYear() - dob.getFullYear()
  const m = now.getMonth() - dob.getMonth()
  if (m < 0 || (m === 0 && now.getDate() < dob.getDate())) age -= 1
  return age
}

export function calcBMI(weightKg: number | null, heightCm: number | null): number | null {
  if (!weightKg || !heightCm) return null
  const m = heightCm / 100
  const bmi = weightKg / (m * m)
  return Math.round(bmi * 10) / 10
}

export function bmiCategory(bmi: number | null): BmiCategory | null {
  if (bmi === null) return null
  if (bmi < 18.5) return 'Underweight'
  if (bmi < 25) return 'Normal'
  if (bmi < 30) return 'Overweight'
  return 'Obese'
}

export function calcWaistHipRatio(waist: number | null, hip: number | null): number | null {
  if (!waist || !hip) return null
  return Math.round((waist / hip) * 100) / 100
}

export function calcIdealWeight(heightCm: number | null): { min: number; max: number } | null {
  if (!heightCm) return null
  const heightMeters = heightCm / 100
  const min = 18.5 * heightMeters * heightMeters
  const max = 24.9 * heightMeters * heightMeters
  return { min: Math.round(min * 10) / 10, max: Math.round(max * 10) / 10 }
}

export function bmiCategoryTone(category: BmiCategory | null) {
  if (!category || category === 'Normal') return { color: 'text-emerald-600', ring: 'bg-emerald-500' }
  if (category === 'Underweight') return { color: 'text-amber-600', ring: 'bg-amber-500' }
  if (category === 'Overweight') return { color: 'text-amber-600', ring: 'bg-amber-500' }
  return { color: 'text-red-500', ring: 'bg-red-500' }
}

export function computeMetrics(metrics: { heightCm?: number | null; weightKg?: number | null; waistCm?: number | null; hipCm?: number | null; gender?: string | null; dateOfBirth?: string | null }): HealthCalculations {
  const height = metrics.heightCm ?? null
  const weight = metrics.weightKg ?? null
  const waist = metrics.waistCm ?? null
  const hip = metrics.hipCm ?? null
  const heightNum = typeof height === 'number' && !Number.isNaN(height) ? height : null
  const weightNum = typeof weight === 'number' && !Number.isNaN(weight) ? weight : null
  const waistNum = typeof waist === 'number' && !Number.isNaN(waist) ? waist : null
  const hipNum = typeof hip === 'number' && !Number.isNaN(hip) ? hip : null
  return {
    age: calcAge(metrics.dateOfBirth ?? undefined),
    bmi: calcBMI(weightNum, heightNum),
    bmiCategory: bmiCategory(calcBMI(weightNum, heightNum)),
    waistHipRatio: calcWaistHipRatio(waistNum, hipNum),
    idealWeightRange: calcIdealWeight(heightNum),
  }
}