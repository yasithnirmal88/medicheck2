import React, { useEffect, useMemo, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  FlaskConical,
  HeartPulse,
  Info,
  LifeBuoy,
  NotebookText,
  ShieldAlert,
  TrendingUp,
} from 'lucide-react'
import Card from '@/shared/ui/Card'
import Button from '@/shared/ui/Button'
import Alert from '@/shared/ui/Alert'
import { fetchReportBySession, generateReport } from '@/features/dashboard/api/patientService'
import { DEMO_HEALTH_REPORT, isResultsDemoMode } from '../demo/resultsDemoData'
import type {
  ReportBodySystem,
  ReportDetail,
} from '../types/report'

// ---------------------------------------------------------------------------
// Real-data helpers. These only FORMAT values that come from the report API;
// they never invent clinical numbers.
// ---------------------------------------------------------------------------

const CATEGORY_ORDER = [
  'Normal',
  'Monitor',
  'Needs Attention',
  'Recommend Screening',
  'Urgent Medical Review',
]

const CATEGORY_BADGE: Record<string, string> = {
  normal: 'bg-emerald-100 text-emerald-700',
  monitor: 'bg-amber-100 text-amber-700',
  'needs attention': 'bg-orange-100 text-orange-700',
  'recommend screening': 'bg-rose-100 text-rose-700',
  'urgent medical review': 'bg-red-100 text-red-700',
}

const ID_PREFIX = /^(bs|cond|condition|rec|recommendation|ind|indicator|q|qg)[_-]/i

function humanizeId(id?: string | null): string {
  if (!id) return 'Unknown'
  return id
    .replace(ID_PREFIX, '')
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .trim()
}

function scoreText(value?: string | null): string | null {
  if (value == null || value === '') return null
  const n = Number(value)
  return Number.isFinite(n)
    ? n.toLocaleString(undefined, { maximumFractionDigits: 2 })
    : value
}

function categoryBadgeClass(category?: string | null): string {
  return (
    CATEGORY_BADGE[(category ?? '').trim().toLowerCase()] ??
    'bg-slate-100 text-slate-600'
  )
}

function highestCategory(systems: ReportBodySystem[]): string | null {
  let bestIdx = -1
  let best: string | null = null
  for (const s of systems) {
    const idx = CATEGORY_ORDER.findIndex(
      (c) => c.toLowerCase() === (s.category ?? '').trim().toLowerCase(),
    )
    if (idx > bestIdx) {
      bestIdx = idx
      best = s.category ?? null
    }
  }
  return best
}

function extractLifestyle(report?: ReportDetail): string | null {
  const raw = report?.lifestyle?.[0]?.data
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>
    const value = parsed?.lifestyle
    if (typeof value === 'string' && value.trim() !== '') return value
  } catch {
    return null
  }
  return null
}

function httpStatus(error: unknown): number | undefined {
  if (error && typeof error === 'object' && 'response' in error) {
    return (error as { response?: { status?: number } }).response?.status
  }
  return undefined
}

// ---------------------------------------------------------------------------
// State UI (same patterns as InteropUI / ReportExplanation).
// ---------------------------------------------------------------------------

const PageEmpty: React.FC<{ title: string; message: string }> = ({ title, message }) => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <Info className="mb-2 h-6 w-6 text-slate-400" aria-hidden />
    <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{title}</p>
    <p className="mt-1 max-w-md text-sm text-slate-500 dark:text-slate-400">{message}</p>
  </div>
)

const PageError: React.FC<{ onRetry: () => void }> = ({ onRetry }) => (
  <div className="space-y-3">
    <Alert variant="error" title="We couldn't load this report" live>
      The assessment report could not be retrieved, so no results are shown.
      Please try again.
    </Alert>
    <Button variant="ghost" onClick={onRetry}>
      Try again
    </Button>
  </div>
)

const LoadingSkeleton: React.FC = () => (
  <div className="animate-pulse space-y-4">
    <div className="h-6 w-48 rounded bg-gray-200 dark:bg-gray-700" />
    <Card>
      <div className="space-y-4 p-2">
        <div className="h-4 w-3/4 rounded bg-gray-200 dark:bg-gray-700" />
        <div className="h-4 w-1/2 rounded bg-gray-200 dark:bg-gray-700" />
      </div>
    </Card>
  </div>
)

const StatTile: React.FC<{ label: string; value: number }> = ({ label, value }) => (
  <div className="rounded-md border border-gray-200 p-3 dark:border-gray-700">
    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{label}</p>
  </div>
)

const Badge: React.FC<{ category?: string | null }> = ({ category }) =>
  category ? (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${categoryBadgeClass(category)}`}
    >
      {category}
    </span>
  ) : null

// ---------------------------------------------------------------------------
// Page.
// ---------------------------------------------------------------------------

const ResultsDashboard: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const demoMode = useMemo(() => isResultsDemoMode(), [])
  const attemptedGeneration = useRef(false)
  const qc = useQueryClient()

  const query = useQuery<ReportDetail>({
    queryKey: ['health-report', id],
    queryFn: () => fetchReportBySession(id!),
    enabled: !!id,
    staleTime: 30_000,
    retry: false,
  })

  const generate = useMutation({
    mutationFn: (sid: string) => generateReport(sid),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ['health-report', id] }),
  })
  const runGenerate = generate.mutate

  const report: ReportDetail | undefined =
    query.data ?? (demoMode ? DEMO_HEALTH_REPORT : undefined)
  const usingDemo = demoMode && query.data === undefined

  const isLoading = query.isLoading || generate.isPending

  const systems = useMemo(() => report?.body_systems ?? [], [report])
  const conditions = useMemo(() => report?.conditions ?? [], [report])
  const advices = useMemo(() => report?.advices ?? [], [report])
  const lifestyle = useMemo(() => extractLifestyle(report), [report])
  const overallCategory = useMemo(() => highestCategory(systems), [systems])
  const hasFindings =
    systems.length > 0 || conditions.length > 0 || advices.length > 0

  // A report is generated on demand when the deterministic engine has not
  // produced one yet. Never runs in demo mode (demo data must not touch the API).
  useEffect(() => {
    if (!id || demoMode) return
    if (query.data !== undefined || isLoading) return
    if (!query.isError || attemptedGeneration.current) return
    attemptedGeneration.current = true
    runGenerate(id)
  }, [id, demoMode, query.data, isLoading, query.isError, runGenerate])

  if (!id && !demoMode) {
    return (
      <div className="mx-auto max-w-4xl p-4">
        <PageEmpty
          title="No assessment selected"
          message="Open an assessment result from your history to see its report."
        />
      </div>
    )
  }

  if (isLoading && !usingDemo) {
    return (
      <div className="mx-auto max-w-4xl p-4">
        <LoadingSkeleton />
      </div>
    )
  }

  if (query.isError && !usingDemo) {
    const status = httpStatus(query.error)
    if (status === 404 || status === 400) {
      return (
        <div className="mx-auto max-w-4xl p-4">
          <PageEmpty
            title="No report available yet"
            message="This assessment doesn't have a clinical report yet. Complete the assessment first, then return here to view your results."
          />
        </div>
      )
    }
    return (
      <div className="mx-auto max-w-4xl p-4">
        <PageError onRetry={() => query.refetch()} />
      </div>
    )
  }

  if (!report) {
    return (
      <div className="mx-auto max-w-4xl p-4">
        <PageEmpty
          title="No report available"
          message="We couldn't find a clinical report for this assessment."
        />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      {usingDemo ? (
        <Alert variant="warning" title="Demo data – not real clinical results" live>
          This page is showing sample data for demonstration only. It is not a
          real assessment and must not be used for any clinical decision.
        </Alert>
      ) : null}

      <header className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-indigo-600" />
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Assessment Results
          </h1>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Generated from {usingDemo ? 'a demo session' : 'session'}{' '}
          <span className="font-medium">{usingDemo ? 'demo-session' : id}</span>
        </p>
      </header>

      {!hasFindings ? (
        <Card>
          <PageEmpty
            title="No clinical findings"
            message="The engine recorded no body-system, condition, or recommendation findings for this assessment."
          />
        </Card>
      ) : (
        <>
          {/* Overview — counts derived from the real report only. */}
          <Card>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                Overview
              </h2>
              {overallCategory ? <Badge category={overallCategory} /> : null}
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <StatTile label="Body systems assessed" value={systems.length} />
              <StatTile label="Possible conditions" value={conditions.length} />
              <StatTile label="Recommendations" value={advices.length} />
            </div>
          </Card>

          {/* Body System Assessments — real category + score. */}
          {systems.length > 0 ? (
            <Card>
              <div className="mb-3 flex items-center gap-2">
                <HeartPulse className="h-4 w-4 text-indigo-600" />
                <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  Body System Assessments
                </h2>
              </div>
              <div className="space-y-3">
                {systems.map((s) => {
                  const score = scoreText(s.score)
                  return (
                    <div
                      key={s.id}
                      className="flex items-center justify-between gap-3 rounded-md border border-gray-200 p-3 dark:border-gray-700"
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                          {humanizeId(s.body_system_id)}
                        </p>
                        {s.notes ? (
                          <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                            {s.notes}
                          </p>
                        ) : null}
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        {score ? (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            Score {score}
                          </span>
                        ) : null}
                        <Badge category={s.category} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </Card>
          ) : null}

          {/* Condition Assessments — real condition + confidence. */}
          {conditions.length > 0 ? (
            <Card>
              <div className="mb-3 flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-rose-600" />
                <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  Possible Conditions
                </h2>
              </div>
              <div className="space-y-3">
                {conditions.map((c) => {
                  const score = scoreText(c.score)
                  return (
                    <div
                      key={c.id}
                      className="flex items-center justify-between gap-3 rounded-md border border-gray-200 p-3 dark:border-gray-700"
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                          {humanizeId(c.condition_id)}
                        </p>
                        {c.notes ? (
                          <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                            {c.notes}
                          </p>
                        ) : null}
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        {score ? (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            Score {score}
                          </span>
                        ) : null}
                        {c.confidence ? (
                          <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                            {c.confidence}
                          </span>
                        ) : null}
                      </div>
                    </div>
                  )
                })}
              </div>
            </Card>
          ) : null}

          {/* Recommendations — real generated advice. */}
          {advices.length > 0 ? (
            <Card>
              <div className="mb-3 flex items-center gap-2">
                <LifeBuoy className="h-4 w-4 text-indigo-600" />
                <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  Recommendations
                </h2>
              </div>
              <div className="space-y-3">
                {advices.map((a) => (
                  <div
                    key={a.id}
                    className="rounded-md border border-gray-200 p-3 dark:border-gray-700"
                  >
                    {a.category ? (
                      <span className="text-xs font-medium uppercase text-gray-500 dark:text-gray-400">
                        {a.category}
                      </span>
                    ) : null}
                    <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">
                      {a.text ?? 'No recommendation text provided.'}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          ) : null}

          {/* Lifestyle snapshot — only rendered when the real report contains one. */}
          {lifestyle ? (
            <Card>
              <div className="mb-3 flex items-center gap-2">
                <NotebookText className="h-4 w-4 text-indigo-600" />
                <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  Lifestyle Snapshot
                </h2>
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300">{lifestyle}</p>
            </Card>
          ) : null}
        </>
      )}

      <div className="flex items-start gap-2 pt-1">
        <FlaskConical className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" aria-hidden />
        <p className="text-xs text-gray-500 dark:text-gray-400">
          These values are produced by the deterministic MediCheck clinical
          engine from your assessment. This is not a diagnosis. If you have
          urgent symptoms, contact a healthcare professional.
        </p>
      </div>
    </div>
  )
}

export default ResultsDashboard
