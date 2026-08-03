import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Clock3, Stethoscope } from 'lucide-react'
import { cn } from '@/lib/utils'
import Card from './Card'
import EmptyState from './EmptyState'
import { Skeleton } from './LoadingSkeleton'

export type UpcomingAssessment = {
  id: string
  name: string
  duration?: number | string
  priority: 'low' | 'medium' | 'high'
  recommendedDate?: string
  reason?: string
}

interface UpcomingAssessmentsProps {
  items: UpcomingAssessment[]
  loading?: boolean
}

const priorityMeta: Record<UpcomingAssessment['priority'], { color: string; dot: string; label: string }> = {
  low: { color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300', dot: 'bg-emerald-500', label: 'Low' },
  medium: { color: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300', dot: 'bg-amber-500', label: 'Medium' },
  high: { color: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300', dot: 'bg-red-500', label: 'High' },
}

export const UpcomingAssessments: React.FC<UpcomingAssessmentsProps> = ({ items, loading }) => {
  return (
    <Card className="flex h-full flex-col">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Upcoming Assessments</h3>
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-500/15 dark:text-blue-300">
          <Stethoscope className="h-4 w-4" />
        </span>
      </div>

      <div className="mt-4 flex-1 space-y-3">
        {loading ? (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <EmptyState icon={Stethoscope} title="No assessments scheduled" description="Recommended assessments will appear here." />
        ) : (
          items.map((item) => {
            const prio = priorityMeta[item.priority]
            return (
              <div
                key={item.id}
                className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50/60 p-3 transition-colors hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800/60 dark:hover:border-slate-600"
              >
                <span className={cn('h-2.5 w-2.5 shrink-0 rounded-full', prio.dot)} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">{item.name}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-slate-400">
                    {item.duration !== undefined ? (
                      <span className="inline-flex items-center gap-1">
                        <Clock3 className="h-3 w-3" />
                        {formatDuration(item.duration)}
                      </span>
                    ) : null}
                    <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium', prio.color)}>
                      {prio.label} priority
                    </span>
                  </div>
                </div>
                <Link
                  to="/questionnaires"
                  className="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-blue-700"
                >
                  Start
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            )
          })
        )}
      </div>
    </Card>
  )
}

function formatDuration(value: number | string): string {
  if (typeof value === 'number') return `~${value} min`
  return value
}

export default UpcomingAssessments