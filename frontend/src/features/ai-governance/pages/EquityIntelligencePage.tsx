/**
 * Phase 11 — AI equity intelligence page ("left-behind" intelligence).
 *
 * Renders AI-generated equity patterns over DE-IDENTIFIED, k-anonymity-
 * suppressed aggregate analytics. The AI never infers disease prevalence or
 * causation, and never identifies an individual. All output requires human
 * review before publication.
 */
import React from 'react'
import { Globe2, Info, ShieldCheck } from 'lucide-react'
import { useEquityInsight, useEquityInsights } from '../hooks/useAiGovernanceQueries'
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

export const EquityIntelligencePage: React.FC = () => {
  const insight = useEquityInsight()
  const history = useEquityInsights()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Equity Intelligence
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          AI-generated equity patterns over de-identified aggregate analytics.
        </p>
      </div>

      <TransparencyNotice>
        AI-generated population summaries are derived from aggregated,
        de-identified metrics and require human review. They do not infer
        disease prevalence, causation, or identify any individual.
      </TransparencyNotice>

      <div className="flex items-center gap-3 text-xs text-slate-400">
        <PrivacyBadge />
        <span className="inline-flex items-center gap-1">
          <ShieldCheck className="h-3.5 w-3.5" /> de-identified aggregate only
        </span>
      </div>

      {insight.isPending && <LoadingState />}
      {insight.isError && (
        <ErrorState message="Could not load equity insights. Researcher or admin role required." />
      )}
      {insight.data && (
        <>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <QualityBadge status={insight.data.quality_status} />
            <span className="inline-flex items-center gap-1">
              <Info className="h-3.5 w-3.5" /> provider: {insight.data.provider}
            </span>
            <span>· prompt v{insight.data.prompt_version}</span>
          </div>

          {!insight.data.available && (
            <EmptyState
              message={insight.data.quality_reason ?? 'No equity insight available.'}
            />
          )}

          {insight.data.available && insight.data.insight && (
            <SectionCard title="Observed Findings">
              {insight.data.insight.observed_findings.length === 0 ? (
                <EmptyState message="No notable equity pattern observed in the released data." />
              ) : (
                <ul className="space-y-2">
                  {insight.data.insight.observed_findings.map((f, i) => (
                    <li
                      key={i}
                      className="text-sm text-slate-700 dark:text-slate-300"
                    >
                      • {f.statement}
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>
          )}

          {insight.data.available && insight.data.insight && (
            <SectionCard title="Possible Operational Interpretations" disclaimer="Non-causal; requires human review.">
              {insight.data.insight.possible_interpretations.length === 0 ? (
                <EmptyState message="No interpretations generated." />
              ) : (
                <ul className="space-y-2">
                  {insight.data.insight.possible_interpretations.map((it, i) => (
                    <li
                      key={i}
                      className="text-sm text-slate-700 dark:text-slate-300"
                    >
                      {it.is_observed ? 'Observed: ' : 'Possible: '}
                      {it.interpretation}
                    </li>
                  ))}
                </ul>
              )}
              <p className="mt-3 text-xs italic text-slate-400">
                {insight.data.insight.limitations}
              </p>
            </SectionCard>
          )}

          {insight.data.record && (
            <SectionCard title="Insight Record" disclaimer="Review lifecycle — AI never self-publishes.">
              <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                <ReviewStatusBadge status={insight.data.record.review_status} />
                <span>insight id {insight.data.record.id.slice(0, 8)}</span>
              </div>
            </SectionCard>
          )}

          <p className="text-xs italic text-slate-400">
            {insight.data.transparency_notice}
          </p>
        </>
      )}

      {/* History */}
      <SectionCard title="Insight History" badge={<Globe2 className="h-4 w-4 text-slate-400" />}>
        {history.isPending && <LoadingState />}
        {history.isError && (
          <ErrorState message="Could not load insight history." />
        )}
        {history.data && history.data.length === 0 && (
          <EmptyState message="No equity insights generated yet." />
        )}
        {history.data && history.data.length > 0 && (
          <div className="space-y-2">
            {history.data.map((r) => (
              <div
                key={r.id}
                className="rounded-lg border border-slate-100 dark:border-slate-800 p-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-slate-400">
                    dimension: {r.target ?? 'n/a'}
                  </span>
                  <ReviewStatusBadge status={r.review_status} />
                </div>
                <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">
                  {r.edited_output ?? r.narrative}
                </p>
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  )
}

export default EquityIntelligencePage
