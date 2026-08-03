import React from 'react'
import { Link } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import { Apple, ArrowRight, Dumbbell, Footprints, HeartPulse, Leaf } from 'lucide-react'
import { cn } from '@/lib/utils'
import Card from './Card'
import EmptyState from './EmptyState'
import { Skeleton } from './LoadingSkeleton'

export type RecommendationItem = {
  id: string
  title: string
  category: 'exercise' | 'nutrition' | 'lifestyle' | 'medical'
  priority: 'low' | 'medium' | 'high'
  support?: boolean
}

interface RecommendationListProps {
  items: RecommendationItem[]
  loading?: boolean
}

const categoryMeta: Record<RecommendationItem['category'], { icon: LucideIcon; tint: string }> = {
  exercise: { icon: Dumbbell, tint: 'bg-blue-100 text-blue-600 dark:bg-blue-500/15 dark:text-blue-300' },
  nutrition: { icon: Apple, tint: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300' },
  lifestyle: { icon: Footprints, tint: 'bg-teal-100 text-teal-600 dark:bg-teal-500/15 dark:text-teal-300' },
  medical: { icon: HeartPulse, tint: 'bg-amber-100 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300' },
}

const priorityTint: Record<RecommendationItem['priority'], string> = {
  high: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300',
  medium: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300',
  low: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300',
}

export const RecommendationList: React.FC<RecommendationListProps> = ({ items, loading }) => {
  return (
    <Card className="flex h-full flex-col">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Recommendations</h3>
        <Link to="/recommendations" className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-300">
          View all
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      <div className="mt-4 flex-1 space-y-3">
        {loading ? (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <EmptyState icon={Leaf} title="No active recommendations" description="Personalized advice will appear once your profile is complete." />
        ) : (
          items.map((item) => {
            const cat = categoryMeta[item.category]
            return (
              <div
                key={item.id}
                className="rounded-xl border border-slate-200 p-3.5 transition-colors hover:border-slate-300 dark:border-slate-700 dark:hover:border-slate-600"
              >
                <div className="flex items-start gap-3">
                  <span className={cn('mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg', cat.tint)}>
                    <cat.icon className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{item.title}</p>
                      <span className={cn('shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide', priorityTint[item.priority])}>
                        {item.priority}
                      </span>
                    </div>
                    <div className="mt-1.5 flex flex-wrap items-center gap-2">
                      <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium capitalize text-slate-500 dark:bg-slate-700 dark:text-slate-300">
                        {item.category}
                      </span>
                      {item.support ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-slate-400">
                          <Leaf className="h-3 w-3" />
                          Evidence-backed
                        </span>
                      ) : null}
                    </div>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>
    </Card>
  )
}

export default RecommendationList