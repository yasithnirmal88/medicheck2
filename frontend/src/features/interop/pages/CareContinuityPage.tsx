/**
 * Phase 10 — Care-continuity dashboard.
 *
 * Renders the screening → referral → care funnel, conversion / drop-off
 * rates, median time-to-care, and CHW-assisted completion. All outputs are
 * de-identified and small-cell-suppressed.
 */
import React from 'react'
import { useCareContinuity } from '../hooks/useInteropQueries'
import {
  SectionCard,
  TransparencyNotice,
  PrivacyBadge,
  MetricCard,
  ErrorState,
  LoadingState,
  SuppressedBadge,
} from '../components/InteropUI'

const STAGE_ORDER = [
  'screened',
  'flagged',
  'referred',
  'referral_received',
  'appointment_scheduled',
  'care_received',
  'followup_completed',
] as const

const FunnelBar: React.FC<{
  stage: string
  count: number
  suppressed: boolean
  max: number
}> = ({ stage, count, suppressed, max }) => {
  const width = suppressed ? 0 : max > 0 ? Math.max((count / max) * 100, 2) : 0
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="w-44 text-sm capitalize text-slate-600 dark:text-slate-400">
        {stage.replace(/_/g, ' ')}
      </span>
      <div className="flex-1 h-7 bg-slate-100 dark:bg-slate-800 rounded overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded transition-all"
          style={{ width: `${width}%` }}
        />
      </div>
      <span className="w-20 text-right text-sm font-medium text-slate-900 dark:text-white">
        {suppressed ? <SuppressedBadge /> : count.toLocaleString()}
      </span>
    </div>
  )
}

export const CareContinuityPage: React.FC = () => {
  const care = useCareContinuity()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Care Continuity
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Referral funnel, completion rates, and time-to-care analytics.
        </p>
      </div>

      <TransparencyNotice>
        This information is aggregated and de-identified for health-system and
        research purposes. Outcome data does not alter clinical scores or
        condition probabilities.
      </TransparencyNotice>

      {care.isPending && <LoadingState />}
      {care.isError && (
        <ErrorState message="Could not load care-continuity analytics." />
      )}
      {care.data && (
        <>
          <div className="flex items-center gap-2">
            <PrivacyBadge threshold={care.data.privacy_threshold} />
          </div>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetricCard
              label="Referral completion"
              value={care.data.metrics.referral_completion_rate}
              suffix="%"
            />
            <MetricCard
              label="Follow-up completion"
              value={care.data.metrics.followup_completion_rate}
              suffix="%"
            />
            <MetricCard
              label="Drop-off rate"
              value={care.data.metrics.drop_off_rate}
              suffix="%"
            />
            <MetricCard
              label="Median time-to-care"
              value={care.data.metrics.median_time_to_care_days}
              suffix=" days"
            />
          </div>

          <SectionCard
            title="Care-Continuity Funnel"
            disclaimer="Screened → Flagged → Referred → Received → Appointment → Care received → Follow-up."
          >
            {(() => {
              const byStage = new Map(
                care.data.funnel.map((s) => [s.stage, s])
              )
              const max = Math.max(
                ...STAGE_ORDER.map((s) => byStage.get(s)?.count ?? 0),
                1
              )
              return STAGE_ORDER.map((stage) => {
                const s = byStage.get(stage)
                return (
                  <FunnelBar
                    key={stage}
                    stage={stage}
                    count={s?.count ?? 0}
                    suppressed={s?.suppressed ?? false}
                    max={max}
                  />
                )
              })
            })()}
          </SectionCard>

          <SectionCard title="Outcome Summary">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <MetricCard label="Screened" value={care.data.metrics.screened} />
              <MetricCard label="Referred" value={care.data.metrics.referred} />
              <MetricCard
                label="Care received"
                value={care.data.metrics.care_received}
              />
              <MetricCard
                label="Lost to follow-up"
                value={care.data.metrics.lost_to_followup}
              />
            </div>
          </SectionCard>

          <SectionCard
            title="CHW-Assisted Completion"
            disclaimer="CHW-assisted assessment + follow-up completion (SDG 3.8 access dimension)."
          >
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <MetricCard
                label="CHW-assisted completion"
                value={care.data.metrics.chw_assisted_completion_rate}
                suffix="%"
              />
              <MetricCard
                label="Appointment scheduled"
                value={care.data.metrics.appointment_scheduled}
              />
              <MetricCard
                label="Referral received"
                value={care.data.metrics.referral_received}
              />
            </div>
          </SectionCard>
        </>
      )}
    </div>
  )
}

export default CareContinuityPage
