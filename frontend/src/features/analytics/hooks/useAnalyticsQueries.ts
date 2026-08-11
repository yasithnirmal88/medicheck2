/**
 * Phase 6 — Population Health + SDG Analytics TanStack Query hooks.
 */
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/analyticsApi'
import type { AnalyticsFilters } from '../api/analyticsApi'

export function useAnalyticsOverview(filters?: AnalyticsFilters) {
  return useQuery({
    queryKey: ['analytics', 'overview', filters],
    queryFn: () => analyticsApi.getOverview(filters),
  })
}

export function useSeverityDistribution(filters?: AnalyticsFilters) {
  return useQuery({
    queryKey: ['analytics', 'severity', filters],
    queryFn: () => analyticsApi.getSeverity(filters),
  })
}

export function useBodySystemsAnalytics(filters?: AnalyticsFilters) {
  return useQuery({
    queryKey: ['analytics', 'body-systems', filters],
    queryFn: () => analyticsApi.getBodySystems(filters),
  })
}

export function useIndicatorTrends(filters?: AnalyticsFilters) {
  return useQuery({
    queryKey: ['analytics', 'indicators', filters],
    queryFn: () => analyticsApi.getIndicators(filters),
  })
}

export function useTrajectoryDistribution(filters?: AnalyticsFilters) {
  return useQuery({
    queryKey: ['analytics', 'trajectory', filters],
    queryFn: () => analyticsApi.getTrajectory(filters),
  })
}

export function useAccessibilityMetrics(filters?: AnalyticsFilters) {
  return useQuery({
    queryKey: ['analytics', 'accessibility', filters],
    queryFn: () => analyticsApi.getAccessibility(filters),
  })
}

export function useSDGDashboard(filters?: AnalyticsFilters) {
  return useQuery({
    queryKey: ['analytics', 'sdg', filters],
    queryFn: () => analyticsApi.getSDGDashboard(filters),
  })
}
