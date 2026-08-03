export type AssessmentStatus =
  | 'not_started'
  | 'in_progress'
  | 'completed'
  | 'recommended'
  | 'locked'
  | 'requires_profile'
  | 'expired'
  | 'needs_review'

export type Difficulty = 'Beginner' | 'Intermediate' | 'Advanced'
export type AIPriority = 'low' | 'medium' | 'high'

export interface BodySystemRef {
  id: string
  name: string
  icon?: string
  colorHex?: string
}

export interface AssessmentDef {
  id: string
  slug: string
  title: string
  description: string
  icon: string
  durationMinutes: number
  questionsCount: number
  difficulty: Difficulty
  bodySystems: BodySystemRef[]
  riskCategories: string[]
  recommendedFrequency: string
  aiEnabled: boolean
  priority: AIPriority
  gradient: string
  status: AssessmentStatus
  progressPct?: number
  lastSaved?: string
  completedDate?: string
  healthScore?: number
  version?: string
  doctorReviewed?: boolean
}

export interface UserAssessment extends AssessmentDef {
  startedAt?: string
  lastAccessedAt?: string
}

export type AssessmentFilterKey =
  | 'status'
  | 'bodySystem'
  | 'duration'
  | 'difficulty'
  | 'priority'

export interface AssessmentFilters {
  search: string
  status: AssessmentStatus[]
  bodySystem: string[]
  duration: 'short' | 'medium' | 'long' | ''
  difficulty: Difficulty[]
  priority: AIPriority[]
}

export interface HealthScorePoint {
  date: string
  score: number
}

export interface AIInsight {
  currentHealthScore: number
  riskTrend: 'improving' | 'declining' | 'stable'
  mostImproved: string
  highestRisk: string
  confidence: number
  lastAIUpdate: string
}

export interface TimelineItem {
  id: string
  type: 'completed' | 'started' | 'profile' | 'lab' | 'rec' | 'ai'
  title: string
  meta?: string
  date: string
  icon: string
  iconBg: string
}
