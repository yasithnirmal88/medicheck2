import React, { useCallback } from 'react'
import type { Question } from '../../types'
import { cn } from '@/lib/utils'

interface SliderInputProps {
  question: Question
  value: number | null
  onChange: (value: number) => void
  error?: string
  disabled?: boolean
}

const colorForValue = (value: number, min: number, max: number): string => {
  const range = max - min
  if (range === 0) return '#22c55e'
  const pct = (value - min) / range
  if (pct < 0.33) return '#22c55e'
  if (pct < 0.66) return '#eab308'
  return '#ef4444'
}

const SliderInput: React.FC<SliderInputProps> = ({ question, value, onChange, error, disabled }) => {
  const rules = question.validation_rules
  const min = rules?.min ?? 0
  const max = rules?.max ?? 100
  const step = rules?.step ?? 1
  const current = value ?? min
  const color = colorForValue(current, min, max)
  const pct = ((current - min) / (max - min)) * 100

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange(parseFloat(e.target.value))
    },
    [onChange]
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500">{min}</span>
        <span
          className="text-2xl font-bold tabular-nums"
          style={{ color }}
        >
          {current}
        </span>
        <span className="text-xs text-gray-500">{max}</span>
      </div>
      <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full">
        <div
          className="absolute top-0 left-0 h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={current}
          onChange={handleChange}
          disabled={disabled}
          aria-label={question.text}
          className={cn(
            'absolute top-0 left-0 w-full h-full opacity-0 cursor-pointer',
            disabled && 'cursor-not-allowed'
          )}
        />
        <div
          className="absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-white border-2 shadow-md pointer-events-none transition-all"
          style={{
            left: `calc(${pct}% - 10px)`,
            borderColor: color,
          }}
        />
      </div>
      {rules?.unit && (
        <p className="text-xs text-gray-500 mt-1 text-center">{rules.unit}</p>
      )}
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default React.memo(SliderInput)
