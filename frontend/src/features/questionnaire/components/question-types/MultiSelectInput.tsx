import React, { useState, useRef, useEffect } from 'react'
import type { Question } from '../../types'
import { cn } from '@/lib/utils'

interface MultiSelectInputProps {
  question: Question
  value: string[]
  onChange: (value: string[]) => void
  error?: string
  disabled?: boolean
}

const MultiSelectInput: React.FC<MultiSelectInputProps> = ({ question, value = [], onChange, error, disabled }) => {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const toggle = (optionValue: string) => {
    const next = value.includes(optionValue)
      ? value.filter((v) => v !== optionValue)
      : [...value, optionValue]
    onChange(next)
  }

  const remove = (optionValue: string) => {
    onChange(value.filter((v) => v !== optionValue))
  }

  const selectedOptions = question.options.filter((o) => value.includes(o.value))

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        aria-label={question.text}
        aria-expanded={open}
        className={cn(
          'w-full px-4 py-3 border rounded-lg text-left focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 flex items-center justify-between min-h-[44px]',
          value.length > 0 ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400'
        )}
      >
        <div className="flex flex-wrap gap-1">
          {selectedOptions.length > 0 ? (
            selectedOptions.slice(0, 3).map((opt) => (
              <span
                key={opt.id}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 rounded-full text-xs"
              >
                {opt.text}
                {!disabled && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      remove(opt.value)
                    }}
                    className="hover:text-indigo-900"
                    aria-label={`Remove ${opt.text}`}
                  >
                    ×
                  </button>
                )}
              </span>
            ))
          ) : (
            <span>Select options...</span>
          )}
          {value.length > 3 && (
            <span className="text-xs text-gray-500">+{value.length - 3} more</span>
          )}
        </div>
        <svg
          className={cn('w-4 h-4 flex-shrink-0 transition-transform', open && 'rotate-180')}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="absolute z-50 mt-1 w-full bg-white dark:bg-slate-800 border rounded-lg shadow-lg max-h-60 overflow-auto">
          {question.options.map((option) => {
            const checked = value.includes(option.value)
            return (
              <button
                key={option.id}
                type="button"
                onClick={() => toggle(option.value)}
                className={cn(
                  'w-full px-4 py-2.5 text-left text-sm hover:bg-indigo-50 dark:hover:bg-indigo-950 flex items-center gap-2 min-h-[44px]',
                  checked && 'bg-indigo-50 dark:bg-indigo-950'
                )}
              >
                <div
                  className={cn(
                    'w-4 h-4 rounded border flex items-center justify-center flex-shrink-0',
                    checked ? 'border-indigo-500 bg-indigo-500' : 'border-gray-300'
                  )}
                >
                  {checked && (
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
                {option.text}
              </button>
            )
          })}
        </div>
      )}
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default React.memo(MultiSelectInput)
