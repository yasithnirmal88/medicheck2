import React from 'react'
import { CheckCircle2, AlertCircle, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { SectionKey } from '@/features/profile/types/wizard'
import { fieldSpecs } from '@/features/profile/wizard/fieldSpecs'

interface ProfileCompletionProps {
  state: Record<string, unknown>
  onSectionClick?: (key: SectionKey) => void
}

export function ProfileCompletion({ state, onSectionClick }: ProfileCompletionProps) {
  const { totalPct, sections } = React.useMemo(() => {
    let totalFilled = 0
    let totalRequired = 0
    const sectionData: Record<string, { filled: number; total: number; pct: number; label: string; icon: string }> = {}

    for (const [key, specs] of Object.entries(fieldSpecs)) {
      if (specs.length === 0) continue
      const record = (state[key] as Record<string, unknown>) ?? {}
      let filled = 0
      let total = 0
      for (const spec of specs) {
        if (spec.kind === 'checkbox') {
          total++
          if (record[spec.name]) filled++
          continue
        }
        if (spec.optional) continue
        total++
        const val = record[spec.name]
        const hasValue =
          val !== undefined &&
          val !== null &&
          val !== '' &&
          (typeof val !== 'string' || (val as string).trim() !== '') &&
          !(Array.isArray(val) && (val as unknown[]).length === 0)
        if (hasValue) filled++
      }
      totalFilled += filled
      totalRequired += total
      const pct = total > 0 ? Math.round((filled / total) * 100) : 0
      sectionData[key] = { filled, total, pct, label: key.replace(/_/g, ' '), icon: '📋' }
    }

    const totalPct = totalRequired > 0 ? Math.round((totalFilled / totalRequired) * 100) : 0
    return { totalPct, sections: sectionData }
  }, [state])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-blue-500" />
          Profile Completion
        </h3>
        <span className="text-lg font-bold text-slate-800 dark:text-slate-100">{totalPct}%</span>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500',
            totalPct >= 80 ? 'bg-emerald-500' : totalPct >= 50 ? 'bg-amber-400' : 'bg-red-400',
          )}
          style={{ width: `${totalPct}%` }}
          role="progressbar"
          aria-valuenow={totalPct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Profile completion: ${totalPct}%`}
        />
      </div>

      <div className="grid grid-cols-2 gap-2">
        {Object.entries(sections).map(([key, data]) => (
          <button
            key={key}
            type="button"
            onClick={() => onSectionClick?.(key as SectionKey)}
            className={cn(
              'flex items-center justify-between rounded-lg border p-2 text-left transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700',
              data.pct === 100 && 'border-emerald-200 bg-emerald-50 dark:border-emerald-800/50 dark:bg-emerald-900/20',
              data.pct > 0 && data.pct < 100 && 'border-amber-200 bg-amber-50 dark:border-amber-800/50 dark:bg-amber-900/20',
              data.pct === 0 && 'border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800',
            )}
            aria-label={`${data.label}: ${data.pct}% complete`}
          >
            <span className="text-xs font-medium text-slate-700 dark:text-slate-300">{data.label}</span>
            <div className="flex items-center gap-1">
              {data.pct === 100 ? (
                <CheckCircle2 className="h-3 w-3 text-emerald-500" />
              ) : data.pct > 0 ? (
                <div className="h-1.5 w-12 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                  <div className="h-full rounded-full bg-amber-400" style={{ width: `${data.pct}%` }} />
                </div>
              ) : (
                <AlertCircle className="h-3 w-3 text-slate-400" />
              )}
              <span className="text-xs text-slate-500 dark:text-slate-400">{data.pct}%</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}