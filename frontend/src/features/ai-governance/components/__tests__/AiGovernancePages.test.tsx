/**
 * Phase 11 — Governed AI Care Coordination & Equity Intelligence frontend tests.
 *
 * Covers: CHW suggestion display + disclaimer, equity insight display,
 * SDG narrative display, k-anonymity/privacy badges, review status, review
 * actions (approve/reject/edit), and loading/unavailable/error/no-data states.
 * Mocks the API layer; no real HTTP calls.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { ChwSuggestionsPage } from '../../pages/ChwSuggestionsPage'
import { EquityIntelligencePage } from '../../pages/EquityIntelligencePage'
import { SdgNarrativesPage } from '../../pages/SdgNarrativesPage'
import type {
  OperationalSuggestionBatchResponse,
  OperationalSuggestionRecord,
  EquityInsightResponse,
  PopulationInsightRecord,
  SdgNarrativeResponse,
  InsightReviewResponse,
} from '../../api/aiGovernanceService'

const apiMocks = vi.hoisted(() => ({
  generateOperationalSuggestions: vi.fn(),
  fetchOperationalSuggestions: vi.fn(),
  generateEquityInsight: vi.fn(),
  fetchEquityInsights: vi.fn(),
  generateSdgNarratives: vi.fn(),
  fetchSdgNarratives: vi.fn(),
  reviewOperationalSuggestion: vi.fn(),
  publishOperationalSuggestion: vi.fn(),
  reviewPopulationInsight: vi.fn(),
  publishPopulationInsight: vi.fn(),
}))

vi.mock('../../api/aiGovernanceService', () => apiMocks)

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

// ── Helpers ───────────────────────────────────────────────────────────

const operationalBatch = (): OperationalSuggestionBatchResponse => ({
  available: true,
  suggestions: [
    {
      task_id: 'task-1',
      operational_reason_codes: ['overdue', 'aged_referral'],
      explanation: 'Operational priority: follow-up is overdue by 3 day(s).',
      operational_priority_score: 0.5,
      confidence: 0.8,
      requires_human_review: true,
    },
  ],
  provider: 'stub',
  model: '',
  prompt_version: '1.0-operational-phase11',
  quality_status: 'valid',
  quality_reason: null,
  transparency_notice:
    'AI suggestions are administrative assistance only. They do not determine clinical priority, urgency, or diagnosis.',
  records: [],
})

const operationalRecord = (
  status: OperationalSuggestionRecord['review_status'] = 'pending_review'
): OperationalSuggestionRecord => ({
  id: 'rec-1',
  chw_user_id: 'chw-1',
  task_id: 'task-1',
  operational_reason_codes: ['overdue'],
  explanation: 'Operational priority: follow-up is overdue by 3 day(s).',
  operational_priority_score: 0.5,
  requires_human_review: true,
  provider: 'stub',
  model: '',
  prompt_version: '1.0-operational-phase11',
  quality_status: 'valid',
  quality_reason: null,
  review_status: status,
  reviewer_id: null,
  reviewer_comment: null,
  edited_output: null,
  approved_at: null,
  created_at: '2026-08-12T00:00:00Z',
})

const equityResponse = (): EquityInsightResponse => ({
  available: true,
  insight: {
    observed_findings: [
      {
        statement: 'Tamil language completion (50%) is lower than English (80%).',
        metric_labels: ['tamil language completion', 'english completion'],
      },
    ],
    possible_interpretations: [
      {
        interpretation: 'Lower Tamil completion may indicate an accessibility gap.',
        is_observed: false,
      },
    ],
    limitations:
      'These observations describe aggregate access patterns only. They do not infer disease prevalence or causation.',
    requires_human_review: true,
  },
  record: {
    id: 'eq-1',
    insight_type: 'equity',
    target: 'language',
    period_start: '2026-01-01',
    period_end: '2026-08-12',
    narrative: 'narrative',
    observed_findings: null,
    possible_interpretations: null,
    limitations: 'l',
    requires_human_review: true,
    provider: 'stub',
    model: '',
    prompt_version: '1.0-equity-phase11',
    quality_status: 'valid',
    quality_reason: null,
    review_status: 'pending_review',
    reviewer_id: null,
    reviewer_comment: null,
    edited_output: null,
    approved_at: null,
    created_at: '2026-08-12T00:00:00Z',
  },
  provider: 'stub',
  prompt_version: '1.0-equity-phase11',
  quality_status: 'valid',
  quality_reason: null,
  transparency_notice:
    'AI-generated population summaries are derived from aggregated, de-identified metrics and require human review.',
})

const sdgResponse = (): SdgNarrativeResponse => ({
  available: true,
  narratives: [
    {
      target: '3.4',
      reporting_period: '2026-01-01 to 2026-08-12',
      population_scope: 'MediCheck platform users (de-identified aggregate)',
      metrics_used: ['sdg-3-4-screening'],
      observed_trends: ['sdg-3-4-screening: 0.7'],
      limitations:
        'These are platform-derived monitoring indicators aligned with SDG targets. They do not prove an SDG target has been achieved.',
      possible_operational_interpretation:
        'Any decrease in completion may indicate a care-continuity bottleneck.',
      requires_human_review: true,
    },
  ],
  records: [],
  provider: 'stub',
  prompt_version: '1.0-sdg-narrative-phase11',
  quality_status: 'valid',
  quality_reason: null,
  transparency_notice:
    'AI-generated SDG narratives describe supplied aggregate metrics only and require human review.',
})

const populationRecord = (
  status: PopulationInsightRecord['review_status'] = 'pending_review'
): PopulationInsightRecord => ({
  id: 'pop-1',
  insight_type: 'sdg_narrative',
  target: '3.4',
  period_start: '2026-01-01',
  period_end: null,
  narrative: 'SDG 3.4 narrative.',
  observed_findings: null,
  possible_interpretations: null,
  limitations: 'l',
  requires_human_review: true,
  provider: 'stub',
  model: '',
  prompt_version: '1.0-sdg-narrative-phase11',
  quality_status: 'valid',
  quality_reason: null,
  review_status: status,
  reviewer_id: null,
  reviewer_comment: null,
  edited_output: null,
  approved_at: null,
  created_at: '2026-08-12T00:00:00Z',
})

const reviewResponse = (): InsightReviewResponse => ({
  id: 'pop-1',
  insight_type: 'sdg_narrative',
  review_status: 'approved',
  reviewer_id: 'rev-1',
  reviewer_comment: 'ok',
  edited_output: null,
  approved_at: '2026-08-12T00:00:00Z',
})

// =====================================================================
// CHW SUGGESTIONS PAGE
// =====================================================================

describe('ChwSuggestionsPage', () => {
  it('renders the operational disclaimer', async () => {
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    renderPage(<ChwSuggestionsPage />)
    expect(
      screen.getByText(/administrative assistance only/i)
    ).toBeInTheDocument()
    expect(
      screen.getByText(/do not determine clinical priority/i)
    ).toBeInTheDocument()
  })

  it('generates and displays suggestions with operational reason codes', async () => {
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    apiMocks.generateOperationalSuggestions.mockResolvedValue(operationalBatch())
    renderPage(<ChwSuggestionsPage />)
    fireEvent.click(screen.getByTestId('generate-suggestions-btn'))
    await waitFor(() => {
      expect(screen.getByText(/follow-up is overdue/i)).toBeInTheDocument()
    })
    expect(screen.getByText('overdue')).toBeInTheDocument()
    expect(screen.getByText('aged referral')).toBeInTheDocument()
  })

  it('shows unavailable state when AI unavailable', async () => {
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    apiMocks.generateOperationalSuggestions.mockResolvedValue({
      ...operationalBatch(),
      available: false,
      quality_status: 'provider_unavailable',
      quality_reason: 'AI operational provider unavailable.',
      suggestions: [],
    })
    renderPage(<ChwSuggestionsPage />)
    fireEvent.click(screen.getByTestId('generate-suggestions-btn'))
    await waitFor(() => {
      expect(
        screen.getByText(/AI operational provider unavailable/i)
      ).toBeInTheDocument()
    })
  })

  it('shows error state on failure', async () => {
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    apiMocks.generateOperationalSuggestions.mockRejectedValue(new Error('403'))
    renderPage(<ChwSuggestionsPage />)
    fireEvent.click(screen.getByTestId('generate-suggestions-btn'))
    await waitFor(() => {
      expect(screen.getByText(/Could not generate suggestions/i)).toBeInTheDocument()
    })
  })

  it('renders suggestion history with review status', async () => {
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([operationalRecord()])
    renderPage(<ChwSuggestionsPage />)
    await waitFor(() => {
      expect(screen.getByText(/follow-up is overdue/i)).toBeInTheDocument()
      expect(screen.getByText('pending review')).toBeInTheDocument()
    })
  })

  it('shows no-data empty state for empty history', async () => {
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    renderPage(<ChwSuggestionsPage />)
    await waitFor(() => {
      expect(screen.getByText(/No suggestions generated yet/i)).toBeInTheDocument()
    })
  })
})

// =====================================================================
// EQUITY INTELLIGENCE PAGE
// =====================================================================

describe('EquityIntelligencePage', () => {
  it('renders the equity disclaimer + privacy badge', async () => {
    apiMocks.generateEquityInsight.mockResolvedValue(equityResponse())
    apiMocks.fetchEquityInsights.mockResolvedValue([])
    renderPage(<EquityIntelligencePage />)
    expect(
      screen.getByText(/do not infer disease prevalence/i)
    ).toBeInTheDocument()
    expect(screen.getByText(/k-anonymity ≥ 10/i)).toBeInTheDocument()
    expect(screen.getByText(/de-identified aggregate only/i)).toBeInTheDocument()
  })

  it('displays observed findings and possible interpretations', async () => {
    apiMocks.generateEquityInsight.mockResolvedValue(equityResponse())
    apiMocks.fetchEquityInsights.mockResolvedValue([])
    renderPage(<EquityIntelligencePage />)
    await waitFor(() => {
      expect(
        screen.getByText(/Tamil language completion/i)
      ).toBeInTheDocument()
      expect(
        screen.getByText(/accessibility gap/i)
      ).toBeInTheDocument()
    })
  })

  it('shows review status badge for the insight record', async () => {
    apiMocks.generateEquityInsight.mockResolvedValue(equityResponse())
    apiMocks.fetchEquityInsights.mockResolvedValue([])
    renderPage(<EquityIntelligencePage />)
    await waitFor(() => {
      expect(screen.getByText('pending review')).toBeInTheDocument()
    })
  })

  it('shows error state on failure', async () => {
    apiMocks.generateEquityInsight.mockRejectedValue(new Error('403'))
    apiMocks.fetchEquityInsights.mockResolvedValue([])
    renderPage(<EquityIntelligencePage />)
    await waitFor(() => {
      expect(
        screen.getByText(/Could not load equity insights/i)
      ).toBeInTheDocument()
    })
  })
})

// =====================================================================
// SDG NARRATIVES + REVIEW QUEUE PAGE
// =====================================================================

describe('SdgNarrativesPage', () => {
  it('renders the SDG narrative disclaimer', async () => {
    apiMocks.generateSdgNarratives.mockResolvedValue(sdgResponse())
    apiMocks.fetchSdgNarratives.mockResolvedValue([])
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    renderPage(<SdgNarrativesPage />)
    expect(
      screen.getByText(/do not prove an SDG target has been achieved/i)
    ).toBeInTheDocument()
    expect(screen.getByText(/not official UN SDG indicators/i)).toBeInTheDocument()
  })

  it('displays SDG narrative with observed trends', async () => {
    apiMocks.generateSdgNarratives.mockResolvedValue(sdgResponse())
    apiMocks.fetchSdgNarratives.mockResolvedValue([])
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    renderPage(<SdgNarrativesPage />)
    await waitFor(() => {
      expect(screen.getByText(/SDG 3.4 Narrative/i)).toBeInTheDocument()
      expect(screen.getByText(/sdg-3-4-screening: 0.7/i)).toBeInTheDocument()
    })
  })

  it('shows review queue with review actions for pending items', async () => {
    apiMocks.generateSdgNarratives.mockResolvedValue({
      ...sdgResponse(),
      narratives: [],
      available: false,
      quality_reason: 'No SDG metrics available for the period.',
    })
    apiMocks.fetchSdgNarratives.mockResolvedValue([populationRecord('pending_review')])
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    apiMocks.reviewPopulationInsight.mockResolvedValue(reviewResponse())
    renderPage(<SdgNarrativesPage />)
    await waitFor(() => {
      // pending_review items can be reviewed (submit) but NOT published.
      expect(screen.getByTestId('submit-review-btn')).toBeInTheDocument()
      expect(screen.queryByTestId('publish-btn')).not.toBeInTheDocument()
    })
  })

  it('shows publish button for approved items only', async () => {
    apiMocks.generateSdgNarratives.mockResolvedValue({
      ...sdgResponse(),
      narratives: [],
      available: false,
      quality_reason: 'none',
    })
    apiMocks.fetchSdgNarratives.mockResolvedValue([populationRecord('approved')])
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    renderPage(<SdgNarrativesPage />)
    await waitFor(() => {
      expect(screen.getByTestId('publish-btn')).toBeInTheDocument()
    })
    // No submit-review button for approved items.
    expect(screen.queryByTestId('submit-review-btn')).not.toBeInTheDocument()
  })

  it('shows no review actions for published items', async () => {
    apiMocks.generateSdgNarratives.mockResolvedValue({
      ...sdgResponse(),
      narratives: [],
      available: false,
      quality_reason: 'none',
    })
    apiMocks.fetchSdgNarratives.mockResolvedValue([populationRecord('published')])
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    renderPage(<SdgNarrativesPage />)
    await waitFor(() => {
      expect(screen.getByText('published')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('publish-btn')).not.toBeInTheDocument()
    expect(screen.queryByTestId('submit-review-btn')).not.toBeInTheDocument()
  })

  it('submits a review (approve)', async () => {
    apiMocks.generateSdgNarratives.mockResolvedValue({
      ...sdgResponse(),
      narratives: [],
      available: false,
      quality_reason: 'none',
    })
    apiMocks.fetchSdgNarratives.mockResolvedValue([populationRecord('pending_review')])
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    apiMocks.reviewPopulationInsight.mockResolvedValue(reviewResponse())
    renderPage(<SdgNarrativesPage />)
    await waitFor(() => {
      expect(screen.getByTestId('submit-review-btn')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByTestId('submit-review-btn'))
    await waitFor(() => {
      expect(apiMocks.reviewPopulationInsight).toHaveBeenCalledWith(
        'pop-1',
        expect.objectContaining({ action: 'approve' })
      )
    })
  })

  it('requires edited output for edit action', async () => {
    apiMocks.generateSdgNarratives.mockResolvedValue({
      ...sdgResponse(),
      narratives: [],
      available: false,
      quality_reason: 'none',
    })
    apiMocks.fetchSdgNarratives.mockResolvedValue([populationRecord('pending_review')])
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    renderPage(<SdgNarrativesPage />)
    await waitFor(() => {
      expect(screen.getByTestId('submit-review-btn')).toBeInTheDocument()
    })
    // Select edit -> submit disabled until text entered.
    fireEvent.click(screen.getByText('edit'))
    expect(screen.getByTestId('edit-output')).toBeInTheDocument()
    expect(screen.getByTestId('submit-review-btn')).toBeDisabled()
  })

  it('shows no-data empty state for empty review queue', async () => {
    apiMocks.generateSdgNarratives.mockResolvedValue({
      ...sdgResponse(),
      narratives: [],
      available: false,
      quality_reason: 'none',
    })
    apiMocks.fetchSdgNarratives.mockResolvedValue([])
    apiMocks.fetchOperationalSuggestions.mockResolvedValue([])
    renderPage(<SdgNarrativesPage />)
    await waitFor(() => {
      expect(
        screen.getByText(/No population insights pending review/i)
      ).toBeInTheDocument()
    })
  })
})
