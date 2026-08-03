import React from 'react'
import { Filter, Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export type AssessmentStatus = 'available' | 'in_progress' | 'paused' | 'completed'

export type QuestionnaireFilter = {
  query: string
  status: 'all' | AssessmentStatus
}

type SearchFiltersProps = {
  value: QuestionnaireFilter
  onChange: (value: QuestionnaireFilter) => void
  availableStatuses?: AssessmentStatus[]
  className?: string
}

const STATUS_OPTIONS: AssessmentStatus[] = ['available', 'in_progress', 'paused', 'completed']
const STATUS_LABELS: Record<AssessmentStatus, string> = {
  available: 'Available',
  in_progress: 'In Progress',
  paused: 'Paused',
  completed: 'Completed',
}

const hasActiveFilter = (value: QuestionnaireFilter): boolean =>
  value.status !== 'all' || Boolean(value.query)

const SearchFilters: React.FC<SearchFiltersProps> = ({
  value,
  onChange,
  availableStatuses = STATUS_OPTIONS,
  className,
}) => {
  const activeCount = availableStatuses.filter((s) => value.status === s).length

  const handleStatusToggle = (status: AssessmentStatus) => {
    onChange({
      ...value,
      status: value.status === status ? 'all' : status,
    })
  }

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <div className="relative">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
        <input
          type="search"
          value={value.query}
          onChange={(e) => onChange({ ...value, query: e.target.value })}
          placeholder="Search assessments..."
          className={cn(
            'w-full rounded-xl border border-gray-300 bg-white py-2 pl-10 pr-3 text-sm text-gray-900',
            'placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/60 focus:border-blue-500',
            'dark:border-gray-600 dark:bg-slate-900 dark:text-gray-100 dark:placeholder:text-gray-500',
          )}
        />
        {value.query ? (
          <button
            type="button"
            onClick={() => onChange({ ...value, query: '' })}
            aria-label="Clear search"
            className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded p-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
          >
            <X className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-600 dark:text-gray-300">
          <Filter className="h-3.5 w-3.5" aria-hidden="true" />
          Filter
        </span>
        {availableStatuses.map((status) => {
          const isActive = value.status === status
          return (
            <button
              key={status}
              type="button"
              onClick={() => handleStatusToggle(status)}
              className={cn(
                'rounded-full px-3 py-1 text-xs font-medium transition-colors',
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-slate-800 dark:text-gray-200 dark:hover:bg-slate-700',
              )}
            >
              {STATUS_LABELS[status]}
            </button>
          )
        })}
        {hasActiveFilter(value) && (
          <button
            type="button"
            onClick={() => onChange({ query: '', status: 'all' })}
            aria-label="Reset filters"
            className="rounded-full px-3 py-1 text-xs font-medium text-gray-500 hover:underline dark:text-gray-400"
          >
            Reset
          </button>
        )}
      </div>

      {(activeCount || value.query) && (
        <div className="flex flex-wrap items-center gap-1.5 py-1 text-xs text-gray-500 dark:text-gray-400">
          {value.query && <span>Search: "{value.query}"</span>}
          {availableStatuses
            .filter((s) => value.status === s)
            .map((s) => (
              <span
                key={s}
                className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 dark:bg-gray-700"
              >
                {STATUS_LABELS[s]}
                <X className="h-3 w-3" />
              </span>
            ))}
        </div>
      )}
    </div>
  )
}

export default React.memo(SearchFilters)
