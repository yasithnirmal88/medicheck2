import React, { useMemo } from 'react'
import type { LucideIcon } from 'lucide-react'
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'
import Card from './Card'
import { Sparkline } from './Sparkline'

type Tone = 'primary' | 'accent' | 'success' | 'warning' | 'danger'
type Trend = 'up' | 'down' | 'flat'

interface MetricCardProps {
  label: string
  value: string
  unit?: string
  trend?: Trend
  trendLabel?: string
  icon: LucideIcon
  tone?: Tone
  data?: number[]
  hint?: string
  className?: string
}

const toneStyles: Record<Tone, string> = {
  primary: 'bg-blue-100 text-blue-600 dark:bg-blue-500/15 dark:text-blue-300',
  accent: 'bg-teal-100 text-teal-600 dark:bg-teal-500/15 dark:text-teal-300',
  success: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300',
  warning: 'bg-amber-100 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300',
  danger: 'bg-red-100 text-red-600 dark:bg-red-500/15 dark:text-red-300',
}

const trendIconColor: Record<Trend, string> = {
  up: 'text-emerald-600 dark:text-emerald-400',
  down: 'text-red-500 dark:text-red-400',
  flat: 'text-slate-500 dark:text-slate-400',
}

const defaultData: Record<Tone, number[]> = {
  primary: [20, 25, 22, 30, 28, 36, 32],
  accent: [15, 18, 22, 20, 26, 24, 30],
  success: [30, 32, 38, 36, 42, 40, 46],
  warning: [40, 38, 42, 36, 40, 34, 38],
  danger: [45, 42, 46, 40, 44, 38, 42],
}

function TrendBadge({ trend, label }: { trend: Trend; label?: string }) {
  const Icon = trend === 'up' ? ArrowUpRight : trend === 'down' ? ArrowDownRight : Minus
  return (
    <span className={cn('inline-flex items-center gap-0.5 text-xs font-semibold', trendIconColor[trend])}>
      <Icon className="h-3.5 w-3.5" />
      {label ?? (trend === 'flat' ? 'stable' : 'vs last')}
    </span>
  )
}

const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  trend,
  trendLabel,
  icon: Icon,
  tone = 'primary',
  data,
  hint,
  className,
}) => {
  const sparklineData = useMemo(() => data ?? defaultData[tone], [data, tone])

  return (
    <Card interactive className={cn('group', className)}>
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-sm font-medium text-slate-500 dark:text-slate-400">{label}</span>
        <span className={cn('flex h-9 w-9 shrink-0 items-center justify-center rounded-xl', toneStyles[tone])}>
          <Icon className="h-5 w-5" />
        </span>
      </div>

      <div className="mt-4 flex items-baseline gap-1.5">
        <span className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{value}</span>
        {unit ? <span className="text-sm text-slate-400 dark:text-slate-500">{unit}</span> : null}
      </div>

      {trend ? (
        <div className="mt-1.5">
          <TrendBadge trend={trend} label={trendLabel} />
        </div>
      ) : null}

      {sparklineData.length ? (
        <div className="mt-4 h-10">
          <Sparkline data={sparklineData} tone={tone} />
        </div>
      ) : null}

      {hint ? <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">{hint}</p> : null}
    </Card>
  )
}

export default React.memo(MetricCard)