import React, { useState, useCallback, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AlertCircle, ClipboardList } from 'lucide-react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import Skeleton from '@/shared/ui/Skeleton'
import Button from '@/shared/ui/Button'
import QuestionnaireHeader from '../components/QuestionnaireHeader'
import QuestionnaireSidebar from '../components/QuestionnaireSidebar'
import { AssessmentSummary } from '../components/AssessmentSummary'
import QuestionnaireComplete from '../components/QuestionnaireComplete'
import ReviewScreen from '../components/ReviewScreen'
import QuestionRenderer from '../components/QuestionRenderer'
import useQuestionnaireFlow from '../hooks/useQuestionnaireFlow'

type Phase = 'question' | 'review' | 'complete'

const QuestionnaireSessionPage: React.FC = () => {
  const { id: sessionId } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [phase, setPhase] = useState<Phase>('question')
  const [localError, setLocalError] = useState<string | undefined>()
  const [reviewAnswers, setReviewAnswers] = useState<Record<string, unknown>>({})

  const {
    session,
    currentQuestion,
    answers,
    history,
    progress,
     answered,
     skipped,
     bodySystemsCovered,
     estimatedTimeRemaining,
     totalQuestions,
    isFirst,
    isLast,
    canGoNext,
    isSubmitting,
    isLoading,
    error: sessionError,
    saveStatus,
    isSaving,
    completeMutation,
    submitAnswer,
    next,
    skip,
    goBack,
    recoverDraft,
    pause,
    resume,
  } = useQuestionnaireFlow(sessionId)

  // Recover any local draft on mount.
  useEffect(() => {
    if (sessionId) recoverDraft()
  }, [sessionId, recoverDraft])

  useEffect(() => {
    if (sessionError) {
      setLocalError('An error occurred loading the session. Please try again.')
    }
  }, [sessionError])

  const handleAnswerChange = useCallback(
    (value: unknown) => {
      if (!currentQuestion) return
      setLocalError(undefined)
      submitAnswer(value)
    },
    [currentQuestion, submitAnswer],
  )

  const handleNext = useCallback(() => {
    if (!currentQuestion) return
    if (currentQuestion.is_required) {
      const val = answers[currentQuestion.id]?.value
      if (val === undefined || val === null || val === '') {
        setLocalError('This question is required')
        return
      }
    }
    if (isLast) {
      setReviewAnswers({ ...answers })
      setPhase('review')
      return
    }
    next()
  }, [currentQuestion, answers, isLast, next])

  const handleSkip = useCallback(() => {
    if (!currentQuestion) return
    skip('')
  }, [currentQuestion, skip])

  const handleBack = useCallback(() => {
    if (!isFirst) goBack()
  }, [isFirst, goBack])

  const handleSubmitReview = useCallback(() => {
    if (!sessionId) return
    completeMutation.mutate(sessionId, {
      onSuccess: () => setPhase('complete'),
      onError: () => setLocalError('Failed to submit. Please try again.'),
    })
  }, [sessionId, completeMutation])

  const handleResume = useCallback(() => {
    resume()
    setLocalError(undefined)
  }, [resume])

  const handleReturnToDashboard = () => navigate('/')
  const handleBackToAssessments = () => navigate('/questionnaires')
  const handleViewResults = useCallback(() => {
    if (sessionId) navigate(`/assessments/${sessionId}/results`)
  }, [sessionId, navigate])
  const handleExit = () => {
    if (window.confirm('Exit the assessment? Your progress has been saved automatically.')) {
      navigate('/questionnaires')
    }
  }

  if (isLoading) {
    return (
      <AppLayout>
        <div className="mx-auto max-w-5xl p-4">
          <Skeleton className="mb-4 h-8 w-3/4" />
          <Skeleton className="mb-2 h-4 w-2/3" />
          <Skeleton className="h-64 w-full" />
          <div className="mt-4 flex justify-between">
            <Skeleton className="h-10 w-24" />
            <Skeleton className="h-10 w-24" />
          </div>
        </div>
      </AppLayout>
    )
  }

  if (!session) {
    return (
      <AppLayout>
        <div className="mx-auto max-w-2xl p-4 text-center">
          <div className="mb-6 rounded-full bg-gray-100 p-4 dark:bg-gray-800">
            <AlertCircle className="mx-auto h-6 w-6 text-gray-400" aria-hidden="true" />
          </div>
          <p className="text-gray-500">Session not found</p>
          <Button onClick={handleBackToAssessments} className="mt-4 min-h-[44px]">
            Back to Assessments
          </Button>
        </div>
      </AppLayout>
    )
  }

  if (phase === 'complete') {
    return (
      <AppLayout>
        <div className="mx-auto max-w-3xl p-4">
           <QuestionnaireComplete session={session} score={null} onReturnToDashboard={handleReturnToDashboard} onViewResults={handleViewResults} />
        </div>
      </AppLayout>
    )
  }

  if (phase === 'review') {
    return (
      <AppLayout>
        <div className="mx-auto max-w-3xl p-4">
          <Card>
            <ReviewScreen
              questions={currentQuestion ? [currentQuestion] : []}
              answers={reviewAnswers}
              onEdit={() => setPhase('question')}
              onSubmit={handleSubmitReview}
            />
          </Card>
        </div>
      </AppLayout>
    )
  }

  const completionPercentage = progress?.completion_percentage ?? 0

  return (
    <AppLayout>
      <div className="mx-auto max-w-6xl p-4">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-start">
          {/* Main column */}
          <div className="flex-1 space-y-6">
            {/* Header: question number, body system, time remaining, pause/save-draft/exit */}
            <QuestionnaireHeader
              session={session}
              currentIndex={history.length}
              totalQuestions={totalQuestions}
              answered={answered}
              elapsedTime={0}
              saveStatus={saveStatus}
              isSaving={isSaving}
              bodySystemName={currentQuestion ? currentQuestion.body_system_id ?? null : null}
              onPause={pause}
              onExit={handleExit}
              onSaveDraft={() => {}}
            />

            {/* Live assessment summary */}
            <AssessmentSummary
              flow={{
                answered,
                skipped,
                totalQuestions,
                bodySystemsCovered,
                estimatedTimeRemaining,
                progress,
              }}
            />
            {/* Question card */}
            <Card className="min-h-[260px]">
              {session.status === 'paused' && (
                <div className="mb-4 rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-center dark:border-yellow-900/50 dark:bg-yellow-900/20">
                  <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Assessment is paused</p>
                  <p className="text-xs text-yellow-700 dark:text-yellow-300">Your progress is saved. Click Resume to continue.</p>
                </div>
              )}

              {currentQuestion ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="flex items-baseline gap-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {currentQuestion.text}
                      {currentQuestion.is_required && <span className="text-red-500">*</span>}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Question {history.length + 1} of {totalQuestions || '...'}
                    </p>
                  </div>
                  <QuestionRenderer
                    question={currentQuestion}
                    value={answers[currentQuestion.id]?.value ?? null}
                    onChange={handleAnswerChange}
                    error={localError}
                    disabled={isSaving || session.status === 'paused'}
                  />
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
                  <span className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-gray-400 dark:bg-gray-800">
                    <ClipboardList className="h-6 w-6" aria-hidden="true" />
                  </span>
                  <p className="text-gray-500 dark:text-gray-300">No more questions</p>
                  <Button variant="primary" onClick={() => setPhase('review')} disabled={isSubmitting} className="mt-2 min-h-[44px]">
                    Review &amp; Submit
                  </Button>
                </div>
              )}
            </Card>

            {/* Navigation: Previous / Skip / Next */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {!isFirst && (
                  <Button variant="ghost" onClick={handleBack} disabled={isSubmitting} className="min-h-[44px]">
                    Previous
                  </Button>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  onClick={handleSkip}
                  disabled={isSubmitting || currentQuestion == null}
                  className="min-h-[44px]"
                >
                  Skip
                </Button>
                {session.status === 'paused' ? (
                  <Button variant="primary" onClick={handleResume} disabled={isSubmitting} className="min-h-[44px]">
                    Resume
                  </Button>
                ) : isLast ? (
                  <Button variant="primary" onClick={() => {
                    setReviewAnswers({ ...answers })
                    setPhase('review')
                  }} disabled={isSubmitting} className="min-h-[44px]">
                    Review
                  </Button>
                ) : (
                  <Button variant="primary" onClick={handleNext} disabled={!canGoNext || isSubmitting} className="min-h-[44px]">
                    Next
                  </Button>
                )}
              </div>
            </div>

            {localError && (
              <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
                <AlertCircle className="mt-0.25 h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{localError}</span>
              </div>
            )}
          </div>

          {/* Right sidebar: why matters, explanation, tips, body system, progress, confidence, AI chat */}
          <div className="w-full xl:w-80">
            <QuestionnaireSidebar
              question={currentQuestion}
              answered={answered}
              totalQuestions={totalQuestions}
              completionPercentage={completionPercentage}
              saveStatus={saveStatus}
              isSaving={isSaving}
            />
          </div>
        </div>
      </div>
    </AppLayout>
  )
}

export default QuestionnaireSessionPage
