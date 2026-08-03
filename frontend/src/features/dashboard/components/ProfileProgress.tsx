import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import Card from './Card'
import { Skeleton } from './LoadingSkeleton'

interface ProfileProgressProps {
  overall: number | null
  completed: number
  total: number
  loading?: boolean
}

export const ProfileProgress: React.FC<ProfileProgressProps> = ({ overall, completed, total, loading }) => {
  const pct = overall ?? 0

  return (
    <Card className="flex h-full flex-col">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Profile Completion</h3>
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-100 text-teal-600 dark:bg-teal-500/15 dark:text-teal-300">
          <User className="h-4 w-4" />
        </span>
      </div>

      <div className="mt-4 flex items-center gap-4">
        <div className="relative h-20 w-20 shrink-0">
          <svg className="h-full w-full -rotate-90" viewBox="0 0 40 40">
            <circle cx="20" cy="20" r="16" fill="none" strokeWidth="4" className="stroke-slate-100 dark:stroke-slate-700" />
            {!loading && overall !== null ? (
              <circle
                cx="20"
                cy="20"
                r="16"
                fill="none"
                stroke="#14B8A6"
                strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray={2 * Math.PI * 16}
                strokeDashoffset={2 * Math.PI * 16 * (1 - pct / 100)}
              />
            ) : null}
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-bold text-slate-800 dark:text-white">{loading ? '—' : `${pct}%`}</span>
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
            {loading ? <Skeleton className="h-4 w-24" /> : total > 0 ? `${completed} of ${total} sections completed` : 'Not started'}
          </p>
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
            <div
              className={cn('h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-500 transition-all duration-500')}
              style={{ width: `${pct}%` }}
            />
          </div>
          {loading ? null : <p className="mt-2 text-xs text-slate-400">Complete your profile for personalized insights</p>}
        </div>
      </div>

      <div className="mt-4 border-t border-slate-100 pt-4 dark:border-slate-700">
        <Link
          to="/profile"
          className={cn(
            'group flex w-full items-center justify-center gap-2 rounded-xl bg-teal-50 px-4 py-2.5 text-sm font-semibold text-teal-700',
            'transition-colors hover:bg-teal-100 dark:bg-teal-500/10 dark:text-teal-300 dark:hover:bg-teal-500/20',
          )}
        >
          Continue Profile
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </Card>
  )
}

export default ProfileProgress