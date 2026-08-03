import { cn } from '@/lib/utils'
import type { AssessmentStatus } from '../types'

const STATUS_CONFIG: Record<AssessmentStatus, { label: string; className: string }> = {
  not_started: { label: 'Not Started', className: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300' },
  in_progress: { label: 'In Progress', className: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300' },
  completed: { label: 'Completed', className: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300' },
  recommended: { label: 'Recommended', className: 'bg-fuchsia-50 text-fuchsia-700 dark:bg-fuchsia-950/40 dark:text-fuchsia-300' },
  locked: { label: 'Locked', className: 'bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-400' },
  requires_profile: { label: 'Requires Profile', className: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300' },
  expired: { label: 'Expired', className: 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300' },
  needs_review: { label: 'Needs Review', className: 'bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300' },
}

export const StatusChip = ({ status }: { status: AssessmentStatus }) => {
  const cfg = STATUS_CONFIG[status]
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-medium',
        cfg.className,
      )}
    >
      {cfg.label}
    </span>
  )
}
