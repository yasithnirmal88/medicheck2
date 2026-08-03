import React, { useState, useRef, useEffect } from 'react'
import type { Question } from '../../types'
import { cn } from '@/lib/utils'

interface SearchInputProps {
  question: Question
  value: string | null
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
  onSearch?: (query: string) => Promise<{ id: string; text: string; value: string }[]>
}

const SearchInput: React.FC<SearchInputProps> = ({ question, value, onChange, error, disabled, onSearch }) => {
  const [query, setQuery] = useState(value ?? '')
  const [results, setResults] = useState<{ id: string; text: string; value: string }[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const q = e.target.value
    setQuery(q)
    if (!onSearch) return

    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (q.length < 2) {
      setResults([])
      setOpen(false)
      return
    }

    setLoading(true)
    setOpen(true)
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await onSearch(q)
        setResults(res)
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 300)
  }

  const select = (item: { id: string; text: string; value: string }) => {
    onChange(item.value)
    setQuery(item.text)
    setOpen(false)
  }

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleQueryChange}
          onFocus={() => results.length > 0 && setOpen(true)}
          disabled={disabled}
          aria-label={question.text}
          placeholder="Search..."
          className={cn(
            'w-full px-4 py-3 border rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50'
          )}
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>
      {open && (
        <div className="absolute z-50 mt-1 w-full bg-white dark:bg-slate-800 border rounded-lg shadow-lg max-h-60 overflow-auto">
          {results.length === 0 && !loading && (
            <div className="p-3 text-sm text-gray-500 text-center">No results found</div>
          )}
          {results.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => select(item)}
              className="w-full px-4 py-2.5 text-left text-sm hover:bg-indigo-50 dark:hover:bg-indigo-950 min-h-[44px]"
            >
              {item.text}
            </button>
          ))}
        </div>
      )}
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default React.memo(SearchInput)
