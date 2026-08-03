import Card from '@/shared/ui/Card'
import { cn } from '@/lib/utils'
import { ArrowRight, Bot, FileText, Target } from 'lucide-react'
import { motion } from 'framer-motion'
import type { AIPriority } from '../types'
import { AssessmentBadge } from './AssessmentCard'
import { recommendationInsight } from '../mockData'

export const RecommendationCard = () => {
  const priorityColor: Record<AIPriority, string> = {
    low: 'bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300',
    medium: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300',
    high: 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300',
  }
  return (
    <Card
      className={cn(
        'relative overflow-hidden border border-slate-200/80 bg-white',
        'dark:border-slate-700/60 dark:bg-slate-800/70',
      )}
    >
      <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full blur-3xl opacity-15 bg-gradient-to-br" />
      <div className="relative p-5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-indigo-600" />
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">AI Recommendation</span>
          </div>
          <span
            className={cn(
              'inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium capitalize',
              priorityColor[recommendationInsight.priority],
            )}
          >
            {recommendationInsight.priority} Priority
          </span>
        </div>

        <div className={cn('mt-3 flex items-start gap-3')}>
          <div
            className={cn(
              'mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg',
              'bg-gradient-to-br',
              recommendationInsight.gradient,
              'text-white shadow-md shadow-black/5',
            )}
          >
            <Target className="h-4 w-4" />
          </div>
          <div>
            <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {recommendationInsight.title}
            </p>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{recommendationInsight.reason}</p>
            <p className="mt-2 text-sm text-gray-700 dark:text-gray-200">
              Estimated risk reduction: <span className="font-medium text-emerald-600">{recommendationInsight.riskReduction}</span>
            </p>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              Suggested completion: {recommendationInsight.suggestedDate}
            </p>
          </div>
        </div>

        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.98 }}
          className={cn(
            'mt-4 w-full rounded-xl px-4 py-2 text-sm font-medium text-white shadow-sm shadow-black/5',
            'bg-gradient-to-r from-indigo-500 to-teal-500',
            'hover:brightness-110',
          )}
        >
          <span className="inline-flex items-center justify-center gap-1.5">
            Start Now
            <ArrowRight className="h-4 w-4" />
          </span>
        </motion.button>
      </div>
    </Card>
  )
}
