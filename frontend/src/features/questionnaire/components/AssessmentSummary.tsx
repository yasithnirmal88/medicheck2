import { memo } from 'react'
import { cn } from '@/lib/utils'
import Card from '@/shared/ui/Card'
import type useQuestionnaireFlow from '../hooks/useQuestionnaireFlow'

type FlowReturn = ReturnType<typeof useQuestionnaireFlow>
type FlowSlice = Pick<
  FlowReturn,
  'answered' | 'skipped' | 'totalQuestions' | 'bodySystemsCovered' | 'estimatedTimeRemaining' | 'progress'
>

function formatEta(seconds: number | null): string {
  if (seconds == null || Number.isNaN(seconds)) return 'Calculating...'
  if (seconds <= 0) return 'Almost done!'
  if (seconds < 60) return `${Math.round(seconds)}s left`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m ${s > 0 ? s + 's' : ''} left`
}

function StatusBadge({
  label,
  color,
}: {
  label: string
  color: 'emerald' | 'amber' | 'rose'
}) {
  const palette = {
    emerald: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-700',
    rose: 'bg-rose-100 text-rose-700',
  }[color]
  return (
    <span
      className={cn(
        'inline-block rounded-full px-2 py-0.5 text-[10px] font-medium leading-tight',
        palette,
      )}
    >
      {label}
    </span>
  )
}

function ProgressBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, value))
  const color =
    pct < 50 ? 'bg-indigo-500' : pct < 85 ? 'bg-amber-500' : 'bg-emerald-500'
  return (
    <div className="relative h-1.5 w-10 flex-1 overflow-hidden rounded-sm bg-gray-200 dark:bg-gray-700">
      <div className={cn('h-full transition-[width] duration-300', color)} style={{ width: `${pct}%` }} />
    </div>
  )
}

export const AssessmentSummary = memo(
  ({
    flow: {
      answered,
      skipped,
      totalQuestions,
      bodySystemsCovered,
      estimatedTimeRemaining,
      progress,
    },
  }: {
    flow: FlowSlice
  }) => {
    const answeredAndSkipped = answered + skipped
    const remaining = Math.max((totalQuestions ?? 0) - answeredAndSkipped, 0)
    const completion = progress?.completion_percentage ?? 0
    const answeredRatio = totalQuestions > 0 ? answered / totalQuestions : 0

    let quality: 'high' | 'medium' | 'low'
    let qualityLabel: string
    if (answeredRatio >= 0.9) {
      quality = 'high'
      qualityLabel = 'High'
    } else if (answeredRatio >= 0.6) {
      quality = 'medium'
      qualityLabel = 'Good'
    } else {
      quality = 'low'
      qualityLabel = 'Needs attention'
    }
    const qualityColor: 'emerald' | 'amber' | 'rose' =
      quality === 'high' ? 'emerald' : quality === 'medium' ? 'amber' : 'rose'

    return (
      <Card>
        <div className="grid grid-cols-2 gap-y-3 px-1 text-xs">
          <div className="flex flex-col">
            <span className="text-muted-foreground">Questions completed</span>
            <span className="font-medium text-foreground">
              {answeredAndSkipped}
              {totalQuestions ? ` / ${totalQuestions}` : ''}
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-muted-foreground">Remaining</span>
            <span className="font-medium text-foreground">{remaining}</span>
          </div>

          <div className="flex flex-col">
            <span className="text-muted-foreground">Body systems covered</span>
            <span className="font-medium text-foreground">
              {bodySystemsCovered.length}
              {bodySystemsCovered.length > 0
                ? ` (${bodySystemsCovered.join(', ')})`
                : ' —'}
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-muted-foreground">Completion</span>
            <div className="mt-0.5 flex items-center gap-1.5">
              <ProgressBar value={completion} />
              <span className="font-medium text-foreground">{completion}%</span>
            </div>
          </div>

          <div className="flex flex-col">
            <span className="text-muted-foreground">Estimated time left</span>
            <span className="font-medium text-foreground">
              {formatEta(estimatedTimeRemaining)}
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-muted-foreground">Assessment quality</span>
            <StatusBadge label={qualityLabel} color={qualityColor} />
          </div>
        </div>
      </Card>
    )
  },
)
AssessmentSummary.displayName = 'AssessmentSummary'
