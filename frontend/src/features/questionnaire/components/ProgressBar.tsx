import React from 'react'
import { cn } from '@/lib/utils'

interface ProgressBarProps {
  current: number
  total: number
  percentage: number
}

const colorFor = (pct: number): string => {
  if (pct < 30) return 'bg-red-500'
  if (pct < 60) return 'bg-yellow-500'
  return 'bg-green-500'
}

const ProgressBar: React.FC<ProgressBarProps> = ({ current, total, percentage }) => {
  const clamped = Math.min(100, Math.max(0, percentage))
  const barColor = colorFor(clamped)

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-500">
          Q{current} of {total}
        </span>
        <span className={cn('text-xs font-medium', colorFor(clamped).replace('bg-', 'text-'))}>
          {Math.round(clamped)}%
        </span>
      </div>
      <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all duration-500 ease-out', barColor)}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  )
}

export default React.memo(ProgressBar)
