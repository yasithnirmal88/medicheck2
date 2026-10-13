/**
 * Phase 10 — TanStack Query hooks for the interoperability feature.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchFhirPatientBundle,
  fetchFhirSessionBundle,
  fetchExportHistory,
  fetchSdgExport,
  fetchSdgCsv,
  fetchCareContinuity,
  fetchFacilities,
  fetchFacility,
  createFacility,
  fetchReferrals,
  fetchReferral,
  createReferral,
  recordFacilityFeedback,
  fetchChwQueue,
  type AnalyticsFilters,
  type CreateReferralRequest,
  type FacilityCreateRequest,
  type FacilityFeedbackRequest,
  type ReferralStatus,
} from '../api/interopService'

export const interopKeys = {
  fhirPatient: (id: string) => ['interop', 'fhir', 'patient', id] as const,
  fhirSession: (id: string) => ['interop', 'fhir', 'session', id] as const,
  exportHistory: () => ['interop', 'exports'] as const,
  sdg: (filters?: AnalyticsFilters) => ['interop', 'sdg', filters ?? {}] as const,
  careContinuity: (filters?: AnalyticsFilters) =>
    ['interop', 'care-continuity', filters ?? {}] as const,
  facilities: () => ['interop', 'facilities'] as const,
  facility: (id: string) => ['interop', 'facilities', id] as const,
  referrals: (status?: ReferralStatus) =>
    ['interop', 'referrals', status ?? 'all'] as const,
  referral: (id: string) => ['interop', 'referrals', id] as const,
  chwQueue: () => ['interop', 'chw-queue'] as const,
}

export const useFhirPatientBundle = (patientId: string | null) =>
  useQuery({
    queryKey: interopKeys.fhirPatient(patientId ?? ''),
    queryFn: () => fetchFhirPatientBundle(patientId!),
    enabled: !!patientId,
  })

export const useFhirSessionBundle = (sessionId: string | null) =>
  useQuery({
    queryKey: interopKeys.fhirSession(sessionId ?? ''),
    queryFn: () => fetchFhirSessionBundle(sessionId!),
    enabled: !!sessionId,
  })

export const useExportHistory = () =>
  useQuery({ queryKey: interopKeys.exportHistory(), queryFn: fetchExportHistory })

export const useSdgExport = (filters?: AnalyticsFilters) =>
  useQuery({ queryKey: interopKeys.sdg(filters), queryFn: () => fetchSdgExport(filters) })

export const useSdgCsv = (filters?: AnalyticsFilters, enabled = false) =>
  useQuery({
    queryKey: [...interopKeys.sdg(filters), 'csv'],
    queryFn: () => fetchSdgCsv(filters),
    enabled,
  })

export const useCareContinuity = (filters?: AnalyticsFilters) =>
  useQuery({
    queryKey: interopKeys.careContinuity(filters),
    queryFn: () => fetchCareContinuity(filters),
  })

export const useFacilities = () =>
  useQuery({ queryKey: interopKeys.facilities(), queryFn: fetchFacilities })

export const useFacility = (id: string | null) =>
  useQuery({
    queryKey: interopKeys.facility(id ?? ''),
    queryFn: () => fetchFacility(id!),
    enabled: !!id,
  })

export const useCreateFacility = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: FacilityCreateRequest) => createFacility(req),
    onSuccess: () => qc.invalidateQueries({ queryKey: interopKeys.facilities() }),
  })
}

export const useReferrals = (status?: ReferralStatus) =>
  useQuery({
    queryKey: interopKeys.referrals(status),
    queryFn: () => fetchReferrals(status),
  })

export const useReferral = (id: string | null) =>
  useQuery({
    queryKey: interopKeys.referral(id ?? ''),
    queryFn: () => fetchReferral(id!),
    enabled: !!id,
  })

export const useCreateReferral = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: CreateReferralRequest) => createReferral(req),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['interop', 'referrals'] }),
  })
}

export const useRecordFacilityFeedback = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      referralId,
      req,
    }: {
      referralId: string
      req: FacilityFeedbackRequest
    }) => recordFacilityFeedback(referralId, req),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: interopKeys.referral(data.id) })
      qc.invalidateQueries({ queryKey: ['interop', 'referrals'] })
    },
  })
}

export const useChwQueue = () =>
  useQuery({ queryKey: interopKeys.chwQueue(), queryFn: fetchChwQueue })
