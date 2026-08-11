/**
 * Phase 6 — Population Health + SDG Analytics API layer.
 *
 * All responses are de-identified, aggregated, small-cell-suppressed.
 * No patient identifiers appear in any type or response.
 */
import api from '@/lib/api'

export interface AnalyticsFilters {
  start_date?: string
  end_date?: string
  body_system_id?: string
  language?: string
  input_type?: string
}

export interface OverviewMetrics {
  period_start: string
  period_end: string
  total_assessments: number
  completed_assessments: number
  in_progress_assessments: number
  unique_participants: number
  completion_rate: number | null
  completion_rate_suppressed: boolean
}

export interface TimeSeriesPoint {
  bucket: string
  count: number
  suppressed: boolean
}

export interface AnalyticsOverviewResponse {
  overview: OverviewMetrics
  trend: TimeSeriesPoint[]
  generated_at: string
}

export interface SeverityBucket {
  category: string
  count: number
  percentage: number | null
  suppressed: boolean
}

export interface SeverityDistributionResponse {
  period_start: string
  period_end: string
  distribution: SeverityBucket[]
  total_assessments: number
  disclaimer: string
}

export interface BodySystemMetric {
  body_system_id: string
  name: string
  code: string
  assessment_count: number
  suppressed: boolean
}

export interface BodySystemsResponse {
  period_start: string
  period_end: string
  body_systems: BodySystemMetric[]
}

export interface IndicatorTrendEntry {
  indicator_id: string
  name: string
  body_system_id: string
  activation_count: number
  suppressed: boolean
}

export interface IndicatorsResponse {
  period_start: string
  period_end: string
  indicators: IndicatorTrendEntry[]
  disclaimer: string
}

export interface TrajectoryBucket {
  trend: string
  count: number
  percentage: number | null
  suppressed: boolean
}

export interface TrajectoryResponse {
  period_start: string
  period_end: string
  distribution: TrajectoryBucket[]
  patients_with_trajectory: number
  disclaimer: string
}

export interface LanguageMetric {
  language: string
  assessment_count: number
  completion_rate: number | null
  suppressed: boolean
}

export interface AccessibilityMetrics {
  by_language: LanguageMetric[]
  voice_intake_count: number
  text_intake_count: number
  voice_completion_rate: number | null
  voice_suppressed: boolean
}

export interface AccessibilityResponse {
  period_start: string
  period_end: string
  accessibility: AccessibilityMetrics
  disclaimer: string
}

export interface SDGMetric {
  label: string
  value: number | null
  suppressed: boolean
  definition: string
}

export interface SDGSection {
  goal: string
  title: string
  metrics: SDGMetric[]
  note: string
}

export interface SDGDashboardResponse {
  period_start: string
  period_end: string
  sections: SDGSection[]
  disclaimer: string
}

const BASE = '/analytics'

function buildParams(filters?: AnalyticsFilters): Record<string, string> {
  const params: Record<string, string> = {}
  if (filters?.start_date) params.start_date = filters.start_date
  if (filters?.end_date) params.end_date = filters.end_date
  if (filters?.body_system_id) params.body_system_id = filters.body_system_id
  if (filters?.language) params.language = filters.language
  if (filters?.input_type) params.input_type = filters.input_type
  return params
}

export const analyticsApi = {
  getOverview: async (filters?: AnalyticsFilters): Promise<AnalyticsOverviewResponse> => {
    const r = await api.get<AnalyticsOverviewResponse>(`${BASE}/overview`, {
      params: buildParams(filters),
    })
    return r.data
  },

  getSeverity: async (filters?: AnalyticsFilters): Promise<SeverityDistributionResponse> => {
    const r = await api.get<SeverityDistributionResponse>(`${BASE}/severity`, {
      params: buildParams(filters),
    })
    return r.data
  },

  getBodySystems: async (filters?: AnalyticsFilters): Promise<BodySystemsResponse> => {
    const r = await api.get<BodySystemsResponse>(`${BASE}/body-systems`, {
      params: buildParams(filters),
    })
    return r.data
  },

  getIndicators: async (filters?: AnalyticsFilters): Promise<IndicatorsResponse> => {
    const r = await api.get<IndicatorsResponse>(`${BASE}/indicators`, {
      params: buildParams(filters),
    })
    return r.data
  },

  getTrajectory: async (filters?: AnalyticsFilters): Promise<TrajectoryResponse> => {
    const r = await api.get<TrajectoryResponse>(`${BASE}/trajectory`, {
      params: buildParams(filters),
    })
    return r.data
  },

  getAccessibility: async (filters?: AnalyticsFilters): Promise<AccessibilityResponse> => {
    const r = await api.get<AccessibilityResponse>(`${BASE}/accessibility`, {
      params: buildParams(filters),
    })
    return r.data
  },

  getSDGDashboard: async (filters?: AnalyticsFilters): Promise<SDGDashboardResponse> => {
    const r = await api.get<SDGDashboardResponse>(`${BASE}/sdg`, {
      params: buildParams(filters),
    })
    return r.data
  },
}
