// ---- Common ----
export interface BaseEntity {
  id: string
  is_active: boolean
  version: number
  created_by: string | null
  updated_by: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

// ---- Dashboard ----
export interface CMSDashboardOverview {
  total_entities: number
  by_type: Record<string, number>
  by_status: Record<string, Record<string, number>>
  knowledge_graph: { graphs: number; nodes: number }
  workflow_pending: {
    approvals: number
    reviews: number
    publishing_jobs: number
    approved_jobs: number
    change_requests: number
  }
  audit: { total_entries: number; recent_updates: number }
}

export interface RecentActivity {
  id: string
  actor_id: string
  entity_type: string
  entity_id: string
  action: string
  changed_at: string | null
  reason: string | null
}

export interface WorkflowSummary {
  approvals: Record<string, number>
  reviews: Record<string, number>
  jobs: Record<string, number>
  change_requests: Record<string, number>
}

// ---- Content Entities ----
export interface Question extends BaseEntity {
  code: string
  text: string
  question_type: string
  question_group_id: string | null
  description: string | null
  tooltip: string | null
  is_required: boolean
  validation_rules: Record<string, unknown> | null
  priority: number
  difficulty: string | null
  body_system_id: string | null
  status: string
  options: QuestionOption[]
}

export interface QuestionOption {
  id: string
  question_id: string
  code: string
  text: string
  value: string
  score_value: number | null
  severity: string | null
  color_hex: string | null
  display_order: number
}

export interface QuestionGroup extends BaseEntity {
  name: string
  title: string
  description: string | null
  body_system_id: string | null
  display_order: number
  is_required: boolean
}

export interface Disease extends BaseEntity {
  name: string
  icd10_code: string | null
  description: string | null
  body_system_id: string | null
  severity: string | null
  status: string
}

export interface BodySystem extends BaseEntity {
  name: string
  code: string
  description: string | null
  icon: string | null
  color_hex: string | null
  display_order: number
  status: string
}

export interface Symptom extends BaseEntity {
  name: string
  code: string
  description: string | null
  body_system_id: string | null
  severity: string | null
  status: string
}

export interface ClinicalIndicator extends BaseEntity {
  name: string
  code: string
  key: string | null
  description: string | null
  body_system_id: string | null
  indicator_type: string | null
  severity: string | null
  priority: number
  status: string
}

export interface LaboratoryTest extends BaseEntity {
  name: string
  code: string
  loinc_code: string | null
  description: string | null
  body_system_id: string | null
  specimen_type: string | null
  is_fasting_required: boolean
  status: string
}

export interface ImagingTest extends BaseEntity {
  name: string
  code: string
  description: string | null
  body_system_id: string | null
  modality: string | null
  preparation: string | null
  status: string
}

export interface Recommendation extends BaseEntity {
  title: string
  code: string
  description: string | null
  body_system_id: string | null
  recommendation_type: string | null
  urgency: string | null
  status: string
}

export interface LifestyleAdvice extends BaseEntity {
  name: string
  code: string
  description: string | null
  category: string | null
  body_system_id: string | null
  status: string
}

export interface ExerciseProgram extends BaseEntity {
  name: string
  code: string
  description: string | null
  body_system_id: string | null
  difficulty_level: string | null
  duration_minutes: number | null
  frequency: string | null
  status: string
}

export interface NutritionAdvice extends BaseEntity {
  name: string
  code: string
  description: string | null
  meal_type: string | null
  calories: number | null
  diet_type: string | null
  status: string
}

export interface MedicalEvidence extends BaseEntity {
  title: string
  code: string
  description: string | null
  body_system_id: string | null
  evidence_type: string | null
  status: string
}

export interface EvidenceReference {
  id: string
  title: string
  citation: string | null
  pmid: string | null
  doi: string | null
  evidence_level: string | null
  confidence_score: number | null
  summary: string | null
  url: string | null
  authors: string | null
  published_at: string | null
  entity_type: string | null
  entity_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Template extends BaseEntity {
  name: string
  code: string
  description: string | null
  body_system_id: string | null
  version: number
  status: string
}

export interface ClinicalGuideline extends BaseEntity {
  title: string
  code: string
  description: string | null
  body_system_id: string | null
  organization: string | null
  evidence_level: string | null
  status: string
}

export interface MedicationRecommendation extends BaseEntity {
  name: string
  generic_name: string | null
  code: string
  description: string | null
  dosage: string | null
  route: string | null
  frequency: string | null
  status: string
}

export interface MedicalTag extends BaseEntity {
  name: string
  code: string
  color_hex: string | null
  status: string
}

export interface MedicalSpecialty extends BaseEntity {
  name: string
  code: string
  description: string | null
  status: string
}

export interface RiskCategory extends BaseEntity {
  name: string
  code: string
  description: string | null
  min_score: number | null
  max_score: number | null
  color_hex: string | null
  status: string
}

export interface SeverityThreshold extends BaseEntity {
  name: string
  code: string
  description: string | null
  severity_level: string | null
  min_value: number | null
  max_value: number | null
  color_hex: string | null
  status: string
}

export interface ScoringProfile extends BaseEntity {
  name: string
  code: string
  description: string | null
  body_system_id: string | null
  scoring_type: string | null
  status: string
}

export interface DiseaseCategory extends BaseEntity {
  name: string
  code: string
  description: string | null
  status: string
}

export interface BodySystemCategory extends BaseEntity {
  name: string
  code: string
  description: string | null
  status: string
}

export interface RecommendationCategory extends BaseEntity {
  name: string
  code: string
  description: string | null
  status: string
}

export interface LabPanel extends BaseEntity {
  name: string
  code: string
  description: string | null
  body_system_id: string | null
  status: string
}

export interface Biomarker extends BaseEntity {
  name: string
  code: string
  description: string | null
  lab_panel_id: string | null
  reference_range: string | null
  unit: string | null
  status: string
}

export interface QuestionCategory extends BaseEntity {
  name: string
  code: string
  description: string | null
  status: string
}

export interface QuestionTag extends BaseEntity {
  name: string
  code: string
  color_hex: string | null
  status: string
}

// ---- Knowledge Graph ----
export interface KnowledgeGraph extends BaseEntity {
  name: string
  body_system_id: string | null
  description: string | null
  status: string
}

export interface KnowledgeGraphNode extends BaseEntity {
  graph_id: string
  entity_type: string
  entity_id: string
  label: string
  x_position: number
  y_position: number
  color: string | null
  metadata: Record<string, unknown> | null
}

export interface KnowledgeGraphEdge extends BaseEntity {
  graph_id: string
  source_node_id: string
  target_node_id: string
  relationship_type: string
  label: string | null
  weight: number
  metadata: Record<string, unknown> | null
}

export interface GraphValidationResult {
  graph_id: string
  total_nodes: number
  total_edges: number
  entity_distribution: Record<string, number>
  orphan_nodes: string[]
  orphan_count: number
  cycles: string[][]
  cycle_count: number
  issues: string[]
  is_valid: boolean
}

export interface ImpactAnalysis {
  entity_type: string
  entity_id: string
  upstream_count: number
  upstream: { entity_type: string; entity_id: string; relationship: string }[]
  downstream_count: number
  downstream: { entity_type: string; entity_id: string; relationship: string }[]
}

export interface EntitySearchResult {
  entity_type: string
  id: string
  label: string
}

// ---- Question Builder ----
export interface QuestionGroupWithQuestions extends QuestionGroup {
  questions: Question[]
}

export interface DependencyRule {
  id: string
  question_id: string
  depends_on_question_id: string
  condition: string
  value: string | null
  logic_type: string
}

export interface BranchRule {
  id: string
  question_id: string
  condition: string
  target_question_id: string
  priority: number
}

export interface BuilderVersion {
  id: string
  template_id: string
  version: number
  snapshot: Record<string, unknown>
  snapshot_type: string
  reason: string | null
  created_by: string | null
  created_at: string
}

// ---- Rules ----
export interface DecisionRule extends BaseEntity {
  name: string
  code: string
  description: string | null
  body_system_id: string | null
  rule_type: string | null
  expression: Record<string, unknown> | null
  priority: number
  status: string
}

export interface RuleEvaluationResult {
  rule_id: string
  name: string
  result: boolean | number | string
  confidence: number | null
}

export interface RuleConflict {
  rule_a: string
  rule_b: string
  description: string
}

// ---- Publishing ----
export interface Workflow extends BaseEntity {
  name: string
  description: string | null
  entity_type: string
  steps: Record<string, unknown>[]
  current_step: number
  status: string
}

export interface PublishingJob {
  id: string
  entity_type: string
  entity_id: string
  version: number
  requested_by: string
  approved_by: string | null
  status: 'pending' | 'approved' | 'published' | 'failed' | 'rolled_back'
  schedule_at: string | null
  published_at: string | null
  rollback_version: number | null
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Approval extends BaseEntity {
  entity_type: string
  entity_id: string
  requested_by: string
  assigned_to: string | null
  role_required: string | null
  status: string
  comments: ApprovalComment[]
  decided_at: string | null
}

export interface ApprovalComment {
  user_id: string
  comment: string
  created_at: string
}

export interface Review extends BaseEntity {
  entity_type: string
  entity_id: string
  reviewer_id: string
  review_type: string
  status: string
  decision: string | null
  comments: string | null
  score: number | null
  completed_at: string | null
}

export interface ChangeRequest extends BaseEntity {
  entity_type: string
  entity_id: string
  requested_by: string
  title: string
  description: string | null
  changes: Record<string, unknown>
  reason: string | null
  status: string
  resolved_at: string | null
  resolved_by: string | null
}

export interface VersionSnapshot {
  id: string
  entity_type: string
  entity_id: string
  version: number
  snapshot: Record<string, unknown>
  snapshot_type: string
  reason: string | null
  created_by: string | null
  created_at: string
}

// ---- Audit ----
export interface AuditLogEntry {
  id: string
  actor_id: string | null
  actor_role: string | null
  entity_type: string
  entity_id: string | null
  action: string
  changed_at: string | null
  old_value: string | null
  new_value: string | null
  reason: string | null
  ip_address: string | null
  user_agent: string | null
  session_id: string | null
  request_id: string | null
  status_code: number | null
  method: string | null
  path: string | null
}

export interface AuditDiff {
  id: string
  action: string
  changed_at: string
  actor_id: string | null
  reason: string | null
  changed_fields: { field: string; old_value: unknown; new_value: unknown }[]
}

export interface AuditStats {
  period_days: number
  total_actions: number
  by_action: Record<string, number>
  by_entity_type: Record<string, number>
  top_actors: { actor_id: string; actions: number }[]
}

// ---- Users & Roles ----
export interface UserRole {
  id: string
  name: string
  code: string
  description: string | null
  hierarchy_level: number
  is_active: boolean
}

export interface UserProfile {
  id: string
  firebase_uid: string
  email: string
  full_name: string
  avatar_url: string | null
  email_verified: boolean
  is_active: boolean
  roles: string[]
  created_at: string
  updated_at: string
}

// ---- Rule Builder ----
export interface RuleExpression {
  type: 'and' | 'or' | 'not' | 'if_else' | 'condition'
  conditions?: RuleExpression[]
  field?: string
  operator?: string
  value?: unknown
  if_true?: RuleExpression
  if_false?: RuleExpression
}

export interface RuleSet {
  id: string
  name: string
  description: string | null
  body_system_id: string | null
  expression: RuleExpression
  version: number
  status: string
  created_at: string
  updated_at: string
}

// ---- Entity type map ----
export const ENTITY_TYPES = [
  'question', 'question_group', 'disease', 'body_system', 'symptom',
  'indicator', 'lab_test', 'imaging', 'recommendation',
  'lifestyle', 'exercise', 'nutrition', 'evidence',
  'template', 'guideline', 'medication', 'tag', 'specialty',
  'risk_category', 'severity_threshold', 'scoring_profile',
  'rule', 'disease_category', 'body_system_category', 'recommendation_category',
  'lab_panel', 'biomarker', 'question_category', 'question_tag',
] as const

export type EntityType = (typeof ENTITY_TYPES)[number]
