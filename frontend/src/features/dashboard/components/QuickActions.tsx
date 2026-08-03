import React from 'react'
import { Link } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import { ArrowUpRight, CalendarPlus, ClipboardList, Download, FlaskConical, HeartPulse, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'
import Card from './Card'

interface QuickAction {
  label: string
  to?: string
  icon: LucideIcon
  tone: string
  disabled?: boolean
}

const actions: QuickAction[] = [
  { label: 'Complete Questionnaire', to: '/questionnaires', icon: ClipboardList, tone: 'bg-blue-100 text-blue-600 dark:bg-blue-500/15 dark:text-blue-300' },
  { label: 'Upload Lab Report', to: '/profile', icon: FlaskConical, tone: 'bg-teal-100 text-teal-600 dark:bg-teal-500/15 dark:text-teal-300' },
  { label: 'View Recommendations', to: '/recommendations', icon: HeartPulse, tone: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300' },
  { label: 'Book Appointment', icon: CalendarPlus, tone: 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-400', disabled: true },
  { label: 'Download Report', to: '/assessments', icon: Download, tone: 'bg-amber-100 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300' },
]

export const QuickActions: React.FC = () => {
  return (
    <Card className="flex h-full flex-col">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Quick Actions</h3>
        <Zap className="h-4 w-4 text-slate-300 dark:text-slate-600" />
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-2">
        {actions.map((action) => {
          const inner = (
            <>
              <span className={cn('flex h-9 w-9 items-center justify-center rounded-lg', action.tone)}>
                <action.icon className="h-[18px] w-[18px]" />
              </span>
              <div className="flex items-center gap-2">
                <span className="flex-1 text-sm font-medium text-slate-700 dark:text-slate-200">{action.label}</span>
                <ArrowUpRight className="h-3.5 w-3.5 text-slate-300 dark:text-slate-600" />
              </div>
            </>
          )

          if (action.disabled || !action.to) {
            return (
              <button
                key={action.label}
                disabled
                title="Coming soon"
                className="flex flex-col gap-2 rounded-xl border border-dashed border-slate-200 p-3 text-left opacity-60 dark:border-slate-700"
              >
                {inner}
              </button>
            )
          }
          return (
            <Link
              key={action.label}
              to={action.to}
              className="group flex flex-col gap-2 rounded-xl border border-slate-200 p-3 text-left transition-colors hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-700/50"
            >
              {inner}
            </Link>
          )
        })}
      </div>
    </Card>
  )
}

export default QuickActions