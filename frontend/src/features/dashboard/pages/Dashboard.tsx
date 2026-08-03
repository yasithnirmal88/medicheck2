import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Activity as ActivityGlyph,
  Brain,
  ClipboardList,
  Droplets,
  Heart,
  HeartPulse,
  Waves,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { DashboardLayout } from '@/layouts/DashboardLayout'
import { useAuth } from '@/hooks/useAuth'
import {
  useDashboardDerived,
  useDashboardProfile,
  useDashboardReports,
  useDashboardSessions,
  useDashboardMeasurements,
  useDashboardLabReports,
  computeHealthScore,
} from '../hooks/useDashboard'

import WelcomeSection from '../components/WelcomeSection'
import HealthScoreCard from '../components/HealthScoreCard'
import ProfileProgress from '../components/ProfileProgress'
import InsightCard from '../components/InsightCard'
import MetricCard from '../components/MetricCard'
import QuickActions from '../components/QuickActions'
import HealthTimeline from '../components/HealthTimeline'
import ActivityTable from '../components/ActivityTable'
import UpcomingAssessments from '../components/UpcomingAssessments'
import RecommendationList from '../components/RecommendationList'
import HealthCharts from '../components/HealthCharts'
import { DashboardSkeleton } from '../components/PageSkeleton'

import type { DerivedDashboard } from '../hooks/useDashboard'
import type { DashboardNotification } from '../components/layout/NotificationPanel'
import type { RecommendationItem } from '../components/RecommendationList'
import type { UpcomingAssessment } from '../components/UpcomingAssessments'
import type { ActivityRow } from '../components/ActivityTable'
import type { TimelineItem } from '../components/HealthTimeline'
import type { BodySystemAssessment, HealthReport, LabReport, Measurement, QuestionnaireSession } from '../types'

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
}

const fadeUp = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

interface MetricCardSpec {
  label: string
  value: string
  trend: 'up' | 'down' | 'flat'
  icon: LucideIcon
  tone: 'primary' | 'accent' | 'success' | 'warning' | 'danger'
  hint?: string
}

interface DashboardViewModel {
  notifications: DashboardNotification[]
  metricCards: MetricCardSpec[]
  upstreamAssessments: UpcomingAssessment[]
  recommendations: RecommendationItem[]
  timeline: TimelineItem[]
  activity: ActivityRow[]
  scoreSeries: { label: string; value: number }[]
  weightSeries: { label: string; weight: number; bmi: number }[]
  primaryAssessment?: string
}

export default function Dashboard() {
  const derived = useDashboardDerived()
  const profile = useDashboardProfile()
  const reports = useDashboardReports()
  const sessionsState = useDashboardSessions()
  const measurements = useDashboardMeasurements()
  const labReports = useDashboardLabReports()
  const { user } = useAuth()

  const loading =
    reports.isLoading || sessionsState.isLoading || measurements.isLoading || labReports.isLoading

  const viewModel = useMemo<DashboardViewModel>(
    () =>
      buildViewModel(
        derived,
        reports.data ?? [],
        sessionsState.data ?? [],
        measurements.data ?? [],
        labReports.data ?? [],
        profile.data?.personal_info?.height_cm ?? undefined,
      ),
    [derived, reports.data, sessionsState.data, measurements.data, labReports.data, profile.data],
  )

  return (
    <DashboardLayout
      notifications={viewModel.notifications}
      userName={profile.data?.personal_info?.full_name ?? 'User'}
      userEmail={user?.email ?? undefined}
    >
      {loading ? (
        <DashboardSkeleton />
      ) : (
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
          <motion.div variants={fadeUp}>
            <WelcomeSection
              greeting={derived.greeting}
              name={derived.name}
              healthScore={derived.healthScore}
              nextAssessment={viewModel.primaryAssessment}
              lastActivity={derived.lastActivity}
            />
          </motion.div>

          <motion.div variants={fadeUp} className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-12">
            <div className="lg:col-span-3">
              <HealthScoreCard score={derived.healthScore} />
            </div>
            <div className="lg:col-span-5">
              <InsightCard summary={derived.aiSummary} nextAssessment={viewModel.primaryAssessment} />
            </div>
            <div className="lg:col-span-4">
              <ProfileProgress
                overall={derived.completion}
                completed={derived.completedSections}
                total={derived.totalSections}
              />
            </div>
          </motion.div>

          <motion.div variants={fadeUp}>
            <h2 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">Health Summary</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {viewModel.metricCards.map((card) => (
                <MetricCard key={card.label} {...card} />
              ))}
            </div>
          </motion.div>

          <motion.div variants={fadeUp} className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <QuickActions />
            <UpcomingAssessments items={viewModel.upstreamAssessments} />
            <RecommendationList items={viewModel.recommendations} />
          </motion.div>

          <motion.div variants={fadeUp} className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <HealthTimeline items={viewModel.timeline} />
            <ActivityTable rows={viewModel.activity} />
          </motion.div>

          <motion.div variants={fadeUp}>
            <HealthCharts scoreSeries={viewModel.scoreSeries} weightSeries={viewModel.weightSeries} />
          </motion.div>
        </motion.div>
      )}
    </DashboardLayout>
  )
}

const SYSTEM_VIEWS: { token: string; label: string; icon: LucideIcon }[] = [
  { token: 'kidney', label: 'Kidney Health', icon: Droplets },
  { token: 'cardio', label: 'Heart Risk', icon: Heart },
  { token: 'heart', label: 'Heart Risk', icon: Heart },
  { token: 'diabet', label: 'Diabetes Risk', icon: ActivityGlyph },
  { token: 'metab', label: 'Diabetes Risk', icon: ActivityGlyph },
  { token: 'glucose', label: 'Diabetes Risk', icon: ActivityGlyph },
  { token: 'mental', label: 'Mental Wellness', icon: Waves },
  { token: 'brain', label: 'Mental Wellness', icon: Brain },
]

function systemView(id: string): { label: string; icon: LucideIcon } {
  for (const view of SYSTEM_VIEWS) {
    if (id.includes(view.token)) return { label: view.label, icon: view.icon }
  }
  return { label: 'System Assessment', icon: HeartPulse }
}

function buildMetricCards(bodySystems: BodySystemAssessment[]): MetricCardSpec[] {
  const cards: MetricCardSpec[] = []
  const seen = new Set<string>()
  for (const bs of bodySystems) {
    const view = systemView(bs.body_system_id)
    if (seen.has(view.label)) continue
    seen.add(view.label)
    cards.push({
      label: view.label,
      value: shortStatus(bs.category),
      trend: categoryTrend(bs.category),
      icon: view.icon,
      tone: categoryTone(bs.category),
      hint: bs.category,
    })
    if (cards.length >= 4) break
  }
  return cards
}

function categoryTone(category: string): MetricCardSpec['tone'] {
  switch (category) {
    case 'Normal':
      return 'success'
    case 'Monitor':
      return 'accent'
    case 'Urgent Medical Review':
      return 'danger'
    default:
      return 'warning'
  }
}

function categoryTrend(category: string): 'up' | 'down' | 'flat' {
  if (category === 'Normal') return 'up'
  if (category === 'Monitor') return 'flat'
  return 'down'
}

function shortStatus(category: string): string {
  switch (category) {
    case 'Normal':
      return 'Stable'
    case 'Monitor':
      return 'Watch'
    case 'Needs Attention':
      return 'Attention'
    case 'Recommend Screening':
      return 'Screening'
    case 'Urgent Medical Review':
      return 'Urgent'
    default:
      return category
  }
}

function categoryPriority(category: string): 'low' | 'medium' | 'high' {
  if (category === 'Normal') return 'low'
  if (category === 'Urgent Medical Review') return 'high'
  return 'medium'
}

function mapAdviceCategory(category?: string): RecommendationItem['category'] {
  const c = (category ?? '').toLowerCase()
  if (c.includes('nutrit') || c.includes('diet') || c.includes('food')) return 'nutrition'
  if (c.includes('exercise') || c.includes('physical') || c.includes('activ')) return 'exercise'
  if (c.includes('medical') || c.includes('screen') || c.includes('lab') || c.includes('test')) return 'medical'
  return 'lifestyle'
}

function buildUpcoming(
  derived: DerivedDashboard,
): UpcomingAssessment[] {
  if (!derived.latestBodySystems.length) return []
  return derived.latestBodySystems
    .filter((bs) => bs.category !== 'Normal')
    .slice(0, 3)
    .map<UpcomingAssessment>((bs) => ({
      id: bs.id,
      name: systemView(bs.body_system_id).label,
      priority: categoryPriority(bs.category),
      duration: '10 min',
      recommendedDate: bs.created_at,
    }))
}

function buildRecommendations(derived: DerivedDashboard): RecommendationItem[] {
  const advices = derived.latestReport?.advices ?? []
  return advices.slice(0, 3).map<RecommendationItem>((a) => ({
    id: a.id || '',
    title: a.text,
    category: mapAdviceCategory(a.category),
    priority: 'medium',
    support: true,
  }))
}

function buildActivity(
  sessions: QuestionnaireSession[],
  reports: { id: string; created_at?: string }[],
): ActivityRow[] {
  const rows: ActivityRow[] = []
  for (const s of sessions) {
    rows.push({
      id: `session-${s.id}`,
      date: s.started_at || s.created_at,
      action: `Questionnaire updated`,
      type: 'questionnaire',
      status: s.status === 'completed' ? 'completed' : 'in_progress',
    })
  }
  for (const r of reports) {
    rows.push({
      id: `report-${r.id}`,
      date: r.created_at,
      action: `Health report generated`,
      type: 'assessment',
      status: 'completed',
    })
  }
  return rows
    .sort((a, b) => (b.date ?? '').localeCompare(a.date ?? ''))
    .slice(0, 8)
}

function buildTimeline(
  sessions: QuestionnaireSession[],
  labs: LabReport[],
  reports: { id: string; created_at?: string }[],
): TimelineItem[] {
  const items: TimelineItem[] = []
  for (const s of sessions) {
    if (s.status === 'completed') {
      items.push({
        id: `session-${s.id}`,
        title: 'Assessment completed',
        description: 'A health assessment questionnaire was completed.',
        time: s.completed_at || s.started_at,
        type: 'assessment',
      })
    }
  }
  for (const r of reports) {
    items.push({
      id: `report-${r.id}`,
      title: 'Health report generated',
      description: 'A preventive health report was created.',
      time: r.created_at,
      type: 'report',
    })
  }
  for (const l of labs) {
    items.push({
      id: `lab-${l.id}`,
      title: l.test_name,
      description: 'Laboratory result recorded.',
      time: l.date || l.created_at,
      type: 'lab',
    })
  }
  return items
    .sort((a, b) => (b.time ?? '').localeCompare(a.time ?? ''))
    .slice(0, 8)
}

function buildScoreSeries(reports: HealthReport[]): { label: string; value: number }[] {
  const points = ([] as { label: string; value: number }[]).concat(
    ...reports.map((r) => {
      const score = computeHealthScore(r.body_systems ?? [])
      return score === null ? [] : [{ label: shortDate(r.created_at), value: score }]
    }),
  )
  return points.slice(0, 8).reverse()
}

function buildWeightSeries(
  measurements: Measurement[],
  heightCm: number | undefined,
): { label: string; weight: number; bmi: number }[] {
  const weights = measurements
    .filter((m) => (m.type || '').includes('weight'))
    .sort((a, b) => (a.recorded_at ?? '').localeCompare(b.recorded_at ?? ''))
    .slice(-8)
  return weights.map((m) => {
    const weight = Number(m.value)
    const bmi = heightCm && weight ? Number((weight / Math.pow(heightCm / 100, 2)).toFixed(1)) : 0
    return { label: shortDate(m.recorded_at), weight, bmi }
  })
}

function buildNotifications(derived: DerivedDashboard): DashboardNotification[] {
  const notify: DashboardNotification[] = []
  const activeCount = derived.activeSessions.length
  if (activeCount > 0) {
    notify.push({
      id: 'active-sessions',
      title: `${activeCount} questionnaire${activeCount > 1 ? 's' : ''} in progress`,
      description: 'Resume your active assessments when you\'re ready.',
      time: new Date().toISOString(),
      tone: 'info',
      icon: ClipboardList,
    })
  }
  const needs = derived.latestBodySystems.filter((bs) => bs.category === 'Needs Attention')
  if (needs.length > 0) {
    notify.push({
      id: 'risk-alert',
      title: 'Health check recommended',
      description: `${needs.length} area${needs.length > 1 ? 's' : ''} need${needs.length > 1 ? '' : 's'} closer attention.`,
      time: derived.lastActivity ?? new Date().toISOString(),
      tone: 'warning',
      icon: HeartPulse,
    })
  }
  if (derived.latestReport) {
    notify.push({
      id: 'report-ready',
      title: 'New health report generated',
      description: 'Your latest assessment report is ready to review.',
      time: derived.latestReport.created_at,
      tone: 'success',
      icon: HeartPulse,
    })
  }
  return notify
}

function buildViewModel(
  derived: DerivedDashboard,
  allReports: { id: string; created_at?: string }[],
  sessions: QuestionnaireSession[],
  measurements: Measurement[],
  labs: LabReport[],
  heightCm: number | undefined,
): DashboardViewModel {
  const upcoming = buildUpcoming(derived)
  const primaryAssessment =
    upcoming.length > 0
      ? `${upcoming[0].name} Questionnaire`
      : sessions.length > 0
        ? 'Complete a Questionnaire'
        : undefined

  return {
    notifications: buildNotifications(derived),
    metricCards: buildMetricCards(derived.latestBodySystems),
    upstreamAssessments: upcoming,
    recommendations: buildRecommendations(derived),
    timeline: buildTimeline(sessions, labs, allReports),
    activity: buildActivity(sessions, allReports),
    scoreSeries: buildScoreSeries(allReports as HealthReport[]),
    weightSeries: buildWeightSeries(measurements, heightCm),
    primaryAssessment,
  }
}

function shortDate(value?: string): string {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}