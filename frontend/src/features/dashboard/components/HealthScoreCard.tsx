import React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import Card from './Card'

interface HealthScoreCardProps {
  score: number | null
  loading?: boolean
}

function toneOf(score: number): { color: string; label: string; track: string } {
  if (score >= 80) return { color: '#10B981', label: 'Excellent', track: 'text-emerald-500' }
  if (score >= 60) return { color: '#2563EB', label: 'Good', track: 'text-blue-600' }
  if (score >= 40) return { color: '#F59E0B', label: 'Moderate', track: 'text-amber-500' }
  return { color: '#EF4444', label: 'Needs attention', track: 'text-red-500' }
}

export const HealthScoreCard: React.FC<HealthScoreCardProps> = ({ score, loading }) => {
  const value = score ?? 0
  const tone = toneOf(value)
  const radius = 52
  const circumference = 2 * Math.PI * radius

  return (
    <Card className="flex h-full flex-col">
      <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Health Score</h3>
      <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">Overall risk-adjusted wellbeing</p>

      <div className="relative mx-auto mt-4 flex h-40 w-40 items-center justify-center">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r={radius} fill="none" strokeWidth="10" className="stroke-slate-100 dark:stroke-slate-700" />
          {!loading && score !== null ? (
            <motion.circle
              cx="60"
              cy="60"
              r={radius}
              fill="none"
              stroke={tone.color}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: circumference * (1 - value / 100) }}
              transition={{ duration: 1, ease: 'easeOut' }}
            />
          ) : null}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn('text-4xl font-bold', tone.track)}>{loading ? '—' : `${value}`}</span>
          <span className="text-[11px] font-medium uppercase tracking-wide text-slate-400">/ 100</span>
        </div>
      </div>

      {score !== null ? (
        <div className="mt-2 text-center">
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{tone.label}</span>
        </div>
      ) : null}
    </Card>
  )
}

export default HealthScoreCard