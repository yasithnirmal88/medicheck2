import React from 'react'
import type { Question } from '../../types'
import { cn } from '@/lib/utils'

interface SingleChoiceProps {
  question: Question
  value: string | null
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
}

const SingleChoice: React.FC<SingleChoiceProps> = ({ question, value, onChange, error, disabled }) => {
  return (
    <div role="radiogroup" aria-label={question.text} className="space-y-2">
      {question.options.map((option) => (
        <label
          key={option.id}
          className={cn(
            'flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors min-h-[44px]',
            value === option.value
              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          style={
            option.color_hex && value === option.value
              ? { borderColor: option.color_hex, backgroundColor: option.color_hex + '20' }
              : undefined
          }
        >
          <input
            type="radio"
            name={question.id}
            value={option.value}
            checked={value === option.value}
            onChange={() => onChange(option.value)}
            disabled={disabled}
            className="sr-only"
            aria-label={option.text}
          />
          <div
            className={cn(
              'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0',
              value === option.value
                ? 'border-indigo-500'
                : 'border-gray-300 dark:border-gray-600'
            )}
            style={
              option.color_hex && value === option.value
                ? { borderColor: option.color_hex }
                : undefined
            }
          >
            {value === option.value && (
              <div
                className="w-2.5 h-2.5 rounded-full bg-indigo-500"
                style={option.color_hex ? { backgroundColor: option.color_hex } : undefined}
              />
            )}
          </div>
          <span className="text-sm font-medium">{option.text}</span>
        </label>
      ))}
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default React.memo(SingleChoice)
