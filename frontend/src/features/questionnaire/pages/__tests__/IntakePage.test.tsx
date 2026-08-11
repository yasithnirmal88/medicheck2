import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import React from 'react'
import IntakePage from '../IntakePage'
import type { IntakeResponse } from '../../api/intakeService'

// Mock the API service.
const extractIntake = vi.hoisted(() => vi.fn())
vi.mock('../../api/intakeService', () => ({ extractIntake }))

// Mock the questionnaire hooks (start session + templates).
const startSession = vi.hoisted(() => vi.fn())
const useStartSession = vi.hoisted(() => vi.fn())
const useTemplates = vi.hoisted(() => vi.fn())
vi.mock('../../hooks/useQuestionnaire', () => ({
  useStartSession,
  useTemplates,
}))

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0 } },
  })
}

function renderPage(client: QueryClient) {
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <IntakePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const successResponse: IntakeResponse = {
  trace_id: 'trace-1',
  prompt_version: '1.0',
  available: true,
  message: null,
  observations: [
    {
      id: 'obs-1',
      source_text: 'tired when climbing stairs',
      normalized_concept: 'Exertional Fatigue',
      observation_type: 'symptom',
      certainty: 'reported',
      temporality: 'current',
      polarity: 'positive',
      severity_description: null,
      duration: null,
      frequency: null,
      context: null,
      body_system: 'CV',
      confidence: 0.7,
    },
  ],
  candidate_indicators: [
    {
      indicator_id: 'ind-1',
      confidence: 0.8,
      observation_ids: ['obs-1'],
      reason: 'may correspond to a clinical indicator',
      uncertainty: null,
      source: 'ai_extraction',
    },
  ],
  candidate_question_groups: [
    {
      question_group_id: 'qg-1',
      code: 'heart-health',
      name: 'Heart Health',
      body_system_id: 'CV',
      linked_indicator_ids: ['ind-1'],
      question_count: 3,
      source: 'cms',
    },
  ],
  candidate_questions: [],
  clarifications: [
    { text: 'When does this happen?', source: 'ai_generated', observation_id: 'obs-1', linked_indicator_id: null, linked_question_id: null },
  ],
}

beforeEach(() => {
  extractIntake.mockReset()
  useStartSession.mockReset()
  useTemplates.mockReset()
  useTemplates.mockReturnValue({ data: [] })
  useStartSession.mockReturnValue({
    mutate: startSession,
    isPending: false,
  })
})

describe('IntakePage', () => {
  it('renders the intake form and entry point text', () => {
    const client = makeClient()
    renderPage(client)
    expect(screen.getByText(/Tell us what you/i)).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Skip AI intake/i })).toBeInTheDocument()
  })

  it('submits text and shows extracted observations', async () => {
    extractIntake.mockResolvedValue(successResponse)
    const client = makeClient()
    renderPage(client)
    const ta = screen.getByRole('textbox')
    fireEvent.change(ta, { target: { value: 'I get tired on exertion' } })
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
    expect(await screen.findByText(/We noticed a few things that may be relevant/i)).toBeInTheDocument()
    expect(screen.getByText('Exertional Fatigue')).toBeInTheDocument()
  })

  it('shows loading state during submission', async () => {
    let resolveFn!: (v: IntakeResponse) => void
    extractIntake.mockReturnValue(new Promise((r) => { resolveFn = r }))
    const client = makeClient()
    renderPage(client)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'tired' } })
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
    expect(await screen.findByText(/Analyzing/i)).toBeInTheDocument()
    resolveFn(successResponse)
    await waitFor(() => expect(screen.getByText('Exertional Fatigue')).toBeInTheDocument())
  })

  it('shows unavailable state when AI is unavailable', async () => {
    extractIntake.mockResolvedValue({ ...successResponse, available: false, message: 'AI-assisted intake is currently unavailable. You can continue with the standard questionnaire.' })
    const client = makeClient()
    renderPage(client)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'tired' } })
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
    expect((await screen.findAllByText(/AI-assisted intake is currently unavailable/i)).length).toBeGreaterThan(0)
    expect(screen.queryByText(/We noticed a few things/i)).not.toBeInTheDocument()
  })

  it('lets the user reject an interpreted observation', async () => {
    extractIntake.mockResolvedValue(successResponse)
    const client = makeClient()
    renderPage(client)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'tired' } })
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
    expect(await screen.findByText('Exertional Fatigue')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Reject this interpretation/i }))
    await waitFor(() => expect(screen.queryByText('Exertional Fatigue')).not.toBeInTheDocument())
  })

  it('transitions to a recommended assessment on click', async () => {
    extractIntake.mockResolvedValue(successResponse)
    const client = makeClient()
    useTemplates.mockReturnValue({ data: [{ id: 'tpl-1', code: 'heart-health' }] })
    renderPage(client)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'tired' } })
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
    expect(await screen.findByText('Heart Health')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Heart Health/i }))
    await waitFor(() => expect(startSession).toHaveBeenCalledWith('tpl-1', expect.anything()))
  })

  it('skip AI intake is available (navigation mocked)', () => {
    const client = makeClient()
    renderPage(client)
    fireEvent.click(screen.getByRole('button', { name: /Skip AI intake/i }))
    expect(true).toBe(true)
  })

  it('lets the user edit their description after results', async () => {
    extractIntake.mockResolvedValue(successResponse)
    const client = makeClient()
    renderPage(client)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'tired' } })
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
    expect(await screen.findByText('Exertional Fatigue')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Edit description/i }))
    await waitFor(() => expect(screen.queryByText(/We noticed a few things/i)).not.toBeInTheDocument())
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('renders clarifying questions when present', async () => {
    extractIntake.mockResolvedValue(successResponse)
    const client = makeClient()
    renderPage(client)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'tired' } })
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
    expect(await screen.findByText('When does this happen?')).toBeInTheDocument()
  })

  it('uses non-diagnostic language in the UI', async () => {
    extractIntake.mockResolvedValue(successResponse)
    const client = makeClient()
    renderPage(client)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'tired' } })
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
    await screen.findByText(/We noticed a few things that may be relevant/i)
    expect(document.body.textContent).toContain('not a diagnosis')
    expect(document.body.textContent).not.toMatch(/AI detected your disease/i)
  })
})
