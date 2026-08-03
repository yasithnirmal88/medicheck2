import React from 'react'
import { Check, Clock, PauseCircle, Play } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { QuestionnaireTemplate } from '../types'
import ProgressBar from './ProgressBar'

type AssessmentCardProps = {
  template: QuestionnaireTemplate
  status?: 'available' | 'in_progress' | 'paused' | 'completed'
  progress?: { current: number; total: number; percentage: number }
  lastTaken?: string
  onStart: (id: string) => void
}

const CalendarIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" {...props}>
    <rect x={3} y={4} width={18} height={18} rx={2} />
    <line x1={16} y1={2} x2={16} y2={6} />
    <line x1={8} y1={2} x2={8} y2={6} />
  </svg>
)

const statusConfig = {
  available: { icon: Play, label: 'Not started', color: 'text-blue-600' },
  in_progress: { icon: Clock, label: 'In progress', color: 'text-yellow-600' },
  paused: { icon: PauseCircle, label: 'Paused', color: 'text-orange-600' },
  completed: { icon: Check, label: 'Completed', color: 'text-green-600' },
}

const AssessmentCard: React.FC<AssessmentCardProps> = ({
  template,
  status = 'available',
  progress,
  lastTaken,
  onStart,
}) => {
  const cfg = statusConfig[status]
  const Icon = cfg.icon

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ') onStart(template.id)
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`Start ${template.name} assessment`}
      onClick={() => onStart(template.id)}
      onKeyDown={handleKeyDown}
      className={cn(
        'group flex flex-col rounded-xl border bg-white shadow-sm transition-all duration-200',
        'hover:shadow-md hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60',
        'dark:bg-slate-800 dark:border-gray-700',
        status === 'completed' && 'bg-gray-50 dark:bg-gray-800/60',
      )}
    >
      <div className="flex items-start gap-3 p-4">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 group-hover:text-blue-700 dark:group-hover:text-blue-400">
            {template.name}
          </h3>
          {template.description && (
            <p className="mt-0.5 line-clamp-2 text-sm text-gray-500 dark:text-gray-400">
              {template.description}
            </p>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700 dark:bg-gray-700 dark:text-gray-300">
              <span className="sr-only">{cfg.label}</span>
              <cfg.icon className="h-3 w-3" aria-hidden="true" />
              {cfg.label}
            </span>
            {template.estimated_time_minutes && (
              <span className="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                <Clock className="h-3 w-3" aria-hidden="true" />
                {template.estimated_time_minutes} min
              </span>
            )}
            {lastTaken && (
              <span className="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                <CalendarIcon className="h-3 w-3" aria-hidden="true" />
                Last taken {lastTaken}
              </span>
            )}
          </div>
        </div>
      </div>

      {progress && (
        <div className="px-4 pb-2">
          <ProgressBar current={progress.current} total={progress.total} percentage={progress.percentage} />
        </div>
      )}

      <div className="mt-auto p-4 pt-2">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onStart(template.id)
          }}
          className={cn(
            'w-full rounded-lg border border-transparent bg-indigo-600 py-2 px-4 text-sm font-semibold text-white',
            'transition-colors hover:bg-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60',
          )}
        >
          {status === 'in_progress' ? 'Resume' : status === 'completed' ? 'Review' : 'Start Assessment'}
        </button>
      </div>
    </div>
  )
}

export default React.memo(AssessmentCard)
