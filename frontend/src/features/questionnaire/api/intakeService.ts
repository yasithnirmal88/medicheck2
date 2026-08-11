/**
 * Phase 3 — AI Clinical Intake API service.
 *
 * Boundaries: the AI is an INPUT INTERPRETATION layer only. It extracts
 * structured observations from patient free text and maps them to EXISTING
 * clinical indicators in the knowledge graph. It never diagnoses, scores, sets
 * severity, or invents clinical entities. The deterministic CDSE remains the
 * clinical decision layer.
 *
 * Unknown / hallucinated indicator IDs are rejected by the backend before they
 * can influence question selection. If AI is unavailable, `available=false`
 * is returned and the standard questionnaire remains functional.
 */

import api from '@/lib/api'

export type Polarity = 'positive' | 'negative' | 'uncertain'
export type Certainty = 'reported' | 'suspected' | 'uncertain'
export type Temporality = 'current' | 'recent' | 'historical' | 'recurring' | 'unknown'
export type ObservationType =
  | 'symptom'
  | 'history'
  | 'behavior'
  | 'measurement'
  | 'context'
  | 'other'

export interface IntakeObservation {
  id: string
  source_text: string
  normalized_concept: string
  observation_type: ObservationType
  certainty: Certainty
  temporality: Temporality
  polarity: Polarity
  severity_description: string | null
  duration: string | null
  frequency: string | null
  context: string | null
  body_system: string | null
  confidence: number
}

export interface IntakeCandidateIndicator {
  indicator_id: string
  confidence: number
  observation_ids: string[]
  reason: string
  uncertainty: string | null
  source: string
}

export interface IntakeCandidateQuestion {
  question_id: string
  question_code: string
  text: string
  question_group_id: string
  question_group_name: string
  body_system_id: string | null
  linked_indicator_ids: string[]
  source: 'cms'
}

export interface IntakeCandidateQuestionGroup {
  question_group_id: string
  code: string
  name: string
  body_system_id: string | null
  linked_indicator_ids: string[]
  question_count: number
  source: 'cms'
}

export interface IntakeClarification {
  text: string
  source: 'ai_generated' | 'cms'
  observation_id: string | null
  linked_indicator_id: string | null
  linked_question_id: string | null
}

export type IntakeLanguage = 'en' | 'si' | 'ta'
export type IntakeInputType = 'text' | 'voice'

export interface IntakeResponse {
  trace_id: string
  prompt_version: string
  observations: IntakeObservation[]
  candidate_indicators: IntakeCandidateIndicator[]
  candidate_question_groups: IntakeCandidateQuestionGroup[]
  candidate_questions: IntakeCandidateQuestion[]
  clarifications: IntakeClarification[]
  available: boolean
  message: string | null
  // Phase 5 — multilingual/voice traceability metadata.
  language: IntakeLanguage
  input_type: IntakeInputType
  detected_language: string | null
}

export interface IntakeExtractRequest {
  session_id?: string
  text: string
  language?: IntakeLanguage
  input_type?: IntakeInputType
}

export interface TranscribeResponse {
  transcript: string
  language: string
  detected_language: string | null
  confidence: number
}

export interface SupportedLanguage {
  code: IntakeLanguage
  label: string
}

export interface LanguagesResponse {
  languages: SupportedLanguage[]
  default: string
}

/**
 * Extract structured observations + candidate indicators from patient free text.
 * Never throws on AI unavailability — returns `available=false` so the caller
 * can keep the standard questionnaire path working.
 *
 * Phase 5: `language` carries the user-selected language; the backend also
 * performs best-effort script detection. Localized input always resolves to
 * the SAME canonical indicator IDs — the language layer is interface-only.
 */
export const extractIntake = async (
  payload: IntakeExtractRequest,
): Promise<IntakeResponse> => {
  const res = await api.post<IntakeResponse>('/ai/intake/extract', payload)
  return res.data
}

/**
 * Phase 5 — transcribe audio to text for patient review.
 * Audio is processed transiently (never stored). The transcript is returned
 * for the patient to review/edit BEFORE clinical interpretation.
 */
export const transcribeAudio = async (
  audioBlob: Blob,
  language: IntakeLanguage,
): Promise<TranscribeResponse> => {
  const form = new FormData()
  form.append('audio', audioBlob, 'recording.webm')
  form.append('language', language)
  const res = await api.post<TranscribeResponse>('/ai/intake/transcribe', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

/**
 * Phase 5 — list supported intake languages for the UI selector.
 */
export const fetchLanguages = async (): Promise<LanguagesResponse> => {
  const res = await api.get<LanguagesResponse>('/ai/intake/languages')
  return res.data
}
