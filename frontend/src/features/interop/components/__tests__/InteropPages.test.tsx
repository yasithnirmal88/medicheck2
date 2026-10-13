/**
 * Phase 10 — Interoperability frontend tests.
 *
 * Covers: FHIR export UI, export authorization states, SDG dashboard,
 * privacy badges, referral status, facility feedback, CHW queue, and
 * error states. Mocks the API layer; no real HTTP calls.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { InteroperabilityDashboardPage } from '../../pages/InteroperabilityDashboardPage'
import { SdgDashboardPage } from '../../pages/SdgDashboardPage'
import { CareContinuityPage } from '../../pages/CareContinuityPage'
import { FacilitiesPage } from '../../pages/FacilitiesPage'
import { ChwQueuePage } from '../../pages/ChwQueuePage'
import type {
  FhirExportResponse,
  ExportHistoryResponse,
  SdgExportResponse,
  CareContinuityResponse,
  FacilityListResponse,
  ReferralListResponse,
  ChwQueueResponse,
} from '../../api/interopService'

const apiMocks = vi.hoisted(() => ({
  fetchFhirPatientBundle: vi.fn(),
  fetchExportHistory: vi.fn(),
  fetchSdgExport: vi.fn(),
  fetchSdgCsv: vi.fn(),
  fetchCareContinuity: vi.fn(),
  fetchFacilities: vi.fn(),
  fetchFacility: vi.fn(),
  createFacility: vi.fn(),
  fetchReferrals: vi.fn(),
  fetchReferral: vi.fn(),
  createReferral: vi.fn(),
  recordFacilityFeedback: vi.fn(),
  fetchChwQueue: vi.fn(),
}))

vi.mock('../../api/interopService', () => apiMocks)

function renderPage(node: React.ReactNode) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({
          defaultOptions: { queries: { retry: false, staleTime: 0 } },
        })
      }
    >
      {node}
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

const fhirBundle: FhirExportResponse = {
  bundle: {
    resourceType: 'Bundle',
    type: 'collection',
    id: 'bundle-123',
    timestamp: '2026-08-15T10:00:00Z',
    entry: [
      { resource: { resourceType: 'Patient', id: 'p1' } },
      { resource: { resourceType: 'DiagnosticReport', id: 'dr1' } },
    ],
  },
  manifest: {
    export_id: 'exp-123',
    export_type: 'patient_bundle',
    format: 'fhir-r4-json',
    requested_by_user_id: 'u1',
    patient_user_id: 'p1',
    resource_types: ['Patient', 'DiagnosticReport', 'Observation'],
    source_trace_ids: ['trace-abc'],
    schema_version: '4.0.1',
    status: 'completed',
    status_reason: null,
    consent_id: 'consent-1',
    item_count: 2,
    created_at: '2026-08-15T10:00:00Z',
  },
  transparency_notice: 'AI assistance does not determine clinical risk.',
}

const emptyHistory: ExportHistoryResponse = { items: [], total: 0 }

describe('InteroperabilityDashboardPage', () => {
  it('shows transparency notice', async () => {
    apiMocks.fetchExportHistory.mockResolvedValue(emptyHistory)
    renderPage(<InteroperabilityDashboardPage />)
    expect(
      await screen.findByText(/authorized healthcare interoperability/i)
    ).toBeInTheDocument()
  })

  it('renders FHIR bundle after export trigger', async () => {
    apiMocks.fetchExportHistory.mockResolvedValue(emptyHistory)
    apiMocks.fetchFhirPatientBundle.mockResolvedValue(fhirBundle)
    renderPage(<InteroperabilityDashboardPage />)
    const input = screen.getByPlaceholderText('Patient ID')
    fireEvent.change(input, { target: { value: 'p1' } })
    fireEvent.click(screen.getByRole('button', { name: /export fhir/i }))
    await waitFor(() => {
      expect(screen.getByText(/2 resources/i)).toBeInTheDocument()
    })
    expect(screen.getByText('FHIR 4.0.1')).toBeInTheDocument()
  })

  it('shows denied error state when export fails', async () => {
    apiMocks.fetchExportHistory.mockResolvedValue(emptyHistory)
    apiMocks.fetchFhirPatientBundle.mockRejectedValue(new Error('403'))
    renderPage(<InteroperabilityDashboardPage />)
    fireEvent.change(screen.getByPlaceholderText('Patient ID'), {
      target: { value: 'p2' },
    })
    fireEvent.click(screen.getByRole('button', { name: /export fhir/i }))
    await waitFor(() => {
      expect(screen.getByText(/Export denied/i)).toBeInTheDocument()
    })
  })

  it('shows export history rows when present', async () => {
    apiMocks.fetchExportHistory.mockResolvedValue({
      items: [
        {
          id: 'exp-123',
          export_type: 'patient_bundle',
          format: 'fhir-r4-json',
          requested_by_user_id: 'u1',
          patient_user_id: 'p1',
          resource_types: ['Patient', 'Observation'],
          source_trace_ids: [],
          schema_version: '4.0.1',
          status: 'completed',
          status_reason: null,
          consent_id: 'c1',
          item_count: 5,
          created_at: '2026-08-15T10:00:00Z',
        },
      ],
      total: 1,
    })
    renderPage(<InteroperabilityDashboardPage />)
    await waitFor(() => {
      expect(screen.getAllByText((_, node) => !!node?.textContent?.includes('export(s) on record')).length).toBeGreaterThan(0)
    })
  })
})

const sdgData: SdgExportResponse = {
  format: 'json',
  rows: [
    {
      indicator: 'NCD screening coverage',
      sdg_target: 'sdg-3-4',
      indicator_type: 'medicheck-aligned-proxy',
      period: '2026',
      geography: null,
      population_group: null,
      value: 75.0,
      denominator: 200,
      numerator: 150,
      suppression_status: 'ok',
      methodology: 'completed assessments / eligible population',
      limitations: 'Not an official UN SDG indicator.',
    },
    {
      indicator: 'Referral completion',
      sdg_target: 'sdg-3-8',
      indicator_type: 'medicheck-aligned-proxy',
      period: '2026',
      geography: null,
      population_group: null,
      value: null,
      denominator: null,
      numerator: null,
      suppression_status: 'suppressed',
      methodology: 'completed referrals / total referrals',
      limitations: 'Small cohort suppressed.',
    },
  ],
  generated_at: '2026-08-15T10:00:00Z',
  privacy_threshold: 10,
  disclaimer: 'Aggregated and de-identified.',
}

describe('SdgDashboardPage', () => {
  it('renders privacy badge + indicators + methodology', async () => {
    apiMocks.fetchSdgExport.mockResolvedValue(sdgData)
    renderPage(<SdgDashboardPage />)
    expect(await screen.findByText(/k-anonymity ≥ 10/i)).toBeInTheDocument()
    expect(screen.getByText('NCD screening coverage')).toBeInTheDocument()
    expect(screen.getAllByText('(proxy)').length).toBeGreaterThan(0)
    expect(
      screen.getByText('completed assessments / eligible population')
    ).toBeInTheDocument()
  })

  it('shows suppressed state for small cohorts', async () => {
    apiMocks.fetchSdgExport.mockResolvedValue(sdgData)
    renderPage(<SdgDashboardPage />)
    await screen.findByText('Referral completion')
    expect(screen.getAllByText('Suppressed').length).toBeGreaterThan(0)
  })

  it('shows error state when research role absent', async () => {
    apiMocks.fetchSdgExport.mockRejectedValue(new Error('403'))
    renderPage(<SdgDashboardPage />)
    await waitFor(() => {
      expect(screen.getByText(/could not load sdg analytics/i)).toBeInTheDocument()
    })
  })
})

const careData: CareContinuityResponse = {
  funnel: [
    { stage: 'screened', count: 100, suppressed: false },
    { stage: 'flagged', count: 40, suppressed: false },
    { stage: 'referred', count: 20, suppressed: false },
    { stage: 'referral_received', count: 15, suppressed: false },
    { stage: 'appointment_scheduled', count: 10, suppressed: false },
    { stage: 'care_received', count: 8, suppressed: false },
    { stage: 'followup_completed', count: 5, suppressed: false },
  ],
  metrics: {
    screened: 100,
    flagged: 40,
    referred: 20,
    referral_received: 15,
    appointment_scheduled: 10,
    care_received: 8,
    followup_completed: 5,
    lost_to_followup: 3,
    referral_completion_rate: 40.0,
    followup_completion_rate: 25.0,
    drop_off_rate: 60.0,
    median_time_to_care_days: 14,
    chw_assisted_completion_rate: 30.0,
  },
  generated_at: '2026-08-15T10:00:00Z',
  privacy_threshold: 10,
  disclaimer: 'Outcome data does not alter clinical scores.',
}

describe('CareContinuityPage', () => {
  it('renders funnel stages + metric cards', async () => {
    apiMocks.fetchCareContinuity.mockResolvedValue(careData)
    renderPage(<CareContinuityPage />)
    expect(await screen.findByText('Referral completion')).toBeInTheDocument()
    expect(screen.getByText('screened')).toBeInTheDocument()
    expect(screen.getByText('care received')).toBeInTheDocument()
  })

  it('shows transparency notice about outcomes', async () => {
    apiMocks.fetchCareContinuity.mockResolvedValue(careData)
    renderPage(<CareContinuityPage />)
    expect(
      await screen.findByText(/does not alter clinical scores/i)
    ).toBeInTheDocument()
  })
})

const facilityData: FacilityListResponse = {
  items: [
    {
      id: 'f1',
      code: 'FAC-001',
      name: 'Central Clinic',
      service_type: 'general',
      region: 'Colombo',
      contact_channel: 'phone',
      availability_status: 'available',
      is_active: true,
      description: null,
      services: [{ id: 's1', facility_id: 'f1', service_type: 'cardiology', name: 'Cardiology', is_active: true }],
    },
  ],
  total: 1,
}

const referralData: ReferralListResponse = {
  items: [
    {
      id: 'ref-1',
      patient_user_id: 'p1',
      originating_session_id: 'sess-1',
      recommendation_id: 'rec-1',
      recommendation_category: 'screening',
      referral_type: 'specialist_referral',
      status: 'sent',
      receiving_status: 'pending',
      facility_id: 'f1',
      facility_name: 'Central Clinic',
      assigned_chw_user_id: null,
      patient_acknowledged: false,
      notes: null,
      scheduled_for: null,
      completed_at: null,
      created_at: '2026-08-15T10:00:00Z',
      updated_at: '2026-08-15T10:00:00Z',
    },
  ],
  total: 1,
}

describe('FacilitiesPage', () => {
  it('renders facility registry + referral status', async () => {
    apiMocks.fetchFacilities.mockResolvedValue(facilityData)
    apiMocks.fetchReferrals.mockResolvedValue(referralData)
    renderPage(<FacilitiesPage />)
    expect((await screen.findAllByText('Central Clinic')).length).toBeGreaterThan(0)
    expect(screen.getByText('specialist referral')).toBeInTheDocument()
  })

  it('renders receiving-status feedback control for active referrals', async () => {
    apiMocks.fetchFacilities.mockResolvedValue(facilityData)
    apiMocks.fetchReferrals.mockResolvedValue(referralData)
    renderPage(<FacilitiesPage />)
    await screen.findAllByText('Central Clinic')
    expect(screen.getByRole('button', { name: /update/i })).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  it('shows empty state when no facilities', async () => {
    apiMocks.fetchFacilities.mockResolvedValue({ items: [], total: 0 })
    apiMocks.fetchReferrals.mockResolvedValue({ items: [], total: 0 })
    renderPage(<FacilitiesPage />)
    expect(await screen.findByText(/no facilities registered/i)).toBeInTheDocument()
  })
})

const chwQueue: ChwQueueResponse = {
  available: true,
  ranked_tasks: [
    {
      referral_id: 'ref-1',
      patient_user_id: 'p1',
      referral_age_days: 7,
      overdue: true,
      missing_follow_up: false,
      rank: 1,
      score: 0.9,
      rationale: 'Referral is overdue for follow-up.',
    },
    {
      referral_id: 'ref-2',
      patient_user_id: 'p2',
      referral_age_days: 2,
      overdue: false,
      missing_follow_up: true,
      rank: 2,
      score: 0.6,
      rationale: 'Missing follow-up contact.',
    },
  ],
  provider: 'operational-stub',
  prompt_version: '1.0-operational',
  transparency_notice: 'AI ranks by operational factors only.',
  quality_status: 'valid',
  generated_at: '2026-08-15T10:00:00Z',
}

describe('ChwQueuePage', () => {
  it('renders ranked tasks + operational rationale', async () => {
    apiMocks.fetchChwQueue.mockResolvedValue(chwQueue)
    renderPage(<ChwQueuePage />)
    expect(await screen.findByText('Referral is overdue for follow-up.')).toBeInTheDocument()
    expect(screen.getByText('Overdue')).toBeInTheDocument()
    expect(screen.getByText('Missing follow-up')).toBeInTheDocument()
  })

  it('shows AI boundary transparency notice', async () => {
    apiMocks.fetchChwQueue.mockResolvedValue(chwQueue)
    renderPage(<ChwQueuePage />)
    expect(
      await screen.findByText(/does NOT determine clinical urgency/i)
    ).toBeInTheDocument()
    // provider + prompt version + quality status render in the metadata row
    expect(await screen.findByText(/prompt v1.0-operational/i)).toBeInTheDocument()
  })

  it('shows error state for non-CHW users', async () => {
    apiMocks.fetchChwQueue.mockRejectedValue(new Error('403'))
    renderPage(<ChwQueuePage />)
    await waitFor(() => {
      expect(screen.getByText(/could not load the chw queue/i)).toBeInTheDocument()
    })
  })

  it('shows empty state when no tasks', async () => {
    apiMocks.fetchChwQueue.mockResolvedValue({ ...chwQueue, ranked_tasks: [] })
    renderPage(<ChwQueuePage />)
    expect(await screen.findByText(/no pending tasks/i)).toBeInTheDocument()
  })
})
