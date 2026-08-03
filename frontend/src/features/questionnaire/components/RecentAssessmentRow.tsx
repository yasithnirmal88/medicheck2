import React from 'react'
import { CheckCircle2, Clock, PauseCircle, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AssessmentSession, QuestionnaireTemplate } from '../types'

const SESSION_ICON: Record<AssessmentSession['status'], React.FC<React.SVGProps<SVGSVGElement>>> = {
  in_progress: Clock,
  paused: PauseCircle,
  completed: CheckCircle2,
  cancelled: XCircle,
}
const SESSION_LABEL: Record<AssessmentSession['status'], string> = {
  in_progress: 'In Progress',
  paused: 'Paused',
  completed: 'Completed',
  cancelled: 'Cancelled',
}
const SESSION_COLOR: Record<AssessmentSession['status'], string> = {
  in_progress: 'text-yellow-600',
  paused: 'text-orange-600',
  completed: 'text-green-600',
  cancelled: 'text-red-600',
}
const SESSION_BG: Record<AssessmentSession['status'], string> = {
  in_progress: 'bg-yellow-100 dark:bg-yellow-900/30',
  paused: 'bg-orange-100 dark:bg-orange-900/30',
  completed: 'bg-green-100 dark:bg-green-900/30',
  cancelled: 'bg-red-100 dark:bg-red-900/30',
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })

export type RecentRowProps = {
  session: AssessmentSession
  template?: QuestionnaireTemplate
  onOpen: (sessionId: string) => void
}

const RecentAssessmentRow: React.FC<RecentRowProps> = ({ session, template, onOpen }) => {
  const Icon = SESSION_ICON[session.status]
  const pct = session.progress?.completion_percentage ?? 0
  return (
    <li className="group flex items-center justify-between gap-3 rounded-lg border border-gray-200 bg-white p-3 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:bg-slate-800 dark:hover:bg-slate-700">
      <div className="flex min-w-0 items-center gap-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400">
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <p className="font-medium text-gray-900 dark:text-gray-100">{template?.name ?? session.questionnaire_template_id}</p>
          <div className="mt-0.5 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            <span>{formatDate(session.updated_at)}</span>
            <span aria-hidden="true">·</span>
            <span
              className={cn(
                'inline-flex items-center gap-1 rounded-full px-1.5 py-0.25 text-xs font-medium',
                SESSION_BG[session.status],
                SESSION_COLOR[session.status],
              )}
            >
              <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: 'currentColor' }} aria-hidden="true" />
              {SESSION_LABEL[session.status]}
            </span>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3" aria-label={`Completion ${pct}%`}>
        <div className="hidden min-[420px]:block">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{pct}%</span>
            <div className="relative h-2 w-20 min-w-[4rem] overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className={cn('h-full rounded-full', pct < 30 ? 'bg-red-500' : pct < 60 ? 'bg-yellow-500' : 'bg-green-500')}
                style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
                aria-hidden="true"
              />
              <span className="sr-only">{`completion ${pct}%`}</span>
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => onOpen(session.id)}
          className={cn(
            'rounded-lg border border-transparent bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white',
            'opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60',
          )}
        >
          {session.status === 'in_progress' ? 'Resume' : 'View'}
        </button>
      </div>
    </li>
  )
}

export default React.memo(RecentAssessmentRow)
