import React, { useState, useRef, useEffect } from 'react'
import type { Question } from '../../types'
import { cn } from '@/lib/utils'

interface DropdownInputProps {
  question: Question
  value: string | null
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
}

const DropdownInput: React.FC<DropdownInputProps> = ({ question, value, onChange, error, disabled }) => {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const searchable = question.validation_rules?.search

  const selectedOption = question.options.find((o) => o.value === value)

  const filtered = searchable
    ? question.options.filter((o) => o.text.toLowerCase().includes(search.toLowerCase()))
    : question.options

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const select = (optionValue: string) => {
    onChange(optionValue)
    setOpen(false)
    setSearch('')
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        aria-label={question.text}
        aria-expanded={open}
        className={cn(
          'w-full px-4 py-3 border rounded-lg text-left focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 flex items-center justify-between',
          value ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400'
        )}
      >
        <span>{selectedOption ? selectedOption.text : 'Select an option...'}</span>
        <svg
          className={cn('w-4 h-4 transition-transform', open && 'rotate-180')}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="absolute z-50 mt-1 w-full bg-white dark:bg-slate-800 border rounded-lg shadow-lg max-h-60 overflow-auto">
          {searchable && (
            <div className="p-2 border-b sticky top-0 bg-white dark:bg-slate-800">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search..."
                className="w-full px-3 py-2 border rounded text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
                autoFocus
              />
            </div>
          )}
          {filtered.length === 0 ? (
            <div className="p-3 text-sm text-gray-500 text-center">No options found</div>
          ) : (
            filtered.map((option) => (
              <button
                key={option.id}
                type="button"
                onClick={() => select(option.value)}
                className={cn(
                  'w-full px-4 py-2.5 text-left text-sm hover:bg-indigo-50 dark:hover:bg-indigo-950 min-h-[44px]',
                  value === option.value && 'bg-indigo-50 dark:bg-indigo-950 font-medium'
                )}
              >
                {option.text}
              </button>
            ))
          )}
        </div>
      )}
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default React.memo(DropdownInput)
