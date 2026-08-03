import { cn } from '@/lib/utils'
import { Filter, Search, RotateCw } from 'lucide-react'
import { motion } from 'framer-motion'
import type { AssessmentFilters as FilterState, AIPriority, Difficulty, AssessmentStatus } from '../types'

const STATUS_OPTIONS: { value: AssessmentStatus; label: string }[] = [
  { value: 'not_started', label: 'Not Started' },
  { value: 'completed', label: 'Completed' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'recommended', label: 'Recommended' },
]

const DURATION_OPTIONS = [
  { value: 'short', label: 'Under 6 min' },
  { value: 'medium', label: '6–10 min' },
  { value: 'long', label: 'Over 10 min' },
]

export const AssessmentFilters = ({
  filters,
  onChange,
  onReset,
}: {
  filters: FilterState
  onChange: (f: Partial<FilterState>) => void
  onReset: () => void
}) => {
  const toggleStatus = (s: AssessmentStatus) => {
    const set = new Set(filters.status)
    set.has(s) ? set.delete(s) : set.add(s)
    onChange({ status: Array.from(set) })
  }
  const toggleDifficulty = (d: Difficulty) => {
    const set = new Set(filters.difficulty)
    set.has(d) ? set.delete(d) : set.add(d)
    onChange({ difficulty: Array.from(set) })
  }
  const togglePriority = (p: AIPriority) => {
    const set = new Set(filters.priority)
    set.has(p) ? set.delete(p) : set.add(p)
    onChange({ priority: Array.from(set) })
  }

  return (
    <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="space-y-3">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-xs">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
          <input
            type="search"
            placeholder="Search assessments..."
            value={filters.search}
            onChange={(e) => onChange({ search: e.target.value })}
            className={cn(
              'w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 py-2 text-sm outline-none',
              'dark:border-slate-700 dark:bg-slate-800/70',
            )}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onReset}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700',
              'hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800',
            )}
          >
            <RotateCw className="h-3.5 w-3.5" />
            Reset Filters
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <Filter className="h-3.5 w-3.5" />
          <span>Status:</span>
        </div>
        {STATUS_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => toggleStatus(opt.value)}
            className={cn(
              'rounded-full px-3 py-1 text-xs font-medium transition-colors',
              filters.status.includes(opt.value)
                ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300',
            )}
          >
            {opt.label}
          </button>
        ))}

        <span className="mx-1 h-4 w-px bg-slate-300 dark:bg-slate-700" />

        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <span>Duration:</span>
        </div>
        {DURATION_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange({ duration: opt.value as FilterState['duration'] })}
            className={cn(
              'rounded-full px-3 py-1 text-xs font-medium transition-colors',
              filters.duration === opt.value
                ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300',
            )}
          >
            {opt.label}
          </button>
        ))}

        <span className="mx-1 h-4 w-px bg-slate-300 dark:bg-slate-700" />

        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <span>Difficulty:</span>
        </div>
        {(['Beginner', 'Intermediate', 'Advanced'] as Difficulty[]).map((d) => (
          <button
            key={d}
            type="button"
            onClick={() => toggleDifficulty(d)}
            className={cn(
              'rounded-full px-3 py-1 text-xs font-medium transition-colors',
              filters.difficulty.includes(d)
                ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300',
            )}
          >
            {d}
          </button>
        ))}

        <span className="mx-1 h-4 w-px bg-slate-300 dark:bg-slate-700" />

        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <span>AI Priority:</span>
        </div>
        {(['high', 'medium', 'low'] as AIPriority[]).map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => togglePriority(p)}
            className={cn(
              'rounded-full px-3 py-1 text-xs font-medium capitalize transition-colors',
              filters.priority.includes(p)
                ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300',
            )}
          >
            {p}
          </button>
        ))}
      </div>
    </motion.div>
  )
}
