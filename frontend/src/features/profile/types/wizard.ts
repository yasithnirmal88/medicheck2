export type Gender = 'male' | 'female' | 'other' | 'prefer-not'

export interface PersonalData {
  first_name: string
  middle_name: string
  last_name: string
  date_of_birth: string
  gender: Gender | ''
  blood_group: string
  nationality: string
  ethnicity: string
  country: string
  state: string
  city: string
  marital_status: string
  education_level: string
  occupation: string
  industry: string
  preferred_language: string
  email: string
  phone: string
}

export interface BodyMeasurement {
  height_cm: string
  weight_kg: string
  waist_cm: string
  hip_cm: string
  body_fat_pct: string
  muscle_pct: string
  water_pct: string
  resting_heart_rate: string
  blood_pressure_systolic: string
  blood_pressure_diastolic: string
  body_temperature_c: string
  oxygen_saturation_pct: string
  blood_sugar_mgdl: string
  hba1c_pct: string
}

export interface LifestyleData {
  smoking: string
  alcohol: string
  drug_use: string
  caffeine_intake: string
  daily_water_intake: string
  screen_time: string
  driving_hours: string
}

export interface NutritionData {
  diet_type: string
  meals_per_day: string
  fast_food_frequency: string
  fruit_intake: string
  vegetable_intake: string
  red_meat: string
  fish: string
  sugar_intake: string
  salt_intake: string
  water_intake: string
  food_allergies: string
  supplements: string
}

export interface PhysicalActivityData {
  occupation_activity: string
  exercise_days: string
  exercise_duration: string
  exercise_types: string[]
  daily_step_count: string
}

export interface SleepData {
  avg_sleep_hours: string
  sleep_time: string
  wake_time: string
  snoring: string
  sleep_apnea: string
  night_awakenings: string
  daytime_sleepiness: string
  shift_worker: string
  sleep_quality: string
}

export interface MentalHealthData {
  stress_level: string
  anxiety: string
  depression_screening: string
  mood: string
  social_support: string
  meditation: string
  mindfulness: string
  work_life_balance: string
  burnout_risk: string
}

export interface MedicalHistoryEntry {
  id: string
  conditions: string[]
  diagnosis_date: string
  severity: string
  status: string
  notes: string
  surgeries_count: string
  hospital_admissions: string
  previous_fractures: string
  organ_transplants: string
}

export interface SurgeryEntry {
  id: string
  procedure: string
  date: string
  hospital: string
  reason: string
  outcome: string
}

export interface FamilyEntry {
  id: string
  relative: string
  diseases: string[]
  age_at_diagnosis: string
  current_status: string
  notes: string
}

export interface MedicationEntry {
  id: string
  medication: string
  dosage: string
  frequency: string
  reason: string
  start_date: string
  prescribing_doctor: string
  current_status: string
}

export interface AllergyEntry {
  id: string
  type: string
  substance: string
  severity: string
  reaction: string
  emergency_medication: string
}

export interface VaccinationEntry {
  id: string
  vaccine: string
  dose: string
  date: string
  provider: string
}

export interface WomenHealthData {
  pregnancy: string
  menstrual_cycle: string
  pcos: string
  menopause: string
  contraception: string
  pregnancy_history: string
}

export interface MenHealthData {
  prostate_issues: string
  testosterone_therapy: string
  urinary_symptoms: string
}

export interface LifestyleRiskData {
  seatbelt_use: string
  helmet_use: string
  sun_exposure: string
  driving_habits: string
  firearms: string
  occupational_hazards: string
  substance_exposure: string
}

export interface EnvironmentData {
  air_pollution: string
  water_source: string
  home_type: string
  pets: string
  mold_exposure: string
  chemical_exposure: string
  noise_pollution: string
}

export interface OccupationData {
  industry: string
  working_hours: string
  night_shifts: boolean
  travel_frequency: string
  heavy_lifting: string
  work_stress: string
  work_environment: string
}

export interface TravelData {
  countries_visited: string[]
  tropical_regions: string[]
  vaccinations_required: string
  recent_travel: string
}

export interface Consents {
  terms_accepted: boolean
  ai_consent: boolean
  research_consent: boolean
}

export interface WizardState {
  personal: PersonalData
  body: BodyMeasurement
  lifestyle: LifestyleData
  nutrition: NutritionData
  physical_activity: PhysicalActivityData
  sleep: SleepData
  mental_health: MentalHealthData
  conditions: MedicalHistoryEntry[]
  surgeries: SurgeryEntry[]
  family_history: FamilyEntry[]
  medications: MedicationEntry[]
  allergies: AllergyEntry[]
  vaccinations: VaccinationEntry[]
  women_health: WomenHealthData
  men_health: MenHealthData
  lifestyle_risks: LifestyleRiskData
  environment: EnvironmentData
  occupation: OccupationData
  travel: TravelData
  consents: Consents
}

export type SectionKey = keyof WizardState

export type StepSlice<K extends SectionKey> = WizardState[K]