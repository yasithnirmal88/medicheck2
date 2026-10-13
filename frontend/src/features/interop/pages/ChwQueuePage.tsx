/**
 * Phase 10 — AI-assisted CHW operational queue.
 *
 * Renders the ranked operational task queue for the signed-in CHW. Ranking
 * uses ONLY operational factors (referral age, overdue, missing follow-up,
 * geographic grouping). The AI NEVER ranks by clinical urgency, severity,
 * or disease probability.
 */
import React from 'react'
import { ClipboardList, Clock, AlertTriangle, Info } from 'lucide-react'
import { useChwQueue } from '../hooks/useInteropQueries'
import {
  SectionCard,
  TransparencyNotice,
  ErrorState,
  LoadingState,
  EmptyState,
} from '../components/InteropUI'

const QueueRow: React.FC<{
  rank: number
  rationale: string
  referralAgeDays: number
  overdue: boolean
  missingFollowUp: boolean
  score: number
}> = ({ rank, rationale, referralAgeDays, overdue, missingFollowUp, score }) => (
  <div className="border-t border-slate-100 dark:border-slate-800 py-3">
    <div className="flex items-start gap-3">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">
        {rank}
      </span>
      <div className="flex-1">
        <div className="flex flex-wrap items-center gap-2">
          {overdue && (
            <span className="inline-flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
              <AlertTriangle className="h-3 w-3" /> Overdue
            </span>
          )}
          {missingFollowUp && (
            <span className="inline-flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
              <Clock className="h-3 w-3" /> Missing follow-up
            </span>
          )}
          <span className="inline-flex items-center gap-1 text-xs text-slate-400">
            <Clock className="h-3 w-3" /> {referralAgeDays}d old
          </span>
          <span className="text-xs text-slate-400">· score {score.toFixed(1)}</span>
        </div>
        <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">{rationale}</p>
      </div>
    </div>
  </div>
)

export const ChwQueuePage: React.FC = () => {
  const queue = useChwQueue()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          CHW Task Queue
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          AI-assisted operational task ranking.
        </p>
      </div>

      <TransparencyNotice>
        AI assistance ranks tasks using operational factors only (referral age,
        overdue status, missing follow-up). It does NOT determine clinical
        urgency, severity, or disease probability. Clinical priority remains
        determined by the deterministic clinical workflow.
      </TransparencyNotice>

      {queue.isPending && <LoadingState />}
      {queue.isError && (
        <ErrorState message="Could not load the CHW queue. CHW role required." />
      )}
      {queue.data && (
        <>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="inline-flex items-center gap-1">
              <Info className="h-3.5 w-3.5" />
              Provider: {queue.data.provider}
            </span>
            <span>· prompt v{queue.data.prompt_version}</span>
            <span>· quality: {queue.data.quality_status}</span>
          </div>

          <SectionCard
            title="Ranked Tasks"
            badge={
              <span className="inline-flex items-center gap-1 text-xs text-slate-400">
                <ClipboardList className="h-3.5 w-3.5" />
                {queue.data.ranked_tasks.length} task(s)
              </span>
            }
          >
            {!queue.data.available ? (
              <EmptyState message="The CHW queue is not available right now." />
            ) : queue.data.ranked_tasks.length === 0 ? (
              <EmptyState message="No pending tasks. You're all caught up!" />
            ) : (
              queue.data.ranked_tasks.map((task) => (
                <QueueRow
                  key={task.referral_id}
                  rank={task.rank}
                  rationale={task.rationale}
                  referralAgeDays={task.referral_age_days}
                  overdue={task.overdue}
                  missingFollowUp={task.missing_follow_up}
                  score={task.score}
                />
              ))
            )}
          </SectionCard>

          <p className="text-xs italic text-slate-400">
            {queue.data.transparency_notice}
          </p>
        </>
      )}
    </div>
  )
}

export default ChwQueuePage
