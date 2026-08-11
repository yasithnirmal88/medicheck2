import React, { useMemo } from 'react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import { Link } from 'react-router-dom'
import { useTrajectory, useTrajectoryExplanation } from '../hooks/useTrajectory'
import type {
  ChangeEvent,
  HealthTrajectory,
  LongitudinalExplanation,
} from '../api/trajectoryService'
import {
  Activity,
  AlertTriangle,
  ArrowDown,
  ArrowRight,
  ArrowUp,
  Brain,
  Minus,
  ShieldAlert,
  Sparkles,
} from 'lucide-react'
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'

const trendIcon: Record<string, React.ReactNode> = {
  improving: <ArrowDown className="h-4 w-4 text-emerald-600" aria-label="improving" />,
  worsening: <ArrowUp className="h-4 w-4 text-rose-600" aria-label="worsening" />,
  stable: <Minus className="h-4 w-4 text-slate-500" aria-label="stable" />,
  new: <ArrowRight className="h-4 w-4 text-blue-600" aria-label="new" />,
  removed: <Minus className="h-4 w-4 text-slate-400" aria-label="removed" />,
  persistent: <Activity className="h-4 w-4 text-amber-600" aria-label="persistent" />,
  insufficient_data: <ShieldAlert className="h-4 w-4 text-slate-400" aria-label="insufficient data" />,
}

function fmtDate(s: string | null): string {
  if (!s) return '—'
  try {
    return new Date(s).toLocaleDateString()
  } catch {
    return s
  }
}

const trendLabel: Record<string, string> = {
  improving: 'Improved',
  worsening: 'Increased',
  stable: 'Stable',
  new: 'New',
  removed: 'No longer detected',
  persistent: 'Persistent',
}

const TrajectoryPage: React.FC = () => {
  const { data: trajectory, isLoading } = useTrajectory(20)
  const hasData = !!trajectory?.sufficient_data
  const { data: explanation } = useTrajectoryExplanation({}, hasData)

  if (isLoading) {
    return (
      <AppLayout>
        <div className="max-w-5xl mx-auto p-4">
          <h1 className="text-2xl font-semibold mb-4">Health Trajectory</h1>
          <Card><div className="text-sm text-gray-500">Loading trajectory…</div></Card>
        </div>
      </AppLayout>
    )
  }

  const empty = !trajectory || trajectory.assessments.length === 0
  if (empty) {
    return (
      <AppLayout>
        <div className="max-w-5xl mx-auto p-4">
          <h1 className="text-2xl font-semibold mb-4">Health Trajectory</h1>
          <Card>
            <div className="text-sm text-gray-500 py-6 text-center">
              Complete an assessment to begin your health timeline.
            </div>
          </Card>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto p-4 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Health Trajectory</h1>
          <Link to="/timeline" className="text-sm text-indigo-600">View timeline list</Link>
        </div>

        <Card>
          <p className="text-sm text-gray-700" data-testid="trajectory-summary">
            {trajectory?.summary}
          </p>
          {!hasData && (
            <p className="text-xs text-gray-500 mt-2">
              Your first assessment is recorded. Complete another assessment to compare changes over time.
            </p>
          )}
        </Card>

        {hasData && trajectory && (
          <>
            <TimelineSection trajectory={trajectory} />
            <TrendChart trajectory={trajectory} />
            <BodySystemCards trajectory={trajectory} />
            <FindingChanges trajectory={trajectory} />
            <AIExplanationSection explanation={explanation} />
          </>
        )}
      </div>
    </AppLayout>
  )
}

const TimelineSection: React.FC<{ trajectory: HealthTrajectory }> = ({ trajectory }) => {
  return (
    <Card>
      <h2 className="text-lg font-medium mb-3">Assessment Timeline</h2>
      <ol className="space-y-3" data-testid="trajectory-timeline">
        {trajectory.assessments.map((a) => (
          <li key={a.assessment_id} className="p-3 border rounded">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium">{fmtDate(a.completed_at)}</div>
                <div className="text-xs text-gray-500">Session: {a.session_id}</div>
              </div>
              <div className="text-right text-sm">
                {a.overall_severity && (
                  <span className="text-xs text-gray-500">Severity: {a.overall_severity}</span>
                )}
                <div className="mt-1">
                  <Link to={`/report/${a.session_id}`} className="text-indigo-600 text-sm">View report</Link>
                </div>
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-600">
              {a.body_systems.length} body system(s) · {a.activated_indicators.length} finding(s) ·{' '}
              {a.possible_conditions.length} possible condition(s)
            </div>
            {a.trace_id && (
              <div className="text-xs text-gray-400 mt-1">trace: {a.trace_id}</div>
            )}
          </li>
        ))}
      </ol>
    </Card>
  )
}

const TrendChart: React.FC<{ trajectory: HealthTrajectory }> = ({ trajectory }) => {
  // Aggregate body-system scores across assessments for the trend chart.
  // Only body systems present in >= 1 assessment are shown.
  const data = useMemo(() => {
    const byDate: { label: string; [key: string]: number | string }[] = []
    for (const a of trajectory.assessments) {
      const point: { label: string; [key: string]: number | string } = {
        label: fmtDate(a.completed_at),
      }
      for (const b of a.body_systems) {
        const key = b.name || b.body_system_id || 'Unknown'
        point[key] = b.score ?? 0
      }
      byDate.push(point)
    }
    return byDate
  }, [trajectory.assessments])

  const seriesKeys = useMemo(() => {
    const keys = new Set<string>()
    for (const a of trajectory.assessments) {
      for (const b of a.body_systems) {
        keys.add(b.name || b.body_system_id || 'Unknown')
      }
    }
    return Array.from(keys)
  }, [trajectory.assessments])

  if (data.length < 2) return null
  const colors = ['#2563EB', '#0EA5E9', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6']

  return (
    <Card>
      <h2 className="text-lg font-medium mb-3">Body System Score Trend</h2>
      <div style={{ height: 260 }} data-testid="trajectory-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 16, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            {seriesKeys.map((k, i) => (
              <Line
                key={k}
                type="monotone"
                dataKey={k}
                stroke={colors[i % colors.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Scores are deterministic body-system assessment values, not diagnoses.
      </p>
    </Card>
  )
}

const BodySystemCards: React.FC<{ trajectory: HealthTrajectory }> = ({ trajectory }) => {
  const last = trajectory.comparisons[trajectory.comparisons.length - 1]
  if (!last) return null
  return (
    <div>
      <h2 className="text-lg font-medium mb-3">Body System Changes</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="body-system-cards">
        {last.body_system_changes.map((c: ChangeEvent) => (
          <Card key={(c.ref_id || '') + (c.label || '')}>
            <div className="flex items-center justify-between">
              <div className="font-medium text-sm">{c.label || c.ref_id || 'Body system'}</div>
              {trendIcon[c.trend]}
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Previous: {c.previous_value ?? '—'} → Current: {c.current_value ?? '—'}
            </div>
            {(c.previous_score != null || c.current_score != null) && (
              <div className="text-xs text-gray-500">
                Score: {c.previous_score ?? '—'} → {c.current_score ?? '—'}
                {c.delta != null && ` (Δ ${c.delta > 0 ? '+' : ''}${c.delta})`}
              </div>
            )}
            <div className="text-xs mt-1">
              <span className="text-gray-600">Change: {trendLabel[c.trend] || c.trend}</span>
            </div>
          </Card>
        ))}
        {last.body_system_changes.length === 0 && (
          <Card><div className="text-sm text-gray-500">No body-system changes between the latest two assessments.</div></Card>
        )}
      </div>
    </div>
  )
}

const FindingChanges: React.FC<{ trajectory: HealthTrajectory }> = ({ trajectory }) => {
  const last = trajectory.comparisons[trajectory.comparisons.length - 1]
  if (!last) return null
  const sections: { title: string; items: string[]; testId: string }[] = [
    { title: 'New findings', items: last.indicator_changes.new, testId: 'new-findings' },
    { title: 'Persistent findings', items: last.indicator_changes.persistent, testId: 'persistent-findings' },
    { title: 'No longer detected', items: last.indicator_changes.resolved, testId: 'resolved-findings' },
    { title: 'New possible conditions', items: last.condition_changes.new, testId: 'new-conditions' },
    { title: 'Possible conditions no longer present', items: last.condition_changes.removed, testId: 'removed-conditions' },
    { title: 'New recommendations', items: last.recommendation_changes.new, testId: 'new-recommendations' },
  ]
  return (
    <Card>
      <h2 className="text-lg font-medium mb-3">Finding Changes</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {sections.map((s) => (
          <div key={s.testId} data-testid={s.testId}>
            <h3 className="text-sm font-medium">{s.title}</h3>
            <ul className="mt-2 list-disc list-inside text-sm">
              {s.items.length > 0 ? (
                s.items.map((id) => <li key={id}>{id}</li>)
              ) : (
                <li className="text-gray-500">None</li>
              )}
            </ul>
          </div>
        ))}
      </div>
    </Card>
  )
}

const AIExplanationSection: React.FC<{ explanation?: LongitudinalExplanation }> = ({ explanation }) => {
  return (
    <Card className="border-l-4 border-l-indigo-400">
      <div className="flex items-center gap-2 mb-3">
        <Brain className="h-5 w-5 text-indigo-600" />
        <h2 className="text-lg font-medium">AI Explanation</h2>
        <span className="text-xs px-2 py-0.5 rounded bg-indigo-50 text-indigo-700">AI-generated</span>
      </div>

      {!explanation || !explanation.available ? (
        <div className="text-sm text-gray-600" data-testid="ai-unavailable">
          <p>AI explanation is currently unavailable.</p>
          <p className="text-xs text-gray-500 mt-1">
            Your assessment history and deterministic results remain available.
          </p>
        </div>
      ) : (
        <div className="space-y-3" data-testid="ai-explanation">
          <p className="text-sm text-gray-700">{explanation.summary}</p>

          {explanation.key_changes.length > 0 && (
            <div>
              <h3 className="text-sm font-medium flex items-center gap-1"><Sparkles className="h-4 w-4" /> Key changes</h3>
              <ul className="mt-1 space-y-1 text-sm">
                {explanation.key_changes.map((f, i) => (
                  <li key={i} className="text-gray-700">{f.explanation}</li>
                ))}
              </ul>
            </div>
          )}

          {explanation.important_context.length > 0 && (
            <div className="text-xs text-gray-600 bg-gray-50 rounded p-2">
              {explanation.important_context.map((c, i) => <p key={i}>{c}</p>)}
            </div>
          )}

          {explanation.evidence_available && explanation.retrieved_evidence.length > 0 && (
            <div data-testid="ai-evidence">
              <h3 className="text-sm font-medium">Supporting evidence</h3>
              <ul className="mt-1 text-xs text-gray-600 list-disc list-inside">
                {explanation.retrieved_evidence.map((e) => (
                  <li key={e.id}>
                    {e.title}
                    {e.evidence_level && ` (level ${e.evidence_level})`}
                    {e.source && ` — ${e.source}`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="mt-3 flex items-start gap-2 text-xs text-gray-500 border-t pt-2">
        <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
        <p data-testid="ai-disclaimer">
          AI-generated explanations summarize changes in your assessment history.
          They do not diagnose conditions or replace professional medical advice.
        </p>
      </div>
    </Card>
  )
}

export default TrajectoryPage
