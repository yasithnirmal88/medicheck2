import { useCallback, useEffect, useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  useSaveAnswer,
  usePauseSession,
  useResumeSession,
  useCompleteSession,
  useSession,
} from './useQuestionnaire'
import type { AnswerResponse, Question } from '../types'

const DRAFT_STORAGE_KEY = (sessionId: string) => `medicheck:questionnaire:draft:${sessionId}`

const bodySystemLookup: Record<string, string> = {
  cardiovascular: 'Cardiovascular',
  neurological: 'Neurological',
  respiratory: 'Respiratory',
  endocrine: 'Endocrine',
  renal: 'Renal',
  gastrointestinal: 'Digestive',
  musculoskeletal: 'Musculoskeletal',
  dermatological: 'Dermatological',
  ophthalmological: 'Ophthalmological',
  otorhinolaryngological: 'ENT',
  psychiatric: 'Neurological',
  general: 'General',
}

type AnswerEntry = {
  value: unknown
  skipped?: boolean
}

export function useQuestionnaireFlow(sessionId: string | undefined) {
  const qc = useQueryClient()
  const { data: session, isLoading, error } = useSession(sessionId)
  const saveMutation = useSaveAnswer()
  const pauseMutation = usePauseSession()
  const resumeMutation = useResumeSession()
  const completeMutation = useCompleteSession()

  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null)
  const [answers, setAnswers] = useState<Record<string, AnswerEntry>>({})
  const [history, setHistory] = useState<Question[]>([])
  const [hasSubmitted, setHasSubmitted] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [visitedBodySystems, setVisitedBodySystems] = useState<string[]>([])

  const progress = session?.progress

  const resolveBodySystemName = (q: Question | null): string | null => {
    if (!q) return null
    if (q.body_system_id) return bodySystemLookup[q.body_system_id.toLowerCase()] ?? q.body_system_id
    return null
  }

  const trackSystem = useCallback((q: Question | null) => {
    const name = resolveBodySystemName(q)
    if (!name) return
    setVisitedBodySystems((prev) => (prev.includes(name) ? prev : [...prev, name]))
  }, [])

  // Seed the first question from the session on load.
  useEffect(() => {
    if (session?.current_question && !hasSubmitted) {
      setCurrentQuestion(session.current_question)
      setHasSubmitted(true)
      trackSystem(session.current_question)
    }
  }, [session?.current_question, hasSubmitted])

  // Auto-save draft to localStorage on every answer change (no advance).
  useEffect(() => {
    if (!sessionId) return
    if (Object.keys(answers).length === 0) return
    try {
      localStorage.setItem(DRAFT_STORAGE_KEY(sessionId), JSON.stringify(answers))
    } catch {
      // ignore storage errors
    }
  }, [answers, sessionId])

  const isFirst = history.length === 0
  const isLast = currentQuestion == null

  const canGoNext =
    currentQuestion != null && currentQuestion.is_required
      ? answers[currentQuestion.id]?.value !== undefined &&
        answers[currentQuestion.id]?.value !== null &&
        answers[currentQuestion.id]?.value !== ''
      : currentQuestion != null

  const submitAnswer = useCallback(
    async (value: unknown): Promise<AnswerResponse | null> => {
      if (!currentQuestion || !sessionId) {
        setSaveStatus('error')
        return null
      }

      // Optimistically record the answer (and skip status) locally first.
      const entry: AnswerEntry = { value }
      setAnswers((prev) => ({ ...prev, [currentQuestion.id]: entry }))
      setSaveStatus('saving')

      try {
        const response = await saveMutation.mutateAsync({
          sessionId,
          data: {
            question_id: currentQuestion.id,
            response_value: { value },
            time_taken_seconds: 0,
          },
        })
        setSaveStatus('saved')

        // Branching: push current onto history, advance to server's next question.
        setHistory((prev) => [...prev.slice(-19), currentQuestion])
        const nextQuestion = response.is_complete || !response.next_question ? null : response.next_question
        setCurrentQuestion(nextQuestion)
        trackSystem(nextQuestion)

        // Refresh session/progress from the server.
        qc.invalidateQueries({ queryKey: ['session', sessionId] })
        qc.invalidateQueries({ queryKey: ['progress', sessionId] })
        return response
      } catch {
        setSaveStatus('error')
        return null
      }
    },
    [currentQuestion, sessionId, saveMutation, qc],
  )

  const next = useCallback(() => {
    if (!currentQuestion) return
    submitAnswer(answers[currentQuestion.id]?.value ?? null)
  }, [submitAnswer, answers, currentQuestion])

  // Skip: record a skipped marker and advance via the same branching path.
  const skip = useCallback(
    async (value: unknown = '') => {
      if (!currentQuestion) return null
      setAnswers((prev) => ({ ...prev, [currentQuestion.id]: { value, skipped: true } }))
      return submitAnswer(value)
    },
    [currentQuestion, submitAnswer],
  )

  const goBack = useCallback(() => {
    setHistory((prev) => {
      if (prev.length === 0) return prev
      const nextHistory = prev.slice(0, -1)
      const previous = nextHistory[nextHistory.length - 1]
      if (previous) setCurrentQuestion(previous)
      return nextHistory
    })
  }, [])

  const pause = useCallback(() => {
    if (sessionId) pauseMutation.mutate(sessionId)
  }, [sessionId, pauseMutation])

  const resume = useCallback(() => {
    if (sessionId) resumeMutation.mutate(sessionId)
  }, [sessionId, resumeMutation])

  const recoverDraft = useCallback(() => {
    if (!sessionId) return
    try {
      const raw = localStorage.getItem(DRAFT_STORAGE_KEY(sessionId))
      if (raw) setAnswers(JSON.parse(raw))
    } catch {
      // ignore
    }
  }, [sessionId])

  const clearDraft = useCallback(() => {
    if (!sessionId) return
    localStorage.removeItem(DRAFT_STORAGE_KEY(sessionId))
  }, [sessionId])

  const isSubmitting = saveMutation.isPending

  const answeredCount = useMemo(
    () => Object.keys(answers).filter((k) => answers[k]?.value !== undefined && answers[k]?.value !== null && answers[k]?.value !== '').length,
    [answers],
  )

  const skippedCount = useMemo(
    () => Object.keys(answers).filter((k) => answers[k]?.skipped).length,
    [answers],
  )

  return {
    // state
    session,
    currentQuestion,
    answers,
    history,
    progress,
    totalQuestions: progress?.total_questions ?? 0,
    answered: answeredCount,
    skipped: skippedCount,
    bodySystemsCovered: visitedBodySystems,
    estimatedTimeRemaining: progress?.estimated_time_remaining ?? null,
    isFirst,
    isLast,
    canGoNext,
    isSubmitting,
    isLoading,
    error,
    // server state helpers
    saveStatus,
    isSaving: saveMutation.isPending,
    completed: (progress?.completion_percentage ?? 0) >= 100,
    // session lifecycle
    pause,
    resume,
    pauseMutation,
    resumeMutation,
    // navigation (adaptive branching lives in submitAnswer)
    submitAnswer,
    next,
    skip,
    goBack,
    // drafting
    recoverDraft,
    clearDraft,
    // mutation handles for UI loading
    completeMutation,
  }
}

export default useQuestionnaireFlow
