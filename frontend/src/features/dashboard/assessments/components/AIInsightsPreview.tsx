import Card from '@/shared/ui/Card'
import { cn } from '@/lib/utils'
import { AlertTriangle, Bot, ChevronUp, TrendingUp, TrendingDown } from 'lucide-react'
import type { AIInsight } from '../types'
import { aiInsight } from '../mockData'

export const AIInsightsPreview = ({ insight }: { insight?: AIInsight }) => {
  const data = insight ?? aiInsight
  const trendColor =
    data.riskTrend === 'improving'
      ? 'text-emerald-500'
      : data.riskTrend === 'declining'
        ? 'text-rose-500'
        : 'text-amber-500'
  const TrendIcon = data.riskTrend === 'improving' ? TrendingUp : data.riskTrend === 'declining' ? TrendingDown : ChevronUp
  return (
    <Card
      className={cn(
        'border border-slate-200/80 bg-white/70 backdrop-blur-sm',
        'dark:border-slate-700/60 dark:bg-slate-800/60',
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-indigo-600" />
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">AI Insights Preview</h3>
        </div>
        <span className="text-xs text-gray-500">Updated {data.lastAIUpdate}</span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-center">
        <div className="rounded-xl bg-slate-50 dark:bg-slate-800/70 p-3">
          <p className="text-xs text-gray-500 dark:text-gray-400">Current Health Score</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">{data.currentHealthScore}</p>
        </div>
        <div className="rounded-xl bg-slate-50 dark:bg-slate-800/70 p-3">
          <p className="text-xs text-gray-500 dark:text-gray-400">Assessment Confidence</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">{data.confidence}%</p>
        </div>
        <div className="rounded-xl bg-slate-50 dark:bg-slate-800/70 p-3">
          <p className="text-xs text-gray-500 dark:text-gray-400">Risk Trend</p>
          <div className="mt-1 flex items-center justify-center gap-1">
            <TrendIcon className={`h-4 w-4 ${trendColor}`} />
            <span className={cn('text-sm font-medium capitalize', trendColor)}>{data.riskTrend}</span>
          </div>
        </div>
      </div>

      <div className="mt-3 space-y-2.5 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-gray-600 dark:text-gray-300">Most improved body system</span>
          <span className="font-medium text-gray-900 dark:text-gray-100">{data.mostImproved}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-300">
            <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />
            Highest risk area
          </span>
          <span className="font-medium text-rose-600">{data.highestRisk}</span>
        </div>
      </div>
    </Card>
  )
}
