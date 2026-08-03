import React from 'react'
import { cn } from '@/lib/utils'

type SkeletonProps = { className?: string }

export const Skeleton: React.FC<SkeletonProps> = ({ className }) => (
  <div
    className={cn(
      'animate-pulse rounded-md bg-slate-200/80 dark:bg-slate-700/60',
      className,
    )}
  />
)

export const MetricCardSkeleton: React.FC = () => (
  <div className="rounded-2xl border border-slate-200/80 bg-white p-5 dark:border-slate-700/60 dark:bg-slate-800/70">
    <div className="flex items-center justify-between">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-8 rounded-full" />
    </div>
    <Skeleton className="mt-4 h-8 w-16" />
    <Skeleton className="mt-2 h-3 w-28" />
<div className="mt-4 flex h-12 items-end gap-1">
      {['h-5', 'h-8', 'h-6', 'h-10', 'h-7', 'h-11', 'h-9'].map((h, i) => (
        <div key={i} className={cn('flex-1 rounded-sm bg-slate-200/80 dark:bg-slate-700/60', h)} />
      ))}
    </div>
  </div>
)

export const PanelSkeleton: React.FC = () => (
  <div className="space-y-3">
    <Skeleton className="h-4 w-40" />
    <Skeleton className="h-20 w-full" />
    <Skeleton className="h-20 w-full" />
    <Skeleton className="h-20 w-full" />
  </div>
)

export const TableRowSkeleton: React.FC<{ rows?: number }> = ({ rows = 4 }) => (
  <div className="space-y-3">
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex items-center justify-between gap-4">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-5 w-20 rounded-full" />
      </div>
    ))}
  </div>
)