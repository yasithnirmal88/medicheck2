import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { AnalyticsDashboardPage } from '../../pages/AnalyticsDashboardPage'

// Mock the analytics API layer so no real HTTP calls are made.
const apiMocks = vi.hoisted(() => ({
  getOverview: vi.fn(),
  getSeverity: vi.fn(),
  getBodySystems: vi.fn(),
  getIndicators: vi.fn(),
  getTrajectory: vi.fn(),
  getAccessibility: vi.fn(),
  getSDGDashboard: vi.fn(),
}))

vi.mock('../../api/analyticsApi', () => ({
  analyticsApi: apiMocks,
}))

function renderPage() {
  return render(
    <QueryClientProvider client={new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: 0 } },
    })}>
      <AnalyticsDashboardPage />
    </QueryClientProvider>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  apiMocks.getOverview.mockResolvedValue({
    overview: {
      period_start: '2026-01-01',
      period_end: '2026-03-31',
      total_assessments: 150,
      completed_assessments: 120,
      in_progress_assessments: 30,
      unique_participants: 100,
      completion_rate: 80.0,
      completion_rate_suppressed: false,
    },
    trend: [],
    generated_at: '2026-03-31',
  })
  apiMocks.getSeverity.mockResolvedValue({
    period_start: '2026-01-01',
    period_end: '2026-03-31',
    distribution: [
      { category: 'Normal', count: 50, percentage: 41.7, suppressed: false },
      { category: 'Monitor', count: 40, percentage: 33.3, suppressed: false },
      { category: 'Needs Attention', count: 20, percentage: 16.7, suppressed: false },
      { category: 'Recommend Screening', count: 7, percentage: null, suppressed: true },
      { category: 'Urgent Medical Review', count: 3, percentage: null, suppressed: true },
    ],
    total_assessments: 120,
    disclaimer: 'Distribution of MediCheck assessment findings, not population prevalence.',
  })
  apiMocks.getBodySystems.mockResolvedValue({
    period_start: '2026-01-01',
    period_end: '2026-03-31',
    body_systems: [],
  })
  apiMocks.getIndicators.mockResolvedValue({
    period_start: '2026-01-01',
    period_end: '2026-03-31',
    indicators: [],
    disclaimer: 'Indicator activation is not confirmed diagnosis.',
  })
  apiMocks.getTrajectory.mockResolvedValue({
    period_start: '2026-01-01',
    period_end: '2026-03-31',
    distribution: [
      { trend: 'improving', count: 15, percentage: 30.0, suppressed: false },
      { trend: 'stable', count: 25, percentage: 50.0, suppressed: false },
      { trend: 'worsening', count: 10, percentage: 20.0, suppressed: false },
      { trend: 'new', count: 0, percentage: null, suppressed: true },
      { trend: 'resolved', count: 0, percentage: null, suppressed: true },
    ],
    patients_with_trajectory: 50,
    disclaimer: 'A worsening trajectory is an assessment trend, not proof of disease progression.',
  })
  apiMocks.getAccessibility.mockResolvedValue({
    period_start: '2026-01-01',
    period_end: '2026-03-31',
    accessibility: {
      by_language: [
        { language: 'en', assessment_count: 80, completion_rate: 82.5, suppressed: false },
        { language: 'si', assessment_count: 40, completion_rate: 75.0, suppressed: false },
        { language: 'ta', assessment_count: 5, completion_rate: null, suppressed: true },
      ],
      voice_intake_count: 30,
      text_intake_count: 90,
      voice_completion_rate: 70.0,
      voice_suppressed: false,
    },
    disclaimer: 'Do not infer demographics from language.',
  })
  apiMocks.getSDGDashboard.mockResolvedValue({
    period_start: '2026-01-01',
    period_end: '2026-03-31',
    sections: [
      {
        goal: 'SDG 3.4',
        title: 'NCD Prevention & Risk Reduction',
        metrics: [
          { label: 'NCD-related assessment activity', value: 120, suppressed: false, definition: 'Completed assessments.' },
        ],
        note: '',
      },
      {
        goal: 'SDG 3.8',
        title: 'Universal Health Coverage & Access',
        metrics: [
          { label: 'Completion rate', value: 80.0, suppressed: false, definition: 'Completed / started.' },
        ],
        note: '',
      },
    ],
    disclaimer: 'Platform-derived monitoring indicators. Do not prove SDG achievement.',
  })
})

describe('AnalyticsDashboardPage', () => {
  it('renders the page title and overview metrics', async () => {
    renderPage()
    expect(screen.getByText('Population Health & SDG Analytics')).toBeInTheDocument()
    await waitFor(() => {
      // "150" (total) and "100" (participants) are unique; "120" appears
      // in multiple places so use getAllByText.
      expect(screen.getByText('150')).toBeInTheDocument()
      expect(screen.getAllByText('120').length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('100')).toBeInTheDocument()
    })
  })

  it('renders the severity distribution with disclaimer', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Assessment Findings Distribution')).toBeInTheDocument()
      expect(screen.getByText(/not population prevalence/i)).toBeInTheDocument()
      expect(screen.getByText('Normal')).toBeInTheDocument()
      expect(screen.getByText('Monitor')).toBeInTheDocument()
    })
  })

  it('renders suppressed badge for small cohorts', async () => {
    renderPage()
    await waitFor(() => {
      // The "Recommend Screening" and "Urgent Medical Review" buckets are suppressed.
      const badges = screen.getAllByText('Suppressed')
      expect(badges.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('renders the trajectory distribution with disclaimer', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Health Trajectory Distribution')).toBeInTheDocument()
      expect(screen.getByText(/not proof of disease progression/i)).toBeInTheDocument()
      expect(screen.getByText('Improving')).toBeInTheDocument()
      expect(screen.getByText('Stable')).toBeInTheDocument()
      expect(screen.getByText('Worsening')).toBeInTheDocument()
    })
  })

  it('renders the accessibility metrics with disclaimer', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Accessibility Metrics')).toBeInTheDocument()
      expect(screen.getByText(/Do not infer demographics/i)).toBeInTheDocument()
      expect(screen.getByText('Voice intake sessions')).toBeInTheDocument()
    })
  })

  it('renders the SDG dashboard sections', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('SDG-Aligned Digital Health Indicators')).toBeInTheDocument()
      expect(screen.getByText(/Do not prove SDG achievement/i)).toBeInTheDocument()
      // Goal labels are rendered as "SDG 3.4 — NCD Prevention..." (split by
      // the em-dash), so match the goal code and the title separately.
      expect(screen.getByText(/SDG 3\.4/)).toBeInTheDocument()
      expect(screen.getByText(/SDG 3\.8/)).toBeInTheDocument()
      expect(screen.getByText(/NCD Prevention/)).toBeInTheDocument()
    })
  })

  it('has a language filter dropdown', async () => {
    renderPage()
    expect(screen.getByLabelText('Language:')).toBeInTheDocument()
    expect(screen.getByText('All')).toBeInTheDocument()
    expect(screen.getByText('English')).toBeInTheDocument()
    expect(screen.getByText('Sinhala')).toBeInTheDocument()
    expect(screen.getByText('Tamil')).toBeInTheDocument()
  })
})
