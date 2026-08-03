import React, { useRef, useEffect, useState } from 'react'
import type { Question } from '../../types'
import { cn } from '@/lib/utils'

interface DateInputProps {
  question: Question
  value: string | null
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
}

const DateInput: React.FC<DateInputProps> = ({ question, value, onChange, error, disabled }) => {
  const inputRef = useRef<HTMLInputElement>(null)
  const rules = question.validation_rules
  const [open, setOpen] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value)
  }

  const today = new Date().toISOString().split('T')[0]

  return (
    <div className="relative">
      <div className="relative">
        <input
          ref={inputRef}
          type="date"
          value={value ?? ''}
          onChange={handleChange}
          disabled={disabled}
          min={rules?.past_only ? undefined : undefined}
          max={rules?.future_only ? today : undefined}
          aria-label={question.text}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          className={cn(
            'w-full px-4 py-3 border rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50',
            !value && 'text-gray-400'
          )}
        />
        <svg
          className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      </div>
      {value && (
        <p className="text-xs text-gray-500 mt-1">
          Selected: {new Date(value).toLocaleDateString()}
        </p>
      )}
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default React.memo(DateInput)
