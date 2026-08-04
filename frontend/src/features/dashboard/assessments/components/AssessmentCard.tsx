import { cn } from '@/lib/utils'
import type { AssessmentDef } from '../types'
import { StatusChip } from './StatusChip'
import { DifficultyIndicator } from './DifficultyIndicator'
import { Award, Bot, Clock, Edit3, PlayCircle, RefreshCw, Trash2 } from 'lucide-react'
import { motion } from 'framer-motion'

export const AssessmentBadge = ({ aiEnabled }: { aiEnabled: boolean }) => (
  <span
    className={cn(
      'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium',
      aiEnabled ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
    )}
  >
    {aiEnabled ? <Bot className="h-3 w-3" /> : <Award className="h-3 w-3" />}
    {aiEnabled ? 'AI' : 'Standard'}
  </span>
)

const STATUS_ACTION: Record<AssessmentDef['status'], { label: string; variant: 'primary' | 'ghost' | 'danger' }> = {
  not_started: { label: 'Start Assessment', variant: 'primary' },
  in_progress: { label: 'Resume', variant: 'primary' },
  completed: { label: 'Review Report', variant: 'ghost' },
  recommended: { label: 'Start Recommended', variant: 'primary' },
  locked: { label: 'Locked', variant: 'ghost' },
  requires_profile: { label: 'Complete Profile', variant: 'primary' },
  expired: { label: 'Retake', variant: 'primary' },
  needs_review: { label: 'Review Answers', variant: 'primary' },
}

export const AssessmentCard = ({
  assessment,
  onPrimary,
  onEdit,
  onDiscard,
  compact = false,
}: {
  assessment: AssessmentDef
  onPrimary?: () => void
  onEdit?: () => void
  onDiscard?: () => void
  compact?: boolean
}) => {
  const action = STATUS_ACTION[assessment.status]
  const iconMap: Record<string, JSX.Element> = {
    'clipboard-text': <Award className="h-5 w-5" />,
    heart: <Award className="h-5 w-5 text-rose-500" />,
    kidney: <Award className="h-5 w-5 text-teal-500" />,
  }
  const Icon = iconMap[assessment.icon] ?? <Award className="h-5 w-5" />

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.28, ease: 'easeOut' }}
      className="group"
    >
      <div
        className={cn(
          'relative flex h-full flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm',
          'dark:border-slate-700/60 dark:bg-slate-800/70',
          'transition-shadow duration-200 group-hover:shadow-md',
          assessment.status === 'completed' && 'border-emerald-200/80 dark:border-emerald-900/40',
          assessment.status === 'in_progress' && 'border-indigo-200/80 dark:border-indigo-900/40',
        )}
      >
        <div className={cn('absolute inset-x-0 top-0 h-1.5', `bg-gradient-to-r ${assessment.gradient}`)} />
        <div className="overflow-hidden p-5 pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br',
                  assessment.gradient,
                  'text-white shadow-md shadow-black/5',
                )}
              >
                {Icon}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{assessment.title}</h3>
                <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
                  {assessment.description}
                </p>
              </div>
            </div>
            <StatusChip status={assessment.status} />
          </div>
        </div>

        <div className={cn('px-5 pb-4', compact ? 'pb-3 pt-2' : 'pb-4')}>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs text-gray-600 dark:text-gray-300">
            <div className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              <span>{assessment.durationMinutes} min</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Edit3 className="h-3.5 w-3.5" />
              <span>{assessment.questionsCount} questions</span>
            </div>
            <div>
              <DifficultyIndicator difficulty={assessment.difficulty} />
            </div>
            <div className="flex items-center gap-1.5">
              <span className="truncate">
                {assessment.bodySystems.map((b) => b.name).join(', ')}
              </span>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between">
            <AssessmentBadge aiEnabled={assessment.aiEnabled} />
            {assessment.status === 'in_progress' && assessment.progressPct !== undefined && (
              <span className="text-xs font-medium text-indigo-600">{assessment.progressPct}% complete</span>
            )}
            {assessment.status === 'completed' && assessment.healthScore !== undefined && (
              <span className="text-xs font-medium text-emerald-600">{assessment.healthScore} health score</span>
            )}
          </div>
        </div>

        <div className="mt-auto flex items-center gap-2 border-t border-slate-200/80 px-5 py-3 dark:border-slate-700/60">
          {action.label === 'Resume' && <RefreshCw className="h-3.5 w-3.5 text-indigo-500" />}
          {action.label === 'Start Assessment' && <PlayCircle className="h-3.5 w-3.5 text-indigo-500" />}
          {onEdit && (
            <button
              type="button"
              onClick={onEdit}
              className="ml-auto rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800"
              aria-label={`Edit ${assessment.title}`}
            >
              <Edit3 className="h-4 w-4" />
            </button>
          )}
          {onDiscard && assessment.status === 'in_progress' && (
            <button
              type="button"
              onClick={onDiscard}
              className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40"
              aria-label={`Discard ${assessment.title}`}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
          <button
            type="button"
            onClick={onPrimary}
            disabled={assessment.status === 'locked'}
            className={cn(
              'ml-2 rounded-lg px-3.5 py-1.5 text-xs font-medium text-white shadow-sm shadow-black/5 transition-opacity',
              'bg-gradient-to-r',
              assessment.gradient,
              'hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60',
            )}
          >
            {action.label}
          </button>
        </div>
      </div>
    </motion.div>
  )
}
