import React from 'react'
import { Link } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import { ArrowRight, Activity, ClipboardList, FlaskConical, HeartPulse, Target } from 'lucide-react'
import { cn } from '@/lib/utils'
import Card from './Card'
import EmptyState from './EmptyState'
import { Skeleton } from './LoadingSkeleton'
import { formatRelative } from '../utils/format'

export type TimelineItem = {
  id: string
  title: string
  description?: string
  time?: string
  type: 'questionnaire' | 'report' | 'lab' | 'assessment' | 'lifestyle'
}

interface HealthTimelineProps {
  items: TimelineItem[]
  loading?: boolean
}

const typeMeta: Record<TimelineItem['type'], { icon: LucideIcon; tint: string; ring: string }> = {
  questionnaire: { icon: ClipboardList, tint: 'bg-blue-600', ring: 'ring-blue-200 dark:ring-blue-500/30' },
  report: { icon: Target, tint: 'bg-teal-600', ring: 'ring-teal-200 dark:ring-teal-500/30' },
  assessment: { icon: Activity, tint: 'bg-violet-600', ring: 'ring-violet-200 dark:ring-violet-500/30' },
  lab: { icon: FlaskConical, tint: 'bg-amber-500', ring: 'ring-amber-200 dark:ring-amber-500/30' },
  lifestyle: { icon: HeartPulse, tint: 'bg-emerald-600', ring: 'ring-emerald-200 dark:ring-emerald-500/30' },
}

export const HealthTimeline: React.FC<HealthTimelineProps> = ({ items, loading }) => {
  return (
    <Card className="flex h-full flex-col">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Health Timeline</h3>
        <Link to="/timeline" className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-300">
          Open timeline
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      <div className="relative mt-5 flex-1">
        {loading ? (
          <div className="space-y-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <EmptyState icon={Activity} title="Nothing to show yet" description="Your health timeline will build as you complete activities." />
        ) : (
          <ol className="space-y-5">
            {items.slice(0, 6).map((item, index) => {
              const meta = typeMeta[item.type]
              const isLast = index === Math.min(items.length, 6) - 1
              return (
                <li key={item.id} className="relative flex gap-4 pl-2">
                  {!isLast ? <span className="absolute left-[19px] top-10 h-full w-px bg-slate-200 dark:bg-slate-700" /> : null}
                  <span className={cn('relative z-10 mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ring-4', meta.tint, meta.ring)}>
                    <meta.icon className="h-3 w-3 text-white" />
                  </span>
                  <div className="min-w-0 pb-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{item.title}</p>
                      <span className="shrink-0 text-[11px] text-slate-400">{formatRelative(item.time)}</span>
                    </div>
                    <p className="mt-0.5 line-clamp-2 text-xs text-slate-500 dark:text-slate-400">
                      {item.description ?? capitalize(item.type)}
                    </p>
                  </div>
                </li>
              )
            })}
          </ol>
        )}
      </div>
    </Card>
  )
}

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

export default HealthTimeline