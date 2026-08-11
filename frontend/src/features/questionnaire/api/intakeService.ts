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
}

export interface IntakeExtractRequest {
  session_id?: string
  text: string
}

/**
 * Extract structured observations + candidate indicators from patient free text.
 * Never throws on AI unavailability — returns `available=false` so the caller
 * can keep the standard questionnaire path working.
 */
export const extractIntake = async (
  payload: IntakeExtractRequest,
): Promise<IntakeResponse> => {
  const res = await api.post<IntakeResponse>('/ai/intake/extract', payload)
  return res.data
}
