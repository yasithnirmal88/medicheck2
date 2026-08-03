import type { WizardState } from '../types/wizard'

export const emptyString = ''

export function createDefaultState(): WizardState {
  return {
    personal: {
      first_name: '',
      middle_name: '',
      last_name: '',
      date_of_birth: '',
      gender: '',
      blood_group: '',
      nationality: '',
      ethnicity: '',
      country: '',
      state: '',
      city: '',
      marital_status: '',
      education_level: '',
      occupation: '',
      industry: '',
      preferred_language: '',
      email: '',
      phone: '',
      emergency_contact: '',
      emergency_phone: '',
      relationship: '',
      photo: '',
    },
    body: {
      height_cm: '',
      weight_kg: '',
      waist_cm: '',
      hip_cm: '',
      body_fat_pct: '',
      muscle_pct: '',
      water_pct: '',
      resting_heart_rate: '',
      blood_pressure_systolic: '',
      blood_pressure_diastolic: '',
      body_temperature_c: '',
      oxygen_saturation_pct: '',
      blood_sugar_mgdl: '',
      hba1c_pct: '',
    },
    lifestyle: {
      smoking: '',
      alcohol: '',
      drug_use: '',
      caffeine_intake: '',
      daily_water_intake: '',
      screen_time: '',
      driving_hours: '',
    },
    nutrition: {
      diet_type: '',
      meals_per_day: '',
      fast_food_frequency: '',
      fruit_intake: '',
      vegetable_intake: '',
      red_meat: '',
      fish: '',
      sugar_intake: '',
      salt_intake: '',
      water_intake: '',
      food_allergies: '',
      supplements: '',
    },
    physical_activity: {
      occupation_activity: '',
      exercise_days: '',
      exercise_duration: '',
      exercise_types: [],
      daily_step_count: '',
    },
    sleep: {
      avg_sleep_hours: '',
      sleep_time: '',
      wake_time: '',
      snoring: '',
      sleep_apnea: '',
      night_awakenings: '',
      daytime_sleepiness: '',
      shift_worker: '',
      sleep_quality: '',
    },
    mental_health: {
      stress_level: '',
      anxiety: '',
      depression_screening: '',
      mood: '',
      social_support: '',
      meditation: '',
      mindfulness: '',
      work_life_balance: '',
      burnout_risk: '',
    },
    conditions: [],
    surgeries: [],
    family_history: [],
    medications: [],
    allergies: [],
    vaccinations: [],
    women_health: {
      pregnancy: '',
      menstrual_cycle: '',
      pcos: '',
      menopause: '',
      contraception: '',
      pregnancy_history: '',
    },
    men_health: {
      prostate_issues: '',
      testosterone_therapy: '',
      urinary_symptoms: '',
    },
    lifestyle_risks: {
      seatbelt_use: '',
      helmet_use: '',
      sun_exposure: '',
      driving_habits: '',
      firearms: '',
      occupational_hazards: '',
      substance_exposure: '',
    },
    environment: {
      air_pollution: '',
      water_source: '',
      home_type: '',
      pets: '',
      mold_exposure: '',
      chemical_exposure: '',
      noise_pollution: '',
    },
    occupation: {
      industry: '',
      working_hours: '',
      night_shifts: false,
      travel_frequency: '',
      heavy_lifting: '',
      work_stress: '',
      work_environment: '',
    },
    travel: {
      countries_visited: [],
      tropical_regions: [],
      vaccinations_required: '',
      recent_travel: '',
    },
    emergency: {
      primary_name: '',
      primary_phone: '',
      primary_relationship: '',
      secondary_name: '',
      secondary_phone: '',
      secondary_relationship: '',
      hospital_preference: '',
      insurance_provider: '',
      organ_donor: '',
    },
    consents: {
      terms_accepted: false,
      ai_consent: false,
      research_consent: false,
    },
  }
}

export function mergeDraft(base: WizardState, draft: Partial<WizardState>): WizardState {
  const merged: Record<string, unknown> = { ...base }
  const keys = Object.keys(base) as (keyof WizardState)[]
  for (const key of keys) {
    const value = draft[key]
    if (value === undefined || value === null) continue
    if (typeof value === 'object' && !Array.isArray(value)) {
      merged[key as string] = { ...(base[key] as object), ...(value as object) }
    } else {
      merged[key as string] = value
    }
  }
  return merged as unknown as WizardState
}