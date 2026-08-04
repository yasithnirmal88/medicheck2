import React from 'react'
import Button from '@/shared/ui/Button'
import { cn } from '@/lib/utils'
import type { Question } from '../types'
import Card from '@/shared/ui/Card'

const CardTitle: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ children, className = '' }) => (
  <p className={`text-sm font-medium text-gray-900 dark:text-gray-100 ${className}`}>{children}</p>
)

function ProgressBar({ value, color = 'indigo' }: { value: number; color?: 'indigo' | 'amber' | 'emerald' | 'red' }) {
  const pct = Math.max(0, Math.min(100, value))
  const colorMap = {
    indigo: 'bg-indigo-500',
    amber: 'bg-amber-500',
    emerald: 'bg-emerald-500',
    red: 'bg-red-500',
  }[color]
  return (
    <div className="relative h-2 w-full overflow-hidden rounded-sm bg-gray-200 dark:bg-gray-700">
      <div className={cn('h-full transition-[width] duration-300', colorMap)} style={{ width: `${pct}%` }} />
    </div>
  )
}

interface ReviewScreenProps {
  questions: Question[]
  answers: Record<string, unknown>
  onEdit: (index: number) => void
  onSubmit: () => void
}

const ReviewScreen: React.FC<ReviewScreenProps> = ({ questions, answers, onEdit, onSubmit }) => {
  const unanswered = questions.filter(
    (q) =>
    q.is_required && (answers[q.id] === undefined || answers[q.id] === null || answers[q.id] === '')
  )

  const answeredCount = questions.filter(
    (q) => answers[q.id] !== undefined && answers[q.id] !== null && answers[q.id] !== '',
  ).length
  const completion = Math.round((answeredCount / questions.length) * 100)

  // AI readiness: weighted blend of overall coverage and required completeness.
  const requiredCount = questions.filter((q) => q.is_required).length
  const requiredAnswered = requiredCount - unanswered.length
  const requiredRatio = requiredCount > 0 ? requiredAnswered / requiredCount : 1
  const coverage = questions.length > 0 ? answeredCount / questions.length : 0
  const aiRaw = Math.round(coverage * 0.5 + requiredRatio * 0.5 * 100)
  const aiReadiness = aiRaw - unanswered.length * 4
  const aiReadinessClamped = Math.max(0, Math.min(100, aiReadiness))
  const aiReadinessLabel =
    aiReadinessClamped >= 70
      ? 'Ready for AI analysis'
      : aiReadinessClamped >= 40
        ? 'Partial data, limited AI analysis'
        : 'Insufficient data for AI analysis'
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Review Your Answers</h2>
          <p className="text-sm text-gray-500">Please review all answers before submitting</p>
        </div>
        {unanswered.length > 0 && (
          <div className="px-3 py-1 bg-red-100 dark:bg-red-950 text-red-600 dark:text-red-400 rounded-full text-xs font-medium">
            {unanswered.length} unanswered required
          </div>
        )}
      </div>

      <div className="space-y-3">
        {questions.map((question, index) => {
          const hasAnswer = answers[question.id] !== undefined && answers[question.id] !== null && answers[question.id] !== ''
          const isRequiredMissing = question.is_required && !hasAnswer

          return (
            <div
              key={question.id}
              className={cn(
                'p-4 rounded-lg border',
                isRequiredMissing
                  ? 'border-red-300 bg-red-50 dark:bg-red-950'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-slate-800'
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-gray-400">Q{index + 1}</span>
                    {question.is_required && <span className="text-xs text-red-500">*</span>}
                    {isRequiredMissing && (
                      <span className="text-xs text-red-500 font-medium">Required</span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{question.text}</p>
              <p className={cn(
                        'text-sm mt-1',
                        hasAnswer ? 'text-gray-600 dark:text-gray-300' : 'text-red-400 italic'
                      )}>
                        {hasAnswer
                          ? (() => {
                              const val = answers[question.id]
                              if (typeof val === 'object' && val !== null) {
                                if ('value' in val) return String(val.value)
                                return JSON.stringify(val)
                              }
                              return String(val)
                            })()
                          : 'No answer provided'}
                      </p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => onEdit(index)}
                  className="flex-shrink-0 min-h-[44px]"
                  aria-label={`Edit question ${index + 1}`}
                >
                  Edit
                </Button>
              </div>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card className="p-4">
          <CardTitle className="text-xs font-medium text-gray-500 uppercase">Completion score</CardTitle>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">{completion}%</span>
            <ProgressBar value={completion} />
          </div>
        </Card>

        <Card className="p-4">
          <CardTitle className="text-xs font-medium text-gray-500 uppercase">AI readiness score</CardTitle>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">{aiReadiness}%</span>
            <ProgressBar value={aiReadiness} color={aiReadiness >= 70 ? 'emerald' : aiReadiness >= 40 ? 'amber' : 'red'} />
          </div>
          <span className={cn(
            'inline-block mt-1 rounded-full px-2 py-0.5 text-[10px] font-medium',
            aiReadiness >= 70 ? 'bg-emerald-100 text-emerald-700' : aiReadiness >= 40 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700',
          )}>{aiReadinessLabel}</span>
        </Card>
      </div>

      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <Button
          type="button"
          variant="primary"
          onClick={onSubmit}
          disabled={unanswered.length > 0}
          className="w-full min-h-[44px]"
        >
          {unanswered.length > 0
            ? `Please answer ${unanswered.length} required question(s)`
            : 'Submit All Answers'}
        </Button>
        {unanswered.length > 0 && (
          <p className="text-xs text-red-500 text-center mt-2">
            Required questions must be answered before submitting
          </p>
        )}
      </div>
    </div>
  )
}

export default ReviewScreen
