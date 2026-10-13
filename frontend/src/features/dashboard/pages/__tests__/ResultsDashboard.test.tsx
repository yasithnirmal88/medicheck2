import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import React from 'react'
import ResultsDashboard from '../ResultsDashboard'
import type { ReportDetail } from '../../types/report'

const fetchReportBySession = vi.hoisted(() => vi.fn())
const generateReport = vi.hoisted(() => vi.fn())

vi.mock('@/features/dashboard/api/patientService', () => ({
  fetchReportBySession,
  generateReport,
}))

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0 } },
  })
}

function renderPage(client: QueryClient = makeClient()) {
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/assessments/sess-1/results']}>
        <Routes>
          <Route path="/assessments/:id/results" element={<ResultsDashboard />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function httpError(status: number) {
  return Object.assign(new Error(`HTTP ${status}`), {
    response: { status },
  })
}

const REAL_REPORT: ReportDetail = {
  id: 'report-1',
  session_id: 'sess-1',
  body_systems: [
    {
      id: 'bsa-1',
      body_system_id: 'bs_cardiovascular',
      category: 'Monitor',
      score: '2.0',
    },
  ],
  conditions: [
    {
      id: 'ca-1',
      condition_id: 'cond_hypertension_risk',
      score: '3.0',
      confidence: 'Moderate',
    },
  ],
  advices: [
    { id: 'adv-1', category: 'Activity', text: 'Increase daily movement.' },
  ],
}

beforeEach(() => {
  fetchReportBySession.mockReset()
  generateReport.mockReset()
  window.history.pushState({}, '', '/')
})

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('ResultsDashboard — real data only', () => {
  it('renders values exclusively from the API report', async () => {
    fetchReportBySession.mockResolvedValue(REAL_REPORT)

    renderPage()

    expect(await screen.findByText('Cardiovascular')).toBeInTheDocument()
    expect(screen.getAllByText('Monitor').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Score 2')).toBeInTheDocument()
    expect(screen.getByText('Hypertension Risk')).toBeInTheDocument()
    expect(screen.getByText('Moderate')).toBeInTheDocument()
    expect(screen.getByText('Increase daily movement.')).toBeInTheDocument()
  })

  it('never shows the old fabricated clinical values', async () => {
    fetchReportBySession.mockResolvedValue(REAL_REPORT)

    renderPage()
    await screen.findByText('Cardiovascular')

    expect(screen.queryByText('128/82 mmHg')).not.toBeInTheDocument()
    expect(screen.queryByText(/mg\/dL/)).not.toBeInTheDocument()
    expect(screen.queryByText(/LDL/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Blood Pressure/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Health Score/)).not.toBeInTheDocument()
    expect(screen.queryByText(/\/100/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Suggested Laboratory Tests/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Risk Indicators/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Next recommended assessment/)).not.toBeInTheDocument()
  })

  it('shows an error state when the fetch fails (and no fabricated data)', async () => {
    fetchReportBySession.mockRejectedValue(httpError(500))
    generateReport.mockRejectedValue(httpError(500))

    renderPage()

    expect(
      await screen.findByText(/couldn't load this report/i),
    ).toBeInTheDocument()
    expect(screen.queryByText('128/82 mmHg')).not.toBeInTheDocument()
    expect(screen.queryByText('Monitor')).not.toBeInTheDocument()
  })

  it('shows a "no report yet" empty state when the report is absent', async () => {
    fetchReportBySession.mockRejectedValue(httpError(404))
    generateReport.mockRejectedValue(httpError(400))

    renderPage()

    expect(await screen.findByText('No report available yet')).toBeInTheDocument()
    expect(screen.queryByText('128/82 mmHg')).not.toBeInTheDocument()
  })
})

describe('ResultsDashboard — gated demo mode', () => {
  it('does not show demo data by default', async () => {
    fetchReportBySession.mockResolvedValue(REAL_REPORT)

    renderPage()
    await screen.findByText('Cardiovascular')

    expect(
      screen.queryByText(/Demo data/i),
    ).not.toBeInTheDocument()
  })

  it('shows clearly-labelled demo data only when ?demo=1 is set', async () => {
    window.history.pushState({}, '', '/?demo=1')
    fetchReportBySession.mockRejectedValue(httpError(404))
    generateReport.mockRejectedValue(httpError(400))

    renderPage()

    expect(
      await screen.findByText(/Demo data – not real clinical results/i),
    ).toBeInTheDocument()
    expect(screen.getByText('Cardiovascular')).toBeInTheDocument()
  })

  it('prefers the real report over demo data when a real report exists', async () => {
    window.history.pushState({}, '', '/?demo=1')
    fetchReportBySession.mockResolvedValue(REAL_REPORT)

    renderPage()

    // Wait for an element that exists only in the real report, not the demo.
    expect(await screen.findByText('Increase daily movement.')).toBeInTheDocument()
    expect(screen.queryByText(/Demo data/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/demonstration only/i)).not.toBeInTheDocument()
  })
})
