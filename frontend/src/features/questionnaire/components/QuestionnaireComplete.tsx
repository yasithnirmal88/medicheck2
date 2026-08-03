import React from 'react'
import Button from '@/shared/ui/Button'
import Card from '@/shared/ui/Card'
import type { AssessmentSession } from '../types'

interface QuestionnaireCompleteProps {
  session: AssessmentSession
  score?: { total: number; max: number; label?: string } | null
  onReturnToDashboard: () => void
  onViewResults?: () => void
}

const QuestionnaireComplete: React.FC<QuestionnaireCompleteProps> = ({
  session,
  score,
  onReturnToDashboard,
  onViewResults,
}) => {
  const progress = session.progress

  return (
    <div className="max-w-lg mx-auto text-center py-8">
      <div className="mb-6">
        <div className="w-20 h-20 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mx-auto mb-4">
          <svg className="w-10 h-10 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Assessment Complete</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Thank you for completing the assessment</p>
      </div>

      <Card className="text-left space-y-4 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 border-b pb-2">Session Summary</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-500">Questions Answered</p>
            <p className="text-lg font-semibold">{progress?.answered_questions ?? 0}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Total Questions</p>
            <p className="text-lg font-semibold">{progress?.total_questions ?? 0}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Completion</p>
            <p className="text-lg font-semibold">
              {progress ? Math.round(progress.completion_percentage) : 0}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Status</p>
            <p className="text-lg font-semibold capitalize">{session.status}</p>
          </div>
        </div>

        {score && (
          <div className="border-t pt-4">
            <p className="text-xs text-gray-500 mb-1">{score.label ?? 'Score'}</p>
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-bold text-indigo-600">{score.total}</span>
              <span className="text-gray-400">/ {score.max}</span>
            </div>
          </div>
        )}
      </Card>

      <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
        {onViewResults && (
          <Button
            variant="primary"
            onClick={onViewResults}
            className="min-h-[44px] min-w-[200px]"
          >
            View AI Report
          </Button>
        )}
        <Button onClick={onReturnToDashboard} className="min-h-[44px] min-w-[200px]">
          Return to Dashboard
        </Button>
      </div>
    </div>
  )
}

export default QuestionnaireComplete
