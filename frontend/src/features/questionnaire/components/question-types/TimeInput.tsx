import React from 'react'
import type { Question } from '../../types'
import { cn } from '@/lib/utils'

interface TimeInputProps {
  question: Question
  value: string | null
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
}

const TimeInput: React.FC<TimeInputProps> = ({ question, value, onChange, error, disabled }) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value)
  }

  return (
    <div>
      <input
        type="time"
        value={value ?? ''}
        onChange={handleChange}
        disabled={disabled}
        aria-label={question.text}
        className={cn(
          'w-full px-4 py-3 border rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50',
          !value && 'text-gray-400'
        )}
      />
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default React.memo(TimeInput)
