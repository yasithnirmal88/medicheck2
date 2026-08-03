import React from 'react'
import type { Question } from '../../types'

interface NumericInputProps {
  question: Question
  value: number | null
  onChange: (value: number | null) => void
  error?: string
  disabled?: boolean
}

const NumericInput: React.FC<NumericInputProps> = ({ question, value, onChange, error, disabled }) => {
  const rules = question.validation_rules
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value
    if (raw === '') {
      onChange(null)
      return
    }
    const num = parseInt(raw, 10)
    if (!isNaN(num)) {
      let clamped = num
      if (rules?.min !== undefined) clamped = Math.max(clamped, rules.min)
      if (rules?.max !== undefined) clamped = Math.min(clamped, rules.max)
      onChange(clamped)
    }
  }

  return (
    <div>
      <div className="relative">
        <input
          type="number"
          value={value ?? ''}
          onChange={handleChange}
          disabled={disabled}
          min={rules?.min}
          max={rules?.max}
          step={rules?.step ?? 1}
          aria-label={question.text}
          className="w-full px-4 py-3 border rounded-lg text-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          placeholder="Enter a number"
        />
        {rules?.unit && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">{rules.unit}</span>
        )}
      </div>
      {rules && (rules.min !== undefined || rules.max !== undefined) && (
        <p className="text-xs text-gray-500 mt-1">
          {rules.min !== undefined && `Min: ${rules.min}`}
          {rules.min !== undefined && rules.max !== undefined && ' | '}
          {rules.max !== undefined && `Max: ${rules.max}`}
        </p>
      )}
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default React.memo(NumericInput)
