/**
 * Phase 10 — Interoperability, Health-System Integration & Outcome Feedback.
 *
 * API layer for FHIR export, SDG export, care-continuity analytics, the
 * facility registry, referral management, and the AI-assisted CHW queue.
 *
 * All exports are consent-aware, RBAC-controlled, audited, and (for population
 * outputs) de-identified + small-cell-suppressed. AI assistance never
 * determines clinical risk or diagnosis.
 */
import api from '@/lib/api'

// ── FHIR ──────────────────────────────────────────────────────────────

export interface FhirIdentifier {
  system?: string
  value?: string
}

export interface FhirExtension {
  url: string
  valueString?: string
}

export interface FhirResource {
  resourceType: string
  id?: string
  [key: string]: unknown
}

export interface FhirBundleEntry {
  fullUrl?: string
  resource: FhirResource
}

export interface FhirBundle {
  resourceType: 'Bundle'
  type: 'collection' | 'searchset' | 'document' | 'transaction'
  id: string
  timestamp: string
  entry: FhirBundleEntry[]
}

export interface FhirExportManifest {
  export_id: string
  export_type: string
  format: string
  requested_by_user_id: string
  patient_user_id: string
  resource_types: string[]
  source_trace_ids: string[]
  schema_version: string
  status: string
  status_reason: string | null
  consent_id: string | null
  item_count: number
  created_at: string
}

export interface FhirExportResponse {
  bundle: FhirBundle
  manifest: FhirExportManifest
  transparency_notice: string
}

export interface ExportHistoryItem {
  id: string
  export_type: string
  format: string
  requested_by_user_id: string
  patient_user_id: string | null
  resource_types: string[]
  source_trace_ids: string[]
  schema_version: string
  status: string
  status_reason: string | null
  consent_id: string | null
  item_count: number
  created_at: string
}

export interface ExportHistoryResponse {
  items: ExportHistoryItem[]
  total: number
}

export const fetchFhirPatientBundle = async (
  patientId: string
): Promise<FhirExportResponse> => {
  const { data } = await api.get<FhirExportResponse>(
    `/interoperability/fhir/patient/${patientId}`
  )
  return data
}

export const fetchFhirSessionBundle = async (
  sessionId: string
): Promise<FhirExportResponse> => {
  const { data } = await api.get<FhirExportResponse>(
    `/interoperability/fhir/session/${sessionId}`
  )
  return data
}

export const fetchExportHistory = async (): Promise<ExportHistoryResponse> => {
  const { data } = await api.get<ExportHistoryResponse>(
    '/interoperability/exports'
  )
  return data
}

// ── SDG export ────────────────────────────────────────────────────────

export interface SdgRow {
  indicator: string
  sdg_target: string
  indicator_type: 'official' | 'medicheck-aligned-proxy'
  period: string
  geography: string | null
  population_group: string | null
  value: number | null
  denominator: number | null
  numerator: number | null
  suppression_status: string
  methodology: string
  limitations: string
}

export interface SdgExportResponse {
  format: 'json' | 'csv'
  rows: SdgRow[]
  generated_at: string
  privacy_threshold: number
  disclaimer: string
}

export interface AnalyticsFilters {
  start_date?: string
  end_date?: string
  body_system_id?: string
  language?: string
  input_type?: string
}

export const fetchSdgExport = async (
  filters?: AnalyticsFilters
): Promise<SdgExportResponse> => {
  const { data } = await api.get<SdgExportResponse>('/interoperability/sdg', {
    params: filters,
  })
  return data
}

export const fetchSdgCsv = async (
  filters?: AnalyticsFilters
): Promise<string> => {
  const { data } = await api.get<string>('/interoperability/sdg/csv', {
    params: filters,
    responseType: 'text',
    transformResponse: (r) => r,
  })
  return data
}

// ── Care continuity ──────────────────────────────────────────────────

export interface CareFunnelStage {
  stage: string
  count: number
  suppressed: boolean
}

export interface CareContinuityMetrics {
  screened: number
  flagged: number
  referred: number
  referral_received: number
  appointment_scheduled: number
  care_received: number
  followup_completed: number
  lost_to_followup: number
  referral_completion_rate: number | null
  followup_completion_rate: number | null
  drop_off_rate: number | null
  median_time_to_care_days: number | null
  chw_assisted_completion_rate: number | null
}

export interface CareContinuityResponse {
  funnel: CareFunnelStage[]
  metrics: CareContinuityMetrics
  generated_at: string
  privacy_threshold: number
  disclaimer: string
}

export const fetchCareContinuity = async (
  filters?: AnalyticsFilters
): Promise<CareContinuityResponse> => {
  const { data } = await api.get<CareContinuityResponse>(
    '/interoperability/care-continuity',
    { params: filters }
  )
  return data
}

// ── Facilities ────────────────────────────────────────────────────────

export interface FacilityService {
  id: string
  facility_id: string
  service_type: string | null
  name: string | null
  is_active: boolean
}

export interface Facility {
  id: string
  code: string
  name: string
  service_type: string | null
  region: string | null
  contact_channel: string | null
  availability_status: string
  is_active: boolean
  description: string | null
  services: FacilityService[]
}

export interface FacilityListResponse {
  items: Facility[]
  total: number
}

export interface FacilityCreateRequest {
  code: string
  name: string
  service_type?: string
  region?: string
  contact_channel?: string
  availability_status?: string
  description?: string
}

export const fetchFacilities = async (): Promise<FacilityListResponse> => {
  const { data } = await api.get<FacilityListResponse>('/facilities')
  return data
}

export const fetchFacility = async (id: string): Promise<Facility> => {
  const { data } = await api.get<Facility>(`/facilities/${id}`)
  return data
}

export const createFacility = async (
  req: FacilityCreateRequest
): Promise<Facility> => {
  const { data } = await api.post<Facility>('/facilities', req)
  return data
}

// ── Referrals ─────────────────────────────────────────────────────────

export type ReferralStatus =
  | 'pending'
  | 'acknowledged'
  | 'sent'
  | 'received'
  | 'accepted'
  | 'scheduled'
  | 'attended'
  | 'completed'
  | 'declined'
  | 'cancelled'
  | 'expired'
  | 'lost_to_followup'
  | 'unable_to_access'

export type ReceivingStatus =
  | 'pending'
  | 'received'
  | 'accepted'
  | 'declined'
  | 'completed'

export interface Referral {
  id: string
  patient_user_id: string
  originating_session_id: string | null
  recommendation_id: string | null
  recommendation_category: string | null
  referral_type: string
  status: ReferralStatus
  receiving_status: ReceivingStatus
  facility_id: string | null
  facility_name: string | null
  assigned_chw_user_id: string | null
  patient_acknowledged: boolean
  notes: string | null
  scheduled_for: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface ReferralListResponse {
  items: Referral[]
  total: number
}

export interface CreateReferralRequest {
  originating_session_id: string
  recommendation_id: string
  referral_type: string
  assigned_chw_user_id?: string
}

export interface FacilityFeedbackRequest {
  receiving_status: ReceivingStatus
  notes?: string
}

export const fetchReferrals = async (
  status?: ReferralStatus
): Promise<ReferralListResponse> => {
  const { data } = await api.get<ReferralListResponse>('/referrals', {
    params: status ? { status } : undefined,
  })
  return data
}

export const fetchReferral = async (id: string): Promise<Referral> => {
  const { data } = await api.get<Referral>(`/referrals/${id}`)
  return data
}

export const createReferral = async (
  req: CreateReferralRequest
): Promise<Referral> => {
  const { data } = await api.post<Referral>('/referrals', req)
  return data
}

export const recordFacilityFeedback = async (
  referralId: string,
  req: FacilityFeedbackRequest
): Promise<Referral> => {
  const { data } = await api.patch<Referral>(
    `/referrals/${referralId}/feedback`,
    req
  )
  return data
}

// ── CHW queue ─────────────────────────────────────────────────────────

export interface ChwQueueTask {
  referral_id: string
  patient_user_id: string
  referral_age_days: number
  overdue: boolean
  missing_follow_up: boolean
  rank: number
  score: number
  rationale: string
}

export interface ChwQueueResponse {
  available: boolean
  ranked_tasks: ChwQueueTask[]
  provider: string
  prompt_version: string
  transparency_notice: string
  quality_status: string
  generated_at: string
}

export const fetchChwQueue = async (): Promise<ChwQueueResponse> => {
  const { data } = await api.get<ChwQueueResponse>('/chw/queue')
  return data
}
