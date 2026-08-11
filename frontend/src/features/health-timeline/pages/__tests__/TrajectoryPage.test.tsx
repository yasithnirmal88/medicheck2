import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import React from 'react'
import TrajectoryPage from '../TrajectoryPage'
import type {
  HealthTrajectory,
  LongitudinalExplanation,
} from '../../api/trajectoryService'

// Mock the trajectory hooks so we can drive each state.
const useTrajectory = vi.hoisted(() => vi.fn())
const useTrajectoryExplanation = vi.hoisted(() => vi.fn())
vi.mock('../../hooks/useTrajectory', () => ({
  useTrajectory,
  useTrajectoryExplanation,
}))

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0 } },
  })
}

function renderPage(client: QueryClient = makeClient()) {
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <TrajectoryPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function point(
  id: string,
  date: string,
  score: number | null,
  category: string | null,
  inds: string[] = [],
  conds: string[] = [],
): HealthTrajectory['assessments'][number] {
  return {
    assessment_id: id,
    session_id: id,
    trace_id: 'trace-' + id,
    completed_at: date,
    overall_severity: category,
    body_systems: [{ body_system_id: 'bs1', name: 'Cardiovascular', score, category }],
    activated_indicators: inds,
    possible_conditions: conds,
    recommendations: [],
  }
}

function trajectory(p1: any, p2: any, bsPrev: any, bsCurr: any): HealthTrajectory {
  const trend = bsCurr.score > bsPrev.score ? 'worsening' : bsCurr.score < bsPrev.score ? 'improving' : 'stable'
  return {
    assessments: [p1, p2],
    sufficient_data: true,
    summary: '2 assessments compared over time.',
    comparisons: [
      {
        previous: p1,
        current: p2,
        overall_change: { scope: 'overall', ref_id: null, label: 'Overall severity', previous_value: bsPrev.category, current_value: bsCurr.category, previous_score: null, current_score: null, delta: null, trend },
        body_system_changes: [
          { scope: 'body_system', ref_id: 'bs1', label: 'Cardiovascular', previous_value: bsPrev.category, current_value: bsCurr.category, previous_score: bsPrev.score, current_score: bsCurr.score, delta: bsCurr.score - bsPrev.score, trend },
        ],
        indicator_changes: { new: [], resolved: [], persistent: [] },
        condition_changes: { new: [], removed: [], persistent: [] },
        recommendation_changes: { new: [], removed: [], persistent: [] },
        change_events: [],
      },
    ],
  }
}

const explanationUnavailable: LongitudinalExplanation = {
  available: false,
  summary: '',
  key_changes: [],
  persistent_findings: [],
  new_findings: [],
  improved_findings: [],
  stable_findings: [],
  important_context: [],
  evidence_ids: [],
  prompt_version: '',
  trace_ids: [],
  retrieved_evidence: [],
  evidence_available: false,
  disclaimer: 'AI explanation is currently unavailable.',
}

const explanationSuccess: LongitudinalExplanation = {
  available: true,
  summary: 'Your latest assessment showed higher-severity findings overall.',
  key_changes: [{ label: 'Overall', ref_id: null, ref_type: 'body_system', explanation: 'Overall severity increased.', evidence_ids: [] }],
  persistent_findings: [],
  new_findings: [{ label: 'Ind2', ref_id: 'ind2', ref_type: 'indicator', explanation: 'Newly activated finding.', evidence_ids: [] }],
  improved_findings: [],
  stable_findings: [],
  important_context: ['These are assessment findings, not confirmed diagnoses.'],
  evidence_ids: [],
  prompt_version: '1.0',
  trace_ids: ['trace-1', 'trace-2'],
  retrieved_evidence: [],
  evidence_available: false,
  disclaimer: 'AI-generated explanations summarize changes in your assessment history.',
}

beforeEach(() => {
  vi.clearAllMocks()
  useTrajectory.mockReturnValue({ data: undefined, isLoading: true })
  useTrajectoryExplanation.mockReturnValue({ data: undefined })
})

describe('TrajectoryPage', () => {
  it('1. shows loading state', () => {
    renderPage()
    expect(screen.getByText('Loading trajectory…')).toBeInTheDocument()
  })

  it('2. shows empty timeline (no assessments)', () => {
    useTrajectory.mockReturnValue({ data: { assessments: [], comparisons: [], sufficient_data: false, summary: 'Complete an assessment to begin your health timeline.' }, isLoading: false })
    renderPage()
    expect(screen.getByText('Complete an assessment to begin your health timeline.')).toBeInTheDocument()
  })

  it('3. shows single assessment insufficient-data message', () => {
    useTrajectory.mockReturnValue({ data: { assessments: [point('a', '2025-01-01', 1, 'Monitor')], comparisons: [], sufficient_data: false, summary: 'Your first assessment is recorded.' }, isLoading: false })
    renderPage()
    expect(screen.getByText('Your first assessment is recorded.')).toBeInTheDocument()
    expect(screen.queryByTestId('trajectory-timeline')).not.toBeInTheDocument()
  })

  it('4. shows multiple assessments timeline', async () => {
    const p1 = point('a', '2025-01-01', 1, 'Monitor')
    const p2 = point('b', '2025-02-01', 2, 'Needs Attention')
    useTrajectory.mockReturnValue({ data: trajectory(p1, p2, { score: 1, category: 'Monitor' }, { score: 2, category: 'Needs Attention' }), isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: explanationUnavailable })
    renderPage()
    expect(await screen.findByTestId('trajectory-timeline')).toBeInTheDocument()
  })

  it('5. shows increasing score trend', async () => {
    const p1 = point('a', '2025-01-01', 1, 'Monitor')
    const p2 = point('b', '2025-02-01', 2, 'Needs Attention')
    useTrajectory.mockReturnValue({ data: trajectory(p1, p2, { score: 1, category: 'Monitor' }, { score: 2, category: 'Needs Attention' }), isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: explanationUnavailable })
    renderPage()
    expect(await screen.findByText(/Increased/)).toBeInTheDocument()
  })

  it('6. shows decreasing score trend', async () => {
    const p1 = point('a', '2025-01-01', 2, 'Needs Attention')
    const p2 = point('b', '2025-02-01', 1, 'Monitor')
    useTrajectory.mockReturnValue({ data: trajectory(p1, p2, { score: 2, category: 'Needs Attention' }, { score: 1, category: 'Monitor' }), isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: explanationUnavailable })
    renderPage()
    expect(await screen.findByText(/Improved/)).toBeInTheDocument()
  })

  it('7. shows stable score trend', async () => {
    const p1 = point('a', '2025-01-01', 1, 'Monitor')
    const p2 = point('b', '2025-02-01', 1, 'Monitor')
    useTrajectory.mockReturnValue({ data: trajectory(p1, p2, { score: 1, category: 'Monitor' }, { score: 1, category: 'Monitor' }), isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: explanationUnavailable })
    renderPage()
    expect(await screen.findByText(/Stable/)).toBeInTheDocument()
  })

  it('8. shows new finding', async () => {
    const p1 = point('a', '2025-01-01', 1, 'Monitor', ['ind1'], [])
    const p2 = point('b', '2025-02-01', 2, 'Needs Attention', ['ind1', 'ind2'], [])
    const t = trajectory(p1, p2, { score: 1, category: 'Monitor' }, { score: 2, category: 'Needs Attention' })
    t.comparisons[0].indicator_changes = { new: ['ind2'], resolved: [], persistent: ['ind1'] }
    useTrajectory.mockReturnValue({ data: t, isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: explanationUnavailable })
    renderPage()
    const nf = await screen.findByTestId('new-findings')
    expect(nf.textContent).toContain('ind2')
  })

  it('9. shows persistent finding', async () => {
    const p1 = point('a', '2025-01-01', 1, 'Monitor', ['ind1'], [])
    const p2 = point('b', '2025-02-01', 2, 'Needs Attention', ['ind1'], [])
    const t = trajectory(p1, p2, { score: 1, category: 'Monitor' }, { score: 2, category: 'Needs Attention' })
    t.comparisons[0].indicator_changes = { new: [], resolved: [], persistent: ['ind1'] }
    useTrajectory.mockReturnValue({ data: t, isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: explanationUnavailable })
    renderPage()
    const pf = await screen.findByTestId('persistent-findings')
    expect(pf.textContent).toContain('ind1')
  })

  it('10. shows removed finding', async () => {
    const p1 = point('a', '2025-01-01', 2, 'Needs Attention', ['ind1', 'ind2'], [])
    const p2 = point('b', '2025-02-01', 1, 'Monitor', ['ind1'], [])
    const t = trajectory(p1, p2, { score: 2, category: 'Needs Attention' }, { score: 1, category: 'Monitor' })
    t.comparisons[0].indicator_changes = { new: [], resolved: ['ind2'], persistent: ['ind1'] }
    useTrajectory.mockReturnValue({ data: t, isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: explanationUnavailable })
    renderPage()
    const rf = await screen.findByTestId('resolved-findings')
    expect(rf.textContent).toContain('ind2')
  })

  it('11-12. AI unavailable then deterministic trajectory still renders', async () => {
    const p1 = point('a', '2025-01-01', 1, 'Monitor')
    const p2 = point('b', '2025-02-01', 2, 'Needs Attention')
    useTrajectory.mockReturnValue({ data: trajectory(p1, p2, { score: 1, category: 'Monitor' }, { score: 2, category: 'Needs Attention' }), isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: undefined })
    renderPage()
    expect(await screen.findByTestId('ai-unavailable')).toBeInTheDocument()
  })

  it('13. AI unavailable state shows fallback message', async () => {
    const p1 = point('a', '2025-01-01', 1, 'Monitor')
    const p2 = point('b', '2025-02-01', 2, 'Needs Attention')
    useTrajectory.mockReturnValue({ data: trajectory(p1, p2, { score: 1, category: 'Monitor' }, { score: 2, category: 'Needs Attention' }), isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: explanationUnavailable })
    renderPage()
    expect(await screen.findByTestId('ai-unavailable')).toBeInTheDocument()
    expect(screen.getByText(/AI explanation is currently unavailable/i)).toBeInTheDocument()
  })

  it('14. AI success shows summary + disclaimer', async () => {
    const p1 = point('a', '2025-01-01', 1, 'Monitor')
    const p2 = point('b', '2025-02-01', 2, 'Needs Attention')
    useTrajectory.mockReturnValue({ data: trajectory(p1, p2, { score: 1, category: 'Monitor' }, { score: 2, category: 'Needs Attention' }), isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: explanationSuccess })
    renderPage()
    expect(await screen.findByTestId('ai-explanation')).toBeInTheDocument()
    expect(screen.getByText(/Your latest assessment showed higher-severity findings overall/i)).toBeInTheDocument()
    expect(screen.getByTestId('ai-disclaimer')).toBeInTheDocument()
  })

  it('15. evidence display shown when available', async () => {
    const p1 = point('a', '2025-01-01', 1, 'Monitor')
    const p2 = point('b', '2025-02-01', 2, 'Needs Attention')
    useTrajectory.mockReturnValue({ data: trajectory(p1, p2, { score: 1, category: 'Monitor' }, { score: 2, category: 'Needs Attention' }), isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: { ...explanationSuccess, evidence_available: true, retrieved_evidence: [{ id: 'ev1', title: 'Guideline A', source: 'JAMA', url: null, evidence_level: 'A', summary: 'sum' }] } })
    renderPage()
    expect(await screen.findByTestId('ai-evidence')).toBeInTheDocument()
    expect(screen.getByText(/Guideline A/)).toBeInTheDocument()
  })

  it('16. disclaimer present even when AI unavailable', async () => {
    const p1 = point('a', '2025-01-01', 1, 'Monitor')
    const p2 = point('b', '2025-02-01', 2, 'Needs Attention')
    useTrajectory.mockReturnValue({ data: trajectory(p1, p2, { score: 1, category: 'Monitor' }, { score: 2, category: 'Needs Attention' }), isLoading: false })
    useTrajectoryExplanation.mockReturnValue({ data: explanationUnavailable })
    renderPage()
    expect(await screen.findByTestId('ai-disclaimer')).toBeInTheDocument()
  })

  it('17. no-session (empty) does not enable AI explanation fetch', () => {
    useTrajectory.mockReturnValue({ data: { assessments: [], comparisons: [], sufficient_data: false, summary: 'Complete an assessment to begin your health timeline.' }, isLoading: false })
    renderPage()
    // Explanation hook enabled flag = hasData (false) -> not fetched.
    expect(useTrajectoryExplanation).toHaveBeenCalledWith({}, false)
  })
})
