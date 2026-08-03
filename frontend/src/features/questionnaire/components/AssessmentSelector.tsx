import React from 'react'
import { Clock, Play } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AssessmentCatalogEntry } from '../data/assessments'
import { difficultyVariant } from '../data/assessments'
import type { QuestionnaireTemplate } from '../types'

type AssessmentCardProps = {
  entry: AssessmentCatalogEntry
  template?: QuestionnaireTemplate
  onStart: (code: string, templateId?: string) => void
  delay?: number
}

const colorClasses: Record<AssessmentCatalogEntry['color'], { bg: string; border: string; text: string; icon: string }> = {
  indigo: { bg: 'bg-indigo-50 dark:bg-indigo-900/20', border: 'border-indigo-200 dark:border-indigo-800', text: 'text-indigo-700 dark:text-indigo-300', icon: 'text-indigo-500 dark:text-indigo-400' },
  blue: { bg: 'bg-blue-50 dark:bg-blue-900/20', border: 'border-blue-200 dark:border-blue-800', text: 'text-blue-700 dark:text-blue-300', icon: 'text-blue-500 dark:text-blue-400' },
  rose: { bg: 'bg-rose-50 dark:bg-rose-900/20', border: 'border-rose-200 dark:border-rose-800', text: 'text-rose-700 dark:text-rose-300', icon: 'text-rose-500 dark:text-rose-400' },
  amber: { bg: 'bg-amber-50 dark:bg-amber-900/20', border: 'border-amber-200 dark:border-amber-800', text: 'text-amber-700 dark:text-amber-300', icon: 'text-amber-500 dark:text-amber-400' },
  emerald: { bg: 'bg-emerald-50 dark:bg-emerald-900/20', border: 'border-emerald-200 dark:border-emerald-800', text: 'text-emerald-700 dark:text-emerald-300', icon: 'text-emerald-500 dark:text-emerald-400' },
  violet: { bg: 'bg-violet-50 dark:bg-violet-900/20', border: 'border-violet-200 dark:border-violet-800', text: 'text-violet-700 dark:text-violet-300', icon: 'text-violet-500 dark:text-violet-400' },
  teal: { bg: 'bg-teal-50 dark:bg-teal-900/20', border: 'border-teal-200 dark:border-teal-800', text: 'text-teal-700 dark:text-teal-300', icon: 'text-teal-500 dark:text-teal-400' },
  cyan: { bg: 'bg-cyan-50 dark:bg-cyan-900/20', border: 'border-cyan-200 dark:border-cyan-800', text: 'text-cyan-700 dark:text-cyan-300', icon: 'text-cyan-500 dark:text-cyan-400' },
  fuchsia: { bg: 'bg-fuchsia-50 dark:bg-fuchsia-900/20', border: 'border-fuchsia-200 dark:border-fuchsia-800', text: 'text-fuchsia-700 dark:text-fuchsia-300', icon: 'text-fuchsia-500 dark:text-fuchsia-400' },
}

const AssessmentCard: React.FC<AssessmentCardProps> = ({ entry, template, onStart, delay = 0 }) => {
  const c = colorClasses[entry.color]
  const diff = difficultyVariant[entry.difficulty]
  const available = template?.is_active ?? true

  return (
    <div
      className={cn(
        'group relative flex flex-col rounded-2xl border bg-white shadow-sm transition-all duration-300',
        'hover:shadow-xl hover:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60',
        'dark:bg-slate-800',
        c.border,
        !available && 'opacity-60',
      )}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className={cn('rounded-t-2xl p-5', c.bg)}>
        <div className="flex items-start justify-between">
          <span className={cn('rounded-xl bg-white/60 p-2', c.icon, 'dark:bg-slate-800/60')}>
            {React.createElement(entry.bodySystems[0]?.icon ?? Clock, { className: 'h-6 w-6' })}
          </span>
          <span
            className={cn(
              'rounded-full px-2.5 py-0.5 text-xs font-semibold',
              diff.bg,
              diff.color,
            )}
          >
            {entry.difficulty}
          </span>
        </div>
        <h3 className="mt-3 text-xl font-bold text-gray-900 dark:text-gray-100">{entry.title}</h3>
        <p className="mt-1 line-clamp-2 text-sm text-gray-600 dark:text-gray-300">{entry.description}</p>
      </div>

      <div className="flex flex-col gap-3 p-5 pt-4">
        <div className="grid grid-cols-2 gap-y-3 gap-x-2 text-sm">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-gray-400 dark:text-gray-400" aria-hidden="true" />
            <span className="text-gray-600 dark:text-gray-300">{entry.estimatedTime} min</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400">Questions:</span>
            <span className="font-medium text-gray-800 dark:text-gray-200">{entry.questions}</span>
          </div>
          <div className="flex items-center gap-2">
            <SparkleIcon className="h-4 w-4 text-yellow-400" aria-hidden="true" />
            <span className="font-medium text-gray-800 dark:text-gray-200">AI Score: {entry.aiScore}%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400">Body systems:</span>
            <span className="font-medium text-gray-800 dark:text-gray-200">{entry.bodySystems.length}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {entry.bodySystems.map((sys) => (
            <span
              key={sys.name}
              className={cn(
                'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs',
                'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
              )}
              title={sys.name}
            >
              {React.createElement(sys.icon, { className: 'h-3 w-3' })}
              {sys.name}
            </span>
          ))}
        </div>

        <button
          type="button"
          disabled={!available}
          onClick={() => onStart(entry.code, template?.id)}
          className={cn(
            'mt-1 inline-flex items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold text-white',
            'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60',
            available ? 'bg-indigo-600 hover:bg-indigo-700' : 'cursor-not-allowed bg-gray-400',
          )}
        >
          <Play className="h-4 w-4" aria-hidden="true" />
          Start Assessment
        </button>
      </div>
    </div>
  )
}

const SparkleIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
    <path d="M12 2l2.9 6.9h6.9l-5.5 4.6 1.7 6.8-5.5-3.6-5.5 3.6 1.7-6.8z" />
  </svg>
)

export default AssessmentCard
