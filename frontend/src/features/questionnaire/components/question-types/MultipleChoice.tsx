import React from 'react'
import type { Question } from '../../types'
import { cn } from '@/lib/utils'

interface MultipleChoiceProps {
  question: Question
  value: string[]
  onChange: (value: string[]) => void
  error?: string
  disabled?: boolean
}

const MultipleChoice: React.FC<MultipleChoiceProps> = ({ question, value = [], onChange, error, disabled }) => {
  const minSel = question.validation_rules?.min_selections
  const maxSel = question.validation_rules?.max_selections

  const toggle = (optionValue: string) => {
    if (disabled) return
    const next = value.includes(optionValue)
      ? value.filter((v) => v !== optionValue)
      : maxSel && value.length >= maxSel
        ? value
        : [...value, optionValue]
    onChange(next)
  }

  return (
    <div role="group" aria-label={question.text}>
      <div className="text-xs text-gray-500 mb-2">
        {value.length} selected
        {maxSel && ` (max ${maxSel})`}
        {minSel && ` (min ${minSel})`}
      </div>
      <div className="space-y-2">
        {question.options.map((option) => {
          const checked = value.includes(option.value)
          return (
            <label
              key={option.id}
              className={cn(
                'flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors min-h-[44px]',
                checked
                  ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300',
                disabled && 'opacity-50 cursor-not-allowed'
              )}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => toggle(option.value)}
                disabled={disabled}
                className="sr-only"
                aria-label={option.text}
              />
              <div
                className={cn(
                  'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0',
                  checked ? 'border-indigo-500 bg-indigo-500' : 'border-gray-300 dark:border-gray-600'
                )}
              >
                {checked && (
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </div>
              <span className="text-sm font-medium">{option.text}</span>
            </label>
          )
        })}
      </div>
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default React.memo(MultipleChoice)
