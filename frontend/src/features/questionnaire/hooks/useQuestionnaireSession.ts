import { useState, useCallback, useRef, useEffect } from 'react'
import { useSaveAnswer, useSession, useProgress } from './useQuestionnaire'
import type { Question } from '../types'

interface AnswerMap {
  [questionId: string]: Record<string, unknown>
}

export function useQuestionnaireSession(sessionId: string | undefined) {
  const { data: session, isLoading, error } = useSession(sessionId)
  const { data: progress } = useProgress(sessionId)
  const saveAnswerMutation = useSaveAnswer()

  const [answers, setAnswers] = useState<AnswerMap>({})
  const [currentIndex, setCurrentIndex] = useState(0)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const questionStartRef = useRef<number>(Date.now())

  const questions: Question[] = session?.current_question ? [session.current_question] : []
  const totalQuestions = progress?.total_questions ?? questions.length
  const currentQuestion = questions[currentIndex] ?? null
  const isFirst = currentIndex === 0
  const isLast = currentIndex >= questions.length - 1

  useEffect(() => {
    if (session?.status === 'in_progress') {
      timerRef.current = setInterval(() => {
        setElapsedTime((prev) => prev + 1)
      }, 1000)
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [session?.status])

  const triggerAutoSave = useCallback(
    (questionId: string, value: Record<string, unknown>) => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      setSaveStatus('saving')
      debounceRef.current = setTimeout(() => {
        if (!sessionId) return
        const timeTaken = Math.floor((Date.now() - questionStartRef.current) / 1000)
        saveAnswerMutation.mutate(
          { sessionId, data: { question_id: questionId, response_value: value, time_taken_seconds: timeTaken } },
          {
            onSuccess: () => setSaveStatus('saved'),
            onError: () => setSaveStatus('error'),
          }
        )
        questionStartRef.current = Date.now()
      }, 3000)
    },
    [sessionId, saveAnswerMutation]
  )

  const saveAnswer = useCallback(
    (questionId: string, value: Record<string, unknown>) => {
      setAnswers((prev) => ({ ...prev, [questionId]: value }))
      triggerAutoSave(questionId, value)
    },
    [triggerAutoSave]
  )

  const goNext = useCallback(() => {
    if (!isLast) {
      setCurrentIndex((i) => i + 1)
      questionStartRef.current = Date.now()
    }
  }, [isLast])

  const goBack = useCallback(() => {
    if (!isFirst) {
      setCurrentIndex((i) => i - 1)
      questionStartRef.current = Date.now()
    }
  }, [isFirst])

  const goToQuestion = useCallback((index: number) => {
    setCurrentIndex(index)
    questionStartRef.current = Date.now()
  }, [])

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  return {
    currentQuestion,
    currentIndex,
    goNext,
    goBack,
    goToQuestion,
    saveAnswer,
    isFirst,
    isLast,
    progress,
    answers,
    elapsedTime,
    saveStatus,
    isSaving: saveAnswerMutation.isPending,
    error: error ?? saveAnswerMutation.error,
    isLoading,
    session,
    totalQuestions,
    questions,
  }
}
