import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import ReportExplanation from '../ReportExplanation'
import type { AIExplanation } from '../../api/patientService'

// Mock the data layer so the AI explanation service is never actually called.
const fetchReportExplanation = vi.hoisted(() => vi.fn())

vi.mock('../../api/patientService', () => ({
  fetchReportExplanation,
}))

function makeClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0, refetchOnWindowFocus: false },
    },
  })
}

function withProvider(client: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    )
  }
}

const baseExplanation: AIExplanation = {
  summary: 'Your assessment flagged findings.',
  key_findings: [],
  severity_explanation: '',
  recommendation_explanations: [],
  evidence_notes: [],
  limitations: 'Not a diagnosis.',
  disclaimer: 'AI-generated, not a diagnosis.',
  available: true,
}

beforeEach(() => {
  fetchReportExplanation.mockReset()
})

describe('ReportExplanation — Phase 7', () => {
  it('renders language and literacy level selectors', async () => {
    fetchReportExplanation.mockResolvedValue(baseExplanation)
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(
      await screen.findByLabelText(/Explanation language/i)
    ).toBeInTheDocument()
    expect(
      await screen.findByLabelText(/Detail level/i)
    ).toBeInTheDocument()
  })

  it('passes language and literacy_level to the fetch call', async () => {
    fetchReportExplanation.mockResolvedValue(baseExplanation)
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    await waitFor(() => expect(fetchReportExplanation).toHaveBeenCalled())
    expect(fetchReportExplanation).toHaveBeenCalledWith(
      'sess-1',
      expect.objectContaining({
        language: 'en',
        literacy_level: 'standard',
      })
    )
  })

  it('refetches when language changes to Sinhala', async () => {
    fetchReportExplanation.mockResolvedValue(baseExplanation)
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    await waitFor(() => expect(fetchReportExplanation).toHaveBeenCalledTimes(1))

    const select = await screen.findByLabelText(/Explanation language/i)
    fireEvent.change(select, { target: { value: 'si' } })

    await waitFor(() => expect(fetchReportExplanation).toHaveBeenCalledTimes(2))
    expect(fetchReportExplanation).toHaveBeenLastCalledWith(
      'sess-1',
      expect.objectContaining({ language: 'si' })
    )
  })

  it('refetches when literacy level changes to detailed', async () => {
    fetchReportExplanation.mockResolvedValue(baseExplanation)
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    await waitFor(() => expect(fetchReportExplanation).toHaveBeenCalledTimes(1))

    const select = await screen.findByLabelText(/Detail level/i)
    fireEvent.change(select, { target: { value: 'detailed' } })

    await waitFor(() => expect(fetchReportExplanation).toHaveBeenCalledTimes(2))
    expect(fetchReportExplanation).toHaveBeenLastCalledWith(
      'sess-1',
      expect.objectContaining({ literacy_level: 'detailed' })
    )
  })

  it('renders the AI transparency notice', async () => {
    fetchReportExplanation.mockResolvedValue({
      ...baseExplanation,
      transparency_notice:
        'Your clinical assessment was calculated by the deterministic engine. AI did not diagnose.',
    })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(
      await screen.findByText(/calculated by the deterministic engine/i)
    ).toBeInTheDocument()
  })

  it('renders the source breakdown section when present', async () => {
    fetchReportExplanation.mockResolvedValue({
      ...baseExplanation,
      source_breakdown: [
        {
          clinical_finding: 'High blood pressure indicator',
          contributing_answer_refs: [],
          knowledge_graph_relationship: 'Indicator → Possible Condition',
          evidence_ids: [],
          deterministic_score: 0.85,
          trace_id: 'trace-abc-123',
        },
      ],
    })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(await screen.findByText(/Show the source/i)).toBeInTheDocument()
    expect(
      screen.getByText(/High blood pressure indicator/i)
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Indicator → Possible Condition/i)
    ).toBeInTheDocument()
    // trace_id is truncated to 8 chars
    expect(screen.getByText(/trace-ab/i)).toBeInTheDocument()
  })

  it('renders the AI quality status badge for valid', async () => {
    fetchReportExplanation.mockResolvedValue({
      ...baseExplanation,
      quality_status: 'valid',
    })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(
      await screen.findByText(/AI explanation verified/i)
    ).toBeInTheDocument()
  })

  it('renders the AI quality status badge for provider_unavailable', async () => {
    fetchReportExplanation.mockResolvedValue({
      ...baseExplanation,
      quality_status: 'provider_unavailable',
    })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(
      await screen.findByText(/AI provider unavailable/i)
    ).toBeInTheDocument()
  })

  it('renders the AI quality status badge for validation_failed', async () => {
    fetchReportExplanation.mockResolvedValue({
      ...baseExplanation,
      quality_status: 'validation_failed',
    })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(
      await screen.findByText(/AI output validation failed/i)
    ).toBeInTheDocument()
  })

  it('renders the AI quality status badge for evidence_unavailable', async () => {
    fetchReportExplanation.mockResolvedValue({
      ...baseExplanation,
      quality_status: 'evidence_unavailable',
    })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(
      await screen.findByText(/No supporting evidence available/i)
    ).toBeInTheDocument()
  })

  it('links source breakdown evidence to retrieved evidence records', async () => {
    fetchReportExplanation.mockResolvedValue({
      ...baseExplanation,
      retrieved_evidence: [
        {
          id: 'ev-1',
          title: 'WHO Guideline',
          url: 'https://who.int/example',
          evidence_level: 'A',
        },
      ],
      source_breakdown: [
        {
          clinical_finding: 'Hypertension indicator',
          contributing_answer_refs: [],
          knowledge_graph_relationship: 'Indicator → Condition',
          evidence_ids: ['ev-1'],
          deterministic_score: 0.7,
          trace_id: null,
        },
      ],
    })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    await waitFor(() => expect(screen.getByText(/Show the source/i)).toBeInTheDocument())
    const link = screen.getByRole('link', { name: /\[1\]/i })
    expect(link).toHaveAttribute('href', 'https://who.int/example')
  })
})
