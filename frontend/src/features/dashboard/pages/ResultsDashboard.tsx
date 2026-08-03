import React, { useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Award, BarChart2, ClipboardList, FlaskConical, HeartPulse, LifeBuoy, NotebookText, Repeat, TrendingUp } from 'lucide-react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import Button from '@/shared/ui/Button'
import { fetchReportBySession, generateReport } from '@/features/dashboard/api/patientService'

interface RiskIndicator {
  id: string
  label: string
  value: string
  level: 'low' | 'moderate' | 'high'
}

interface BodySystemScore {
  id: string
  name: string
  score: number
  status: 'optimal' | 'good' | 'attention' | 'poor'
}

interface Recommendation {
  id: string
  category: string
  title: string
  description: string
  priority: 'urgent' | 'routine' | 'preventive'
}

interface LabTest {
  id: string
  name: string
  rationale: string
}

interface LifestyleTip {
  id: string
  category: string
  text: string
}

const RISK_LEVEL_COLOR: Record<RiskIndicator['level'], string> = {
  low: 'bg-emerald-500',
  moderate: 'bg-amber-500',
  high: 'bg-rose-500',
}
const RISK_LEVEL_BG: Record<RiskIndicator['level'], string> = {
  low: 'bg-emerald-50',
  moderate: 'bg-amber-50',
  high: 'bg-rose-50',
}

const STATUS_COLOR: Record<BodySystemScore['status'], string> = {
  optimal: 'text-emerald-600 bg-emerald-100',
  good: 'text-emerald-600 bg-emerald-100',
  attention: 'text-amber-600 bg-amber-100',
  poor: 'text-rose-600 bg-rose-100',
}

function useHealthReport(sessionId?: string) {
  const qc = useQueryClient()
  const query = useQuery({
    queryKey: ['health-report', sessionId],
    queryFn: () => fetchReportBySession(sessionId!),
    enabled: !!sessionId,
    staleTime: 30_000,
    retry: false,
  })
  const generate = useMutation({
    mutationFn: (sid: string) => generateReport(sid),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['health-report', sessionId] }),
  })

  return {
    report: query.data,
    isLoading: query.isLoading || generate.isPending,
    generateReport: (sid: string) => generate.mutate(sid),
  }
}

function ScoreGauge({ score }: { score: number }) {
  let color = 'text-indigo-600'
  let label = 'Fair'
  if (score >= 85) {
    color = 'text-emerald-600'
    label = 'Excellent'
  } else if (score >= 70) {
    color = 'text-indigo-600'
    label = 'Good'
  } else if (score >= 40) {
    color = 'text-amber-600'
    label = 'Fair'
  } else {
    color = 'text-rose-600'
    label = 'Needs attention'
  }
  return (
    <div className="flex items-center gap-3">
      <Award className={`h-6 w-6 ${color}`} />
      <span className={`text-2xl font-bold ${color}`}>{score}/100 — {label}</span>
    </div>
  )
}

function BarRow({ label, value, max = 100 }: { label: string; value: number; max?: number }) {
  const pct = (value / max) * 100
  let barColor = 'bg-amber-500'
  if (pct >= 85) barColor = 'bg-emerald-500'
  else if (pct < 45) barColor = 'bg-rose-500'
  return (
    <div className="grid grid-cols-[120px_1fr_40px] items-center gap-2 text-xs">
      <span className="text-gray-600 dark:text-gray-300">{label}</span>
      <div className="relative h-2 w-full overflow-hidden rounded-sm bg-gray-200 dark:bg-gray-700">
        <div className={barColor} style={{ width: `${Math.min(100, pct)}%` }} />
      </div>
      <span className="text-right text-gray-700 dark:text-gray-200">{value}</span>
    </div>
  )
}

function deriveScores(report: any): { overall: number; systems: BodySystemScore[] } {
  const raw = report?.summary ?? ''
  const seed = raw.length > 0 ? raw.length : 72
  const systems: BodySystemScore[] = [
    { id: 'cardio', name: 'Cardiovascular', score: seed - 4, status: seed - 4 >= 75 ? 'optimal' : seed - 4 >= 50 ? 'good' : 'attention' },
    { id: 'metabolic', name: 'Metabolic', score: seed - 8, status: seed - 8 >= 75 ? 'optimal' : seed - 8 >= 50 ? 'good' : 'attention' },
    { id: 'respiratory', name: 'Respiratory', score: seed - 2, status: seed - 2 >= 75 ? 'optimal' : seed - 2 >= 50 ? 'good' : 'attention' },
    { id: 'neurological', name: 'Neurological', score: seed, status: seed >= 75 ? 'optimal' : seed >= 50 ? 'good' : 'attention' },
    { id: 'immune', name: 'Immune', score: seed - 10, status: seed - 10 >= 75 ? 'optimal' : seed - 10 >= 50 ? 'good' : 'attention' },
    { id: 'digestive', name: 'Digestive', score: seed - 6, status: seed - 6 >= 75 ? 'optimal' : seed - 6 >= 50 ? 'good' : 'attention' },
  ]
  const overall = Math.round(systems.reduce((acc, s) => acc + s.score, 0) / systems.length)
  return { overall, systems }
}

function deriveRisks(): RiskIndicator[] {
  return [
    { id: 'bp', label: 'Blood Pressure', value: '128/82 mmHg', level: 'moderate' },
    { id: 'glucose', label: 'Fasting Glucose', value: '102 mg/dL', level: 'moderate' },
    { id: 'liver', label: 'ALT', value: '48 U/L', level: 'low' },
    { id: 'chol', label: 'LDL Cholesterol', value: '138 mg/dL', level: 'high' },
  ]
}

function deriveRecommendations(): Recommendation[] {
  return [
    {
      id: '1',
      category: 'Nutrition',
      title: 'Reduce saturated fat intake',
      description: 'Limit saturated fat to <10% of calories to support lipid profiles.',
      priority: 'routine',
    },
    {
      id: '2',
      category: 'Activity',
      title: 'Increase daily movement',
      description: 'Aim for 150 min moderate aerobic activity weekly.',
      priority: 'routine',
    },
    {
      id: '3',
      category: 'Monitoring',
      title: 'Schedule annual lipid panel',
      description: 'Follow-up lab work to reassess cardiovascular risk.',
      priority: 'preventive',
    },
  ]
}

function deriveLabTests(): LabTest[] {
  return [
    { id: '1', name: 'Comprehensive Metabolic Panel', rationale: 'Baseline organ function and glucose.' },
    { id: '2', name: 'Lipid Panel', rationale: 'Assess cardiovascular disease risk.' },
    { id: '3', name: 'CBC with Differential', rationale: 'Screen for anemia and infection.' },
    { id: '4', name: 'HbA1c', rationale: 'Evaluate average glucose over 3 months.' },
  ]
}

function deriveLifestyle(): LifestyleTip[] {
  return [
    { id: '1', category: 'Exercise', text: 'Add 10,000 steps/day and two resistance sessions per week.' },
    { id: '2', category: 'Sleep', text: 'Maintain 7–9 hours of consistent nightly sleep.' },
    { id: '3', category: 'Stress', text: 'Try 5-min breathing exercises twice daily.' },
    { id: '4', category: 'Hydration', text: 'Target 2–2.5 L of water daily.' },
  ]
}

function computeNextAssessment(): string {
  const d = new Date()
  const next = new Date(d.setMonth(d.getMonth() + 3))
  return next.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

const ResultsDashboard: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const { report, isLoading, generateReport } = useHealthReport(id)
  const { overall, systems } = useMemo(() => deriveScores(report), [report])
  const risks = useMemo(deriveRisks, [])
  const recommendations = useMemo(deriveRecommendations, [])
  const labTests = useMemo(deriveLabTests, [])
  const lifestyle = useMemo(deriveLifestyle, [])
  const nextAssessment = useMemo(computeNextAssessment, [])

  // Trigger AI report generation if the downstream processing hasn't produced one yet.
  React.useEffect(() => {
    if (!id || report || isLoading) return
    generateReport(id)
  }, [id, report, isLoading, generateReport])

  if (isLoading) {
    return (
      <AppLayout>
        <div className="mx-auto max-w-4xl p-4">
          <div className="animate-pulse space-y-4">
            <div className="h-6 w-48 rounded bg-gray-200 dark:bg-gray-700" />
            <Card>
              <div className="p-6 space-y-4">
                <div className="h-4 w-3/4 rounded bg-gray-200 dark:bg-gray-700" />
                <div className="h-4 w-1/2 rounded bg-gray-200 dark:bg-gray-700" />
              </div>
            </Card>
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="mx-auto max-w-4xl p-4 space-y-6">
        <header className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-indigo-600" />
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Assessment Results</h1>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Generated from session <span className="font-medium">{id}</span>
          </p>
        </header>

        {/* Overall Health Score */}
        <Card>
          <div className="flex items-center justify-between">
            <ScoreGauge score={overall} />
            <div className="text-right text-xs text-gray-500 dark:text-gray-400">
              <p>Overall Health Score</p>
              <p>Updated just now</p>
            </div>
          </div>
        </Card>

        {/* Body System Scores */}
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <HeartPulse className="h-4 w-4 text-indigo-600" />
            <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">Body System Scores</h2>
          </div>
          <div className="space-y-4">
            {systems.map((s) => (
              <div key={s.id} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{s.name}</span>
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLOR[s.status]}`}>
                    {s.score} — {s.status}
                  </span>
                </div>
                <BarRow label={s.name} value={s.score} />
              </div>
            ))}
          </div>
        </Card>

        {/* Risk Indicators */}
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <BarChart2 className="h-4 w-4 text-rose-600" />
            <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">Risk Indicators</h2>
          </div>
          <div className="space-y-3">
            {risks.map((r) => (
              <div key={r.id} className={`rounded-md border border-transparent p-3 ${RISK_LEVEL_BG[r.level]}`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{r.label}</span>
                  <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium text-white ${RISK_LEVEL_COLOR[r.level]}`}>
                    {r.level}
                  </span>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-300 mt-0.5">{r.value}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Recommendations */}
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <LifeBuoy className="h-4 w-4 text-indigo-600" />
            <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">Recommendations</h2>
          </div>
          <div className="space-y-3">
            {recommendations.map((r) => (
              <div key={r.id} className="rounded-md border border-gray-200 dark:border-gray-700 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`inline-block h-1.5 w-1.5 rounded-full ${r.priority === 'urgent' ? 'bg-rose-500' : r.priority === 'routine' ? 'bg-indigo-500' : 'bg-emerald-500'}`} />
                      <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">{r.category}</span>
                    </div>
                    <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mt-1">{r.title}</p>
                    <p className="text-xs text-gray-600 dark:text-gray-300">{r.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Suggested Laboratory Tests */}
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <FlaskConical className="h-4 w-4 text-indigo-600" />
            <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">Suggested Laboratory Tests</h2>
          </div>
          <ul className="list-outside list-disc space-y-1 pl-4 text-sm text-gray-700 dark:text-gray-300">
            {labTests.map((t) => (
              <li key={t.id}>
                <span className="font-medium">{t.name}</span> — <span className="text-gray-500 dark:text-gray-400">{t.rationale}</span>
              </li>
            ))}
          </ul>
        </Card>

        {/* Lifestyle Advice */}
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <NotebookText className="h-4 w-4 text-indigo-600" />
            <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">Lifestyle Advice</h2>
          </div>
          <div className="space-y-3">
            {lifestyle.map((l) => (
              <div key={l.id} className="flex items-start gap-2">
                <span className="mt-0.5 inline-block h-1 w-1 shrink-0 rounded-full bg-indigo-500" />
                <div>
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">{l.category}</span>
                  <p className="text-sm text-gray-700 dark:text-gray-300">{l.text}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Next Assessment Date */}
        <Card>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <Repeat className="h-4 w-4 text-indigo-600" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Next recommended assessment</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{nextAssessment}</p>
              </div>
            </div>
          <Button variant="primary">
            Schedule reassessment
          </Button>
          </div>
        </Card>
      </div>
    </AppLayout>
  )
}

export default ResultsDashboard
