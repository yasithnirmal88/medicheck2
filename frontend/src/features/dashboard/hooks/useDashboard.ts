import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  fetchCompletion,
  fetchLabReports,
  fetchMeasurements,
  fetchProfile,
  fetchReports,
  fetchSessions,
} from '../api/dashboardService'
import type {
  BodySystemAssessment,
  HealthReport,
  ProfileCompletion,
  QuestionnaireSession,
} from '../types'

const FIVE_MIN = 1000 * 60 * 5

/**
 * Dashboard queries are gated on `enabled` so they never fire before an
 * authenticated Firebase user is available. Without this, un-blocking the
 * auth gate (P1-2) would let requests fire with no token, producing 401s and
 * retry storms. Callers pass `enabled = !!user`.
 */
export function useDashboardProfile(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['dashboard', 'profile'],
    queryFn: fetchProfile,
    staleTime: FIVE_MIN,
    enabled: options?.enabled ?? true,
  })
}

export function useDashboardCompletion(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['dashboard', 'completion'],
    queryFn: fetchCompletion,
    staleTime: 1000 * 30,
    enabled: options?.enabled ?? true,
  })
}

export function useDashboardSessions(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['dashboard', 'sessions'],
    queryFn: fetchSessions,
    staleTime: 1000 * 30,
    enabled: options?.enabled ?? true,
  })
}

export function useDashboardReports(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['dashboard', 'reports'],
    queryFn: () => fetchReports(8),
    staleTime: 1000 * 60,
    enabled: options?.enabled ?? true,
  })
}

export function useDashboardMeasurements(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['dashboard', 'measurements'],
    queryFn: fetchMeasurements,
    staleTime: FIVE_MIN,
    enabled: options?.enabled ?? true,
  })
}

export function useDashboardLabReports(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['dashboard', 'lab-reports'],
    queryFn: fetchLabReports,
    staleTime: FIVE_MIN,
    enabled: options?.enabled ?? true,
  })
}

function greetingByHour(hour: number): string {
  if (hour < 12) return 'Good Morning'
  if (hour < 17) return 'Good Afternoon'
  return 'Good Evening'
}

const CATEGORY_RISK_POINTS: Record<string, number> = {
  Normal: 0,
  Monitor: 5,
  'Needs Attention': 15,
  'Recommend Screening': 25,
  'Urgent Medical Review': 40,
}

export function computeHealthScore(bodySystems: BodySystemAssessment[]): number | null {
  if (!bodySystems.length) return null
  const raw =
    bodySystems.reduce((acc, bs) => acc + (CATEGORY_RISK_POINTS[bs.category] ?? 10), 0) /
    bodySystems.length
  return Math.max(0, Math.min(100, Math.round(100 - raw)))
}

export interface DerivedDashboard {
  name: string
  greeting: string
  lastActivity?: string
  completion: number | null
  completedSections: number
  totalSections: number
  activeSessions: QuestionnaireSession[]
  latestReport?: HealthReport
  latestBodySystems: BodySystemAssessment[]
  healthScore: number | null
  aiSummary?: string
}

export function useDashboardDerived(options?: { enabled?: boolean }): DerivedDashboard {
  const enabled = options?.enabled ?? true
  const profile = useDashboardProfile({ enabled })
  const completion = useDashboardCompletion({ enabled })
  const sessions = useDashboardSessions({ enabled })
  const reports = useDashboardReports({ enabled })

  return useMemo(() => {
    const reportsData: HealthReport[] = reports.data ?? []
    const sessionsData: QuestionnaireSession[] = sessions.data ?? []
    const completionData: ProfileCompletion | undefined = completion.data
    const latestReport = reportsData[0]

    const fullName = profile.data?.personal_info?.full_name ?? ''
    const firstName = fullName.trim().split(' ')[0] || 'there'

    const activeSessions = sessionsData.filter(
      (s) => s.status === 'in_progress' || s.status === 'paused',
    )

    const latestBodySystems = latestReport?.body_systems ?? []

    return {
      healthScore: computeHealthScore(latestBodySystems),
      greeting: greetingByHour(new Date().getHours()),
      name: firstName,
      lastActivity: latestReport?.created_at,
      completion: completionData?.overall ?? null,
      completedSections: completionData?.completed ?? 0,
      totalSections: completionData?.total ?? 0,
      activeSessions,
      latestReport,
      latestBodySystems,
      aiSummary: latestReport?.summary,
    }
  }, [profile.data, completion.data, sessions.data, reports.data])
}