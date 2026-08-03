import React from 'react'
import type { Question } from '../../types'
import { cn } from '@/lib/utils'

interface YesNoProps {
  question: Question
  value: boolean | null
  onChange: (value: boolean) => void
  error?: string
  disabled?: boolean
}

const YesNo: React.FC<YesNoProps> = ({ question, value, onChange, error, disabled }) => {
  return (
    <div role="radiogroup" aria-label={question.text}>
      <div className="grid grid-cols-2 gap-4">
        <button
          type="button"
          onClick={() => onChange(true)}
          disabled={disabled}
          aria-label="Yes"
          className={cn(
            'flex flex-col items-center justify-center p-6 rounded-xl border-2 min-h-[80px] transition-all',
            value === true
              ? 'border-green-500 bg-green-50 dark:bg-green-950 shadow-md'
              : 'border-gray-200 dark:border-gray-700 hover:border-green-300',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          <svg className="w-8 h-8 text-green-600 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-lg font-semibold text-green-700 dark:text-green-400">Yes</span>
        </button>
        <button
          type="button"
          onClick={() => onChange(false)}
          disabled={disabled}
          aria-label="No"
          className={cn(
            'flex flex-col items-center justify-center p-6 rounded-xl border-2 min-h-[80px] transition-all',
            value === false
              ? 'border-red-500 bg-red-50 dark:bg-red-950 shadow-md'
              : 'border-gray-200 dark:border-gray-700 hover:border-red-300',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          <svg className="w-8 h-8 text-red-600 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          <span className="text-lg font-semibold text-red-700 dark:text-red-400">No</span>
        </button>
      </div>
      {error && <p className="text-sm text-red-500 mt-2 text-center">{error}</p>}
    </div>
  )
}

export default React.memo(YesNo)
