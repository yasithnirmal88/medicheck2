import { z } from 'zod'

const stringField = z.string().trim()
const optionalString = stringField.optional()
const positiveNumber = z.string().trim().regex(/^\d+(\.\d+)?$/, 'Must be a valid number').optional()
const nonNegativeNumber = z.string().trim().regex(/^\d+(\.\d+)?$/, 'Must be a valid number').optional()

export const personalSchema = z.object({
  first_name: stringField.min(1, 'First name is required'),
  middle_name: optionalString,
  last_name: stringField.min(1, 'Last name is required'),
  date_of_birth: stringField.min(1, 'Date of birth is required'),
  gender: stringField.min(1, 'Gender is required'),
  blood_group: optionalString,
  nationality: optionalString,
  ethnicity: optionalString,
  country: stringField.min(1, 'Country is required'),
  state: optionalString,
  city: optionalString,
  marital_status: optionalString,
  education_level: optionalString,
  occupation: optionalString,
  industry: optionalString,
  preferred_language: optionalString,
  email: stringField.email('Invalid email').optional().or(z.literal('')),
  phone: optionalString,
})

export const bodySchema = z.object({
  height_cm: positiveNumber,
  weight_kg: positiveNumber,
  waist_cm: optionalString,
  hip_cm: optionalString,
  body_fat_pct: optionalString,
  muscle_pct: optionalString,
  water_pct: optionalString,
  resting_heart_rate: optionalString,
  blood_pressure_systolic: optionalString,
  blood_pressure_diastolic: optionalString,
  body_temperature_c: optionalString,
  oxygen_saturation_pct: optionalString,
  blood_sugar_mgdl: optionalString,
  hba1c_pct: optionalString,
})

export const lifestyleSchema = z.object({
  smoking: stringField,
  alcohol: stringField,
  drug_use: optionalString,
  caffeine_intake: optionalString,
  daily_water_intake: nonNegativeNumber,
  screen_time: nonNegativeNumber,
  driving_hours: nonNegativeNumber,
})

export const nutritionSchema = z.object({
  diet_type: stringField,
  meals_per_day: z.string().trim().regex(/^\d+$/, 'Must be a whole number'),
  fast_food_frequency: stringField,
  fruit_intake: nonNegativeNumber,
  vegetable_intake: nonNegativeNumber,
  red_meat: optionalString,
  fish: optionalString,
  sugar_intake: optionalString,
  salt_intake: optionalString,
  water_intake: nonNegativeNumber,
  food_allergies: optionalString,
  supplements: optionalString,
})

export const physicalActivitySchema = z.object({
  occupation_activity: stringField,
  exercise_days: z.string().trim().regex(/^\d+$/, 'Must be a whole number'),
  exercise_duration: optionalString,
  exercise_types: z.string().trim().optional(),
  daily_step_count: nonNegativeNumber,
})

export const sleepSchema = z.object({
  avg_sleep_hours: z.string().trim().regex(/^\d+(\.\d+)?$/, 'Must be a valid number'),
  sleep_time: optionalString,
  wake_time: optionalString,
  snoring: stringField,
  sleep_apnea: stringField,
  night_awakenings: stringField,
  daytime_sleepiness: stringField,
  shift_worker: stringField,
  sleep_quality: stringField,
})

export const mentalHealthSchema = z.object({
  stress_level: stringField,
  anxiety: stringField,
  depression_screening: stringField,
  mood: stringField,
  social_support: stringField,
  meditation: optionalString,
  mindfulness: optionalString,
  work_life_balance: stringField,
  burnout_risk: stringField,
})

const medicalHistoryEntrySchema = z.object({
  id: z.string(),
  conditions: z.array(z.string()).min(1, 'At least one condition is required'),
  diagnosis_date: optionalString,
  severity: optionalString,
  status: optionalString,
  notes: optionalString,
  surgeries_count: optionalString,
  hospital_admissions: optionalString,
  previous_fractures: optionalString,
  organ_transplants: optionalString,
})

export const conditionsSchema = z.array(medicalHistoryEntrySchema)

const surgeryEntrySchema = z.object({
  id: z.string(),
  procedure: stringField.min(1, 'Procedure is required'),
  date: optionalString,
  hospital: optionalString,
  reason: optionalString,
  outcome: optionalString,
})

export const surgeriesSchema = z.array(surgeryEntrySchema)

const familyEntrySchema = z.object({
  id: z.string(),
  relative: stringField.min(1, 'Relative is required'),
  diseases: z.array(z.string()).min(1, 'At least one disease is required'),
  age_at_diagnosis: optionalString,
  current_status: optionalString,
  notes: optionalString,
})

export const familyHistorySchema = z.array(familyEntrySchema)

const medicationEntrySchema = z.object({
  id: z.string(),
  medication: stringField.min(1, 'Medication is required'),
  dosage: optionalString,
  frequency: optionalString,
  reason: optionalString,
  start_date: optionalString,
  prescribing_doctor: optionalString,
  current_status: optionalString,
})

export const medicationsSchema = z.array(medicationEntrySchema)

const allergyEntrySchema = z.object({
  id: z.string(),
  type: stringField,
  substance: stringField.min(1, 'Substance is required'),
  severity: optionalString,
  reaction: optionalString,
  emergency_medication: optionalString,
})

export const allergiesSchema = z.array(allergyEntrySchema)

const vaccinationEntrySchema = z.object({
  id: z.string(),
  vaccine: stringField.min(1, 'Vaccine is required'),
  dose: optionalString,
  date: optionalString,
  provider: optionalString,
})

export const vaccinationsSchema = z.array(vaccinationEntrySchema)

export const womenHealthSchema = z.object({
  pregnancy: optionalString,
  menstrual_cycle: optionalString,
  pcos: optionalString,
  menopause: optionalString,
  contraception: optionalString,
  pregnancy_history: optionalString,
})

export const menHealthSchema = z.object({
  prostate_issues: optionalString,
  testosterone_therapy: optionalString,
  urinary_symptoms: optionalString,
})

export const lifestyleRisksSchema = z.object({
  seatbelt_use: stringField,
  helmet_use: optionalString,
  sun_exposure: stringField,
  driving_habits: optionalString,
  firearms: optionalString,
  occupational_hazards: optionalString,
  substance_exposure: optionalString,
})

export const environmentSchema = z.object({
  air_pollution: stringField,
  water_source: stringField,
  home_type: stringField,
  pets: optionalString,
  mold_exposure: optionalString,
  chemical_exposure: optionalString,
  noise_pollution: optionalString,
})

export const occupationSchema = z.object({
  industry: optionalString,
  working_hours: nonNegativeNumber,
  night_shifts: z.boolean(),
  travel_frequency: optionalString,
  heavy_lifting: optionalString,
  work_stress: stringField,
  work_environment: optionalString,
})

export const travelSchema = z.object({
  countries_visited: z.array(z.string()).default([]),
  tropical_regions: z.array(z.string()).default([]),
  vaccinations_required: optionalString,
  recent_travel: optionalString,
})

export const consentsSchema = z.object({
  terms_accepted: z.boolean().refine((v) => v === true, 'You must accept the terms'),
  ai_consent: z.boolean(),
  research_consent: z.boolean(),
})

export const sectionSchemas: Record<string, z.ZodType> = {
  personal: personalSchema,
  body: bodySchema,
  lifestyle: lifestyleSchema,
  nutrition: nutritionSchema,
  physical_activity: physicalActivitySchema,
  sleep: sleepSchema,
  mental_health: mentalHealthSchema,
  conditions: conditionsSchema,
  surgeries: surgeriesSchema,
  family_history: familyHistorySchema,
  medications: medicationsSchema,
  allergies: allergiesSchema,
  vaccinations: vaccinationsSchema,
  women_health: womenHealthSchema,
  men_health: menHealthSchema,
  lifestyle_risks: lifestyleRisksSchema,
  environment: environmentSchema,
  occupation: occupationSchema,
  travel: travelSchema,
  consents: consentsSchema,
}