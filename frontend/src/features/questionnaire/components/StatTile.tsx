import React from 'react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

type StatTileProps = {
  icon: LucideIcon
  label: string
  value: string | number
  trend?: 'up' | 'down' | 'flat'
  className?: string
}

const TrendIcon: React.FC<{ trend: NonNullable<StatTileProps['trend']> }> = ({ trend }) => {
  if (trend === 'up') {
    return (
      <svg className="h-3 w-3 text-green-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
        <line x1={12} y1={19} x2={12} y2={5} />
        <polyline points="5 12 12 5 19 12" />
      </svg>
    )
  }
  if (trend === 'down') {
    return (
      <svg className="h-3 w-3 text-red-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
        <line x1={12} y1={5} x2={12} y2={19} />
        <polyline points="5 12 12 19 19 12" />
      </svg>
    )
  }
  return null
}

const StatTile: React.FC<StatTileProps> = ({ icon, label, value, trend, className }) => {
  const Icon = icon
  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-xl border bg-white p-4 shadow-sm transition-transform duration-200',
        'hover:translate-y-0.5 dark:bg-slate-800 dark:border-gray-700',
        className,
      )}
    >
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium tracking-wide uppercase text-gray-500 dark:text-gray-400">
          {label}
        </p>
        <div className="flex items-center gap-1.5">
          <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</span>
          {trend ? <TrendIcon trend={trend} /> : null}
        </div>
      </div>
    </div>
  )
}

export default React.memo(StatTile)
