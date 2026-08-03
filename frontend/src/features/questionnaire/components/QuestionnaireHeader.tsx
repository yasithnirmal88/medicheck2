import React from 'react'
import { Pause, Save, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import AutoSaveIndicator from './AutoSaveIndicator'
import ProgressBar from './ProgressBar'
import type { AssessmentSession } from '../types'

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m ${s.toString().padStart(2, '0')}s`
}

type QuestionnaireHeaderProps = {
  session: AssessmentSession | null
  currentIndex: number
  totalQuestions: number
  answered: number
  elapsedTime: number
  saveStatus: 'idle' | 'saving' | 'saved' | 'error'
  isSaving: boolean
  bodySystemName: string | null
  onPause: () => void
  onExit: () => void
  onSaveDraft: () => void
}

const QuestionnaireHeader: React.FC<QuestionnaireHeaderProps> = ({
  session,
  currentIndex,
  totalQuestions,
  answered,
  elapsedTime,
  saveStatus,
  isSaving,
  bodySystemName,
  onPause,
  onExit,
  onSaveDraft,
}) => {
  const pct = Math.max(0, Math.min(100, ((currentIndex + 1) / totalQuestions) * 100))

  return (
    <div className="flex flex-col gap-4">
      {/* Top bar: question number, body system, controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
            Question {currentIndex + 1} of {totalQuestions}
          </span>
          {bodySystemName && (
            <>
              <span className="hidden h-4 w-px bg-gray-300 dark:bg-gray-600 sm:inline-block" aria-hidden="true" />
              <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
                {bodySystemName}
              </span>
            </>
          )}
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={onSaveDraft}
            disabled={isSaving}
            aria-label="Save draft"
            className={cn(
              'inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700',
              'hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60',
              'disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-600 dark:bg-slate-800 dark:text-gray-200 dark:hover:bg-slate-700',
            )}
          >
            {isSaving ? <AutoSaveIndicator status="saving" /> : <Save className="h-4 w-4" />}
            Save Draft
          </button>
          <button
            type="button"
            onClick={onPause}
            aria-label="Pause assessment"
            className={cn(
              'inline-flex items-center justify-center rounded-lg border border-gray-300 bg-white p-2 text-gray-600',
              'hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60',
              'dark:border-gray-600 dark:bg-slate-800 dark:text-gray-300 dark:hover:bg-slate-700',
            )}
          >
            <Pause className="h-4 w-4" aria-hidden="true" />
          </button>
          <button
            type="button"
            onClick={onExit}
            aria-label="Exit assessment"
            className={cn(
              'inline-flex items-center justify-center rounded-lg border border-transparent bg-red-100 p-2 text-red-600',
              'hover:bg-red-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500/60',
            )}
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>

      {/* Progress: time remaining + progress bar + answered */}
      <div className="flex flex-col gap-2.5">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>
            {answered}/{totalQuestions} answered
          </span>
          <span className="inline-flex items-center gap-1">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <circle cx={12} cy={12} r={10} strokeWidth={2} />
              <path d="M12 8v4l3 3" />
            </svg>
            {formatDuration(elapsedTime)} elapsed
          </span>
        </div>
        <ProgressBar current={currentIndex + 1} total={totalQuestions} percentage={pct} />
        {saveStatus === 'saved' && (
          <AutoSaveIndicator status="saved" />
        )}
      </div>
    </div>
  )
}

export default React.memo(QuestionnaireHeader)
