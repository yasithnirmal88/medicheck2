/**
 * Phase 11 — AI SDG narratives + human review queue page.
 *
 * Renders AI-generated SDG narratives over DE-IDENTIFIED, k-anonymity-
 * suppressed aggregate metrics, plus the human review queue for AI-generated
 * insights (equity, SDG narratives, operational suggestions). AI never
 * self-publishes — only a human reviewer may approve/reject/edit/publish.
 */
import React, { useState } from 'react'
import { FileText, Info, Globe2 } from 'lucide-react'
import {
  useSdgNarratives,
  useSdgNarrativeList,
  useOperationalSuggestions,
  useReviewOperationalSuggestion,
  usePublishOperationalSuggestion,
  useReviewPopulationInsight,
  usePublishPopulationInsight,
} from '../hooks/useAiGovernanceQueries'
import {
  SectionCard,
  TransparencyNotice,
  ErrorState,
  LoadingState,
  EmptyState,
  PrivacyBadge,
  QualityBadge,
  ReviewStatusBadge,
} from '../components/AiGovernanceUI'
import type { ReviewAction } from '../api/aiGovernanceService'

const ReviewActions: React.FC<{
  insightId: string
  kind: 'operational' | 'population'
  status: string
}> = ({ insightId, kind, status }) => {
  const [comment, setComment] = useState('')
  const [edited, setEdited] = useState('')
  const [action, setAction] = useState<ReviewAction>('approve')
  const reviewOp = useReviewOperationalSuggestion()
  const publishOp = usePublishOperationalSuggestion()
  const reviewPop = useReviewPopulationInsight()
  const publishPop = usePublishPopulationInsight()

  const canReview = status === 'pending_review'
  const canPublish = status === 'approved' || status === 'edited'

  const onReview = () => {
    const req = {
      action,
      reviewer_comment: comment || undefined,
      edited_output: action === 'edit' ? edited : undefined,
    }
    if (kind === 'operational') {
      reviewOp.mutate({ suggestionId: insightId, req })
    } else {
      reviewPop.mutate({ insightId, req })
    }
  }
  const onPublish = () => {
    if (kind === 'operational') publishOp.mutate(insightId)
    else publishPop.mutate(insightId)
  }

  if (!canReview && !canPublish) return null

  return (
    <div className="mt-2 space-y-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 p-3">
      {canReview && (
        <>
          <div className="flex flex-wrap items-center gap-2">
            {(['approve', 'reject', 'edit'] as ReviewAction[]).map((a) => (
              <button
                key={a}
                type="button"
                onClick={() => setAction(a)}
                className={`rounded px-3 py-1 text-xs font-medium ${
                  action === a
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-slate-600 dark:bg-slate-800 dark:text-slate-300'
                }`}
              >
                {a}
              </button>
            ))}
          </div>
          {action === 'edit' && (
            <textarea
              className="w-full rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-sm text-slate-700 dark:text-slate-300"
              rows={2}
              placeholder="Edited output text (required for edit)"
              value={edited}
              onChange={(e) => setEdited(e.target.value)}
              data-testid="edit-output"
            />
          )}
          <input
            className="w-full rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-sm text-slate-700 dark:text-slate-300"
            placeholder="Reviewer comment (optional)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <button
            type="button"
            onClick={onReview}
            disabled={action === 'edit' && !edited.trim()}
            className="rounded-lg bg-slate-700 px-3 py-1 text-xs font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            data-testid="submit-review-btn"
          >
            Submit review
          </button>
        </>
      )}
      {canPublish && (
        <button
          type="button"
          onClick={onPublish}
          className="rounded-lg bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700"
          data-testid="publish-btn"
        >
          Publish
        </button>
      )}
    </div>
  )
}

export const SdgNarrativesPage: React.FC = () => {
  const narratives = useSdgNarratives()
  const sdgHistory = useSdgNarrativeList()
  const opHistory = useOperationalSuggestions()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          SDG Narratives & AI Review Queue
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          AI-generated SDG narratives over de-identified aggregates, plus the
          human review workflow.
        </p>
      </div>

      <TransparencyNotice>
        AI-generated SDG narratives describe supplied aggregate metrics only and
        require human review. They do not prove an SDG target has been achieved
        and are not official UN SDG indicators.
      </TransparencyNotice>

      <div className="flex items-center gap-3 text-xs text-slate-400">
        <PrivacyBadge />
        <span className="inline-flex items-center gap-1">
          <Globe2 className="h-3.5 w-3.5" /> de-identified aggregate only
        </span>
      </div>

      {/* SDG narratives */}
      {narratives.isPending && <LoadingState />}
      {narratives.isError && (
        <ErrorState message="Could not load SDG narratives. Researcher or admin role required." />
      )}
      {narratives.data && (
        <>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <QualityBadge status={narratives.data.quality_status} />
            <span className="inline-flex items-center gap-1">
              <Info className="h-3.5 w-3.5" /> provider: {narratives.data.provider}
            </span>
            <span>· prompt v{narratives.data.prompt_version}</span>
          </div>

          {!narratives.data.available && (
            <EmptyState
              message={narratives.data.quality_reason ?? 'No narratives available.'}
            />
          )}

          {narratives.data.available &&
            narratives.data.narratives.map((n, i) => (
              <SectionCard
                key={i}
                title={`SDG ${n.target} Narrative`}
                disclaimer={n.reporting_period ?? undefined}
                badge={
                  <span className="text-xs text-slate-400">
                    {n.requires_human_review ? 'review required' : 'reviewed'}
                  </span>
                }
              >
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Population scope: {n.population_scope}
                </p>
                {n.observed_trends.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {n.observed_trends.map((t, j) => (
                      <li
                        key={j}
                        className="text-sm text-slate-700 dark:text-slate-300"
                      >
                        • {t}
                      </li>
                    ))}
                  </ul>
                )}
                <p className="mt-3 text-sm text-slate-700 dark:text-slate-300">
                  {n.possible_operational_interpretation}
                </p>
                <p className="mt-2 text-xs italic text-slate-400">{n.limitations}</p>
              </SectionCard>
            ))}

          <p className="text-xs italic text-slate-400">
            {narratives.data.transparency_notice}
          </p>
        </>
      )}

      {/* Review queue — SDG / equity insights */}
      <SectionCard
        title="Review Queue — Population Insights"
        badge={
          <span className="inline-flex items-center gap-1 text-xs text-slate-400">
            <FileText className="h-3.5 w-3.5" />
            {sdgHistory.data?.length ?? 0} item(s)
          </span>
        }
        disclaimer="AI never self-publishes — only a human reviewer may approve/reject/edit/publish."
      >
        {sdgHistory.isPending && <LoadingState />}
        {sdgHistory.isError && (
          <ErrorState message="Could not load review queue." />
        )}
        {sdgHistory.data && sdgHistory.data.length === 0 && (
          <EmptyState message="No population insights pending review." />
        )}
        {sdgHistory.data && sdgHistory.data.length > 0 && (
          <div className="space-y-3">
            {sdgHistory.data.map((r) => (
              <div
                key={r.id}
                className="rounded-lg border border-slate-100 dark:border-slate-800 p-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-slate-400">
                    {r.insight_type} · target {r.target ?? 'n/a'}
                  </span>
                  <ReviewStatusBadge status={r.review_status} />
                </div>
                <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">
                  {r.edited_output ?? r.narrative}
                </p>
                <ReviewActions
                  insightId={r.id}
                  kind="population"
                  status={r.review_status}
                />
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      {/* Review queue — operational suggestions */}
      <SectionCard title="Review Queue — Operational Suggestions">
        {opHistory.isPending && <LoadingState />}
        {opHistory.isError && (
          <ErrorState message="Could not load operational suggestions." />
        )}
        {opHistory.data && opHistory.data.length === 0 && (
          <EmptyState message="No operational suggestions pending review." />
        )}
        {opHistory.data && opHistory.data.length > 0 && (
          <div className="space-y-3">
            {opHistory.data.map((r) => (
              <div
                key={r.id}
                className="rounded-lg border border-slate-100 dark:border-slate-800 p-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-slate-400">
                    task {r.task_id.slice(0, 8)}
                  </span>
                  <ReviewStatusBadge status={r.review_status} />
                </div>
                <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">
                  {r.edited_output ?? r.explanation}
                </p>
                <ReviewActions
                  insightId={r.id}
                  kind="operational"
                  status={r.review_status}
                />
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  )
}

export default SdgNarrativesPage
