import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, BrainCircuit, ShieldCheck } from 'lucide-react'
import Card from './Card'
import { Skeleton } from './LoadingSkeleton'

interface InsightCardProps {
  summary?: string
  confidence?: number | null
  nextAssessment?: string
  loading?: boolean
}

export const InsightCard: React.FC<InsightCardProps> = ({ summary, nextAssessment, loading }) => {
  const hasInsight = Boolean(summary)

  return (
    <Card className="relative flex h-full flex-col overflow-hidden">
      <div className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-blue-100/60 blur-2xl dark:bg-blue-500/10" />
      <div className="relative flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-teal-500 text-white">
          <BrainCircuit className="h-4 w-4" />
        </span>
        <div>
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">AI Health Insights</h3>
          <p className="text-[11px] text-slate-400 dark:text-slate-500">Explainable risk analysis</p>
        </div>
      </div>

      <div className="relative mt-4 flex-1">
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-4/5" />
            <Skeleton className="h-4 w-3/5" />
          </div>
        ) : hasInsight ? (
          <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">{summary}</p>
        ) : (
          <p className="text-sm text-slate-400 dark:text-slate-500">
            Complete an assessment to unlock personalized AI insights about your health.
          </p>
        )}
      </div>

      <div className="relative mt-4 space-y-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-teal-500" />
          <span className="text-xs text-slate-500 dark:text-slate-400">Explainability</span>
          <span className="ml-auto w-24">
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
              <div className="h-full w-3/4 rounded-full bg-teal-500" />
            </div>
          </span>
        </div>

        {nextAssessment ? (
          <Link
            to="/questionnaires"
            className="group flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700"
          >
            <div>
              <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">Recommended next</p>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{nextAssessment}</p>
            </div>
            <ArrowRight className="h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-0.5" />
          </Link>
        ) : null}
      </div>
    </Card>
  )
}

export default InsightCard