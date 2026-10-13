/**
 * Phase 11 — AI-assisted CHW operational suggestions page.
 *
 * Renders AI-generated operational suggestions for the signed-in CHW's
 * follow-up queue. Suggestions use ONLY operational factors (referral age,
 * overdue, contact attempts, facility/communication status). The AI NEVER
 * ranks by clinical urgency, severity, or disease probability — clinical
 * priority remains determined by the deterministic clinical workflow.
 */
import React from 'react'
import { ClipboardList, Clock, AlertTriangle, Info, Sparkles } from 'lucide-react'
import { useGenerateOperationalSuggestions, useOperationalSuggestions } from '../hooks/useAiGovernanceQueries'
import {
  SectionCard,
  TransparencyNotice,
  ErrorState,
  LoadingState,
  EmptyState,
  QualityBadge,
} from '../components/AiGovernanceUI'

const SuggestionRow: React.FC<{
  taskId: string
  reasonCodes: string[]
  explanation: string
  score: number
}> = ({ reasonCodes, explanation, score }) => (
  <div className="border-t border-slate-100 dark:border-slate-800 py-3">
    <div className="flex flex-wrap items-center gap-2">
      {reasonCodes.map((c) => (
        <span
          key={c}
          className="inline-flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400"
        >
          <AlertTriangle className="h-3 w-3" /> {c.replace(/_/g, ' ')}
        </span>
      ))}
      <span className="text-xs text-slate-400">· priority {score.toFixed(2)}</span>
    </div>
    <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">{explanation}</p>
  </div>
)

export const ChwSuggestionsPage: React.FC = () => {
  const list = useOperationalSuggestions()
  const generate = useGenerateOperationalSuggestions()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          AI Operational Suggestions
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          AI-assisted administrative task ranking for your follow-up queue.
        </p>
      </div>

      <TransparencyNotice>
        AI suggestions are administrative assistance only. They do not determine
        clinical priority, urgency, severity, or diagnosis. Clinical priority
        remains determined by the deterministic clinical workflow.
      </TransparencyNotice>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => generate.mutate()}
          disabled={generate.isPending}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          data-testid="generate-suggestions-btn"
        >
          <Sparkles className="h-4 w-4" />
          {generate.isPending ? 'Generating...' : 'Generate suggestions'}
        </button>
        {generate.data && (
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <QualityBadge status={generate.data.quality_status} />
            <span className="inline-flex items-center gap-1">
              <Info className="h-3.5 w-3.5" /> provider: {generate.data.provider}
            </span>
            <span>· prompt v{generate.data.prompt_version}</span>
          </div>
        )}
      </div>

      {generate.isError && (
        <ErrorState message="Could not generate suggestions. CHW role required." />
      )}

      {generate.data && !generate.data.available && (
        <EmptyState
          message={generate.data.quality_reason ?? 'No suggestions available.'}
        />
      )}

      {generate.data && generate.data.available && generate.data.suggestions.length > 0 && (
        <SectionCard
          title="Suggested Tasks"
          badge={
            <span className="inline-flex items-center gap-1 text-xs text-slate-400">
              <ClipboardList className="h-3.5 w-3.5" />
              {generate.data.suggestions.length} suggestion(s)
            </span>
          }
        >
          {generate.data.suggestions.map((s) => (
            <SuggestionRow
              key={s.task_id}
              taskId={s.task_id}
              reasonCodes={s.operational_reason_codes}
              explanation={s.explanation}
              score={s.operational_priority_score}
            />
          ))}
        </SectionCard>
      )}

      {generate.data && (
        <p className="text-xs italic text-slate-400">
          {generate.data.transparency_notice}
        </p>
      )}

      {/* Persisted suggestion history (own only) */}
      <SectionCard title="Suggestion History" disclaimer="Your persisted suggestions and their review status.">
        {list.isPending && <LoadingState />}
        {list.isError && (
          <ErrorState message="Could not load suggestion history." />
        )}
        {list.data && list.data.length === 0 && (
          <EmptyState message="No suggestions generated yet." />
        )}
        {list.data && list.data.length > 0 && (
          <div className="space-y-2">
            {list.data.map((r) => (
              <div
                key={r.id}
                className="rounded-lg border border-slate-100 dark:border-slate-800 p-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-slate-400">
                    <Clock className="inline h-3 w-3" /> task {r.task_id.slice(0, 8)}
                  </span>
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                    {r.review_status.replace(/_/g, ' ')}
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">
                  {r.edited_output ?? r.explanation}
                </p>
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  )
}

export default ChwSuggestionsPage
