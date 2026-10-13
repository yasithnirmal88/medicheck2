import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
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

const successExplanation: AIExplanation = {
  summary: 'Your assessment flagged findings across the cardiovascular area.',
  key_findings: [
    {
      title: 'Chest Pain',
      explanation: 'A signal from your answers, not a confirmed condition.',
      source_indicator_ids: ['ind-1'],
    },
  ],
  severity_explanation: 'Moderate severity means findings warrant follow-up.',
  recommendation_explanations: [
    { recommendation_id: 'rec-1', explanation: 'Consider follow-up screening.' },
  ],
  evidence_notes: ['Guideline A (evidence level B)'],
  limitations: 'Not a diagnosis.',
  disclaimer:
    'This AI-generated explanation is based on your MediCheck assessment and does not constitute a diagnosis.',
  available: true,
  prompt_version: '1.0',
  trace_id: 'trace123',
}

beforeEach(() => {
  fetchReportExplanation.mockReset()
})

describe('ReportExplanation', () => {
  it('shows loading state then renders a successful explanation', async () => {
    fetchReportExplanation.mockResolvedValue(successExplanation)
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(await screen.findByText(/Preparing your explanation/i)).toBeInTheDocument()
    expect(await screen.findByText(/What this means/i)).toBeInTheDocument()
    expect(
      screen.getByText(/Your assessment flagged findings across the cardiovascular area/i)
    ).toBeInTheDocument()
    expect(screen.getByText(/Understanding the severity/i)).toBeInTheDocument()
    expect(screen.getByText(/Why these findings matter/i)).toBeInTheDocument()
    expect(screen.getByText(/Understanding your recommendations/i)).toBeInTheDocument()
  })

  it('clearly labels the section as AI-generated and includes the disclaimer', async () => {
    fetchReportExplanation.mockResolvedValue(successExplanation)
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(await screen.findByText('AI Explanation')).toBeInTheDocument()
    // The disclaimer text is interleaved with a styled <span>, so assert on
    // the whole document body rather than a single element's text.
    await waitFor(() => {
      expect(document.body.textContent).toContain(
        'does not constitute a diagnosis'
      )
    })
  })

  it('shows graceful fallback when the explanation is unavailable', async () => {
    fetchReportExplanation.mockResolvedValue({ ...successExplanation, available: false })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(
      await screen.findByText(/We couldn't generate the explanation right now/i)
    ).toBeInTheDocument()
    expect(screen.queryByText(/What this means/i)).not.toBeInTheDocument()
  })

  it('shows graceful fallback when the request errors', async () => {
    fetchReportExplanation.mockRejectedValue(new Error('network'))
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(
      await screen.findByText(/We couldn't generate the explanation right now/i)
    ).toBeInTheDocument()
  })

  it('renders an empty-but-available explanation without findings', async () => {
    fetchReportExplanation.mockResolvedValue({
      summary: 'No notable findings.',
      key_findings: [],
      severity_explanation: '',
      recommendation_explanations: [],
      evidence_notes: [],
      limitations: 'Not a diagnosis.',
      disclaimer: 'AI-generated, not a diagnosis.',
      available: true,
    })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(await screen.findByText(/No notable findings/i)).toBeInTheDocument()
    expect(screen.queryByText(/Why these findings matter/i)).not.toBeInTheDocument()
  })

  it('does not call the API when there is no sessionId', () => {
    const client = makeClient()
    render(<ReportExplanation sessionId={undefined} />, {
      wrapper: withProvider(client),
    })
    expect(screen.queryByText(/AI Explanation/i)).not.toBeInTheDocument()
    expect(fetchReportExplanation).not.toHaveBeenCalled()
  })

  it('renders accessible loading text', async () => {
    let resolveFn: (v: AIExplanation) => void = () => {}
    fetchReportExplanation.mockImplementation(
      () => new Promise<AIExplanation>((res) => (resolveFn = res))
    )
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(await screen.findByText(/Preparing your explanation/i)).toBeInTheDocument()
    resolveFn(successExplanation)
    await waitFor(() =>
      expect(screen.getByText(/What this means/i)).toBeInTheDocument()
    )
  })

  // ── Phase 2: evidence-grounded RAG ────────────────────────────────────

  it('renders the evidence section with retrieved evidence and citation markers', async () => {
    fetchReportExplanation.mockResolvedValue({
      ...successExplanation,
      prompt_version: '2.0',
      evidence_available: true,
      retrieved_evidence: [
        {
          id: 'ev-1',
          title: '2024 ACC/AHA Guideline',
          source: 'JACC',
          url: 'https://doi.org/10.1016/example',
          evidence_level: 'A',
          excerpt: 'Guideline excerpt.',
          relevance: 0.9,
        },
      ],
      key_findings: [
        {
          title: 'Chest Pain',
          explanation: 'A signal from your answers.',
          source_indicator_ids: ['ind-1'],
          evidence_ids: ['ev-1'],
        },
      ],
    })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    expect(await screen.findByText(/2024 ACC\/AHA Guideline/i)).toBeInTheDocument()
    // Evidence section is visually distinguished from AI prose.
    expect(screen.getByText(/Retrieved from the MediCheck approved clinical evidence repository/i)).toBeInTheDocument()
    expect(screen.getByText(/Evidence level: A/i)).toBeInTheDocument()
    expect(screen.getByText(/Source: JACC/i)).toBeInTheDocument()
    // Citation marker on the finding links to evidence [1] with a real URL.
    expect(screen.getByText(/Based on evidence associated with this finding/i)).toBeInTheDocument()
    const link = screen.getByRole('link', { name: /\[1\]/i })
    expect(link).toHaveAttribute('href', 'https://doi.org/10.1016/example')
  })

  it('states that no supporting evidence was available when evidence_available is false', async () => {
    fetchReportExplanation.mockResolvedValue({
      ...successExplanation,
      prompt_version: '2.0',
      evidence_available: false,
      retrieved_evidence: [],
      evidence_notes: [
        'No supporting evidence was available from the MediCheck evidence repository for this explanation.',
      ],
    })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    await waitFor(() =>
      expect(screen.getAllByText(/No supporting evidence was available from the MediCheck evidence/i).length).toBeGreaterThan(0)
    )
    // No fake citation links rendered.
    expect(screen.queryByRole('link', { name: /\[1\]/i })).not.toBeInTheDocument()
  })

  it('does not render a citation marker when the AI references an evidence id that was not retrieved', async () => {
    fetchReportExplanation.mockResolvedValue({
      ...successExplanation,
      prompt_version: '2.0',
      evidence_available: true,
      retrieved_evidence: [
        { id: 'ev-1', title: 'Real Evidence', evidence_level: 'B' },
      ],
      // Finding references a fabricated evidence id not in retrieved_evidence.
      key_findings: [
        {
          title: 'Chest Pain',
          explanation: 'A signal.',
          source_indicator_ids: ['ind-1'],
          evidence_ids: ['EV-999-INVENTED'],
        },
      ],
    })
    const client = makeClient()
    render(<ReportExplanation sessionId="sess-1" />, {
      wrapper: withProvider(client),
    })
    await waitFor(() => expect(screen.getByText(/Real Evidence/i)).toBeInTheDocument())
    // The fabricated id resolves to nothing → no citation marker rendered.
    expect(screen.queryByText(/Based on evidence associated with this finding/i)).not.toBeInTheDocument()
  })
})
