import api from '@/lib/api'
import type {
  Approval, AuditDiff, AuditLogEntry, AuditStats, BodySystem,
  BranchRule, BuilderVersion, ChangeRequest, ClinicalGuideline,
  ClinicalIndicator, CMSDashboardOverview, DecisionRule,
  DependencyRule, Disease, EntitySearchResult, EntityType,
  EvidenceReference, ExerciseProgram, GraphValidationResult,
  ImpactAnalysis, ImagingTest, KnowledgeGraph, LaboratoryTest,
  LifestyleAdvice, MedicationRecommendation, NutritionAdvice,
  PaginatedResponse, PublishingJob, Question, QuestionGroup,
  QuestionGroupWithQuestions, Recommendation, RecentActivity,
  Review, RuleConflict, RuleEvaluationResult, RuleSet,
  SeverityThreshold, Symptom, Template, UserProfile, UserRole,
  VersionSnapshot, Workflow, WorkflowSummary,
} from '../types'

function contentBase(entityType: string) {
  return `/api/v1/cms/content/${entityType}`
}

function entityApi<T>(entityType: EntityType) {
  const base = contentBase(entityType)
  return {
    list: (params?: Record<string, unknown>) =>
      api.get<PaginatedResponse<T>>(base, { params }).then((r) => r.data),
    getById: (id: string) =>
      api.get<T>(`${base}/${id}`).then((r) => r.data),
    create: (data: Partial<T>) =>
      api.post<T>(base, data).then((r) => r.data),
    update: (id: string, data: Partial<T>) =>
      api.put<T>(`${base}/${id}`, data).then((r) => r.data),
    delete: (id: string) =>
      api.delete(`${base}/${id}`),
    search: (params?: Record<string, unknown>) =>
      api.get<PaginatedResponse<T>>(`${base}/search`, { params }).then((r) => r.data),
    count: () =>
      api.get<number>(`${base}/count`).then((r) => r.data),
  }
}

export const cmsApi = {
  // ---- Dashboard ----
  getDashboardOverview: () =>
    api.get<CMSDashboardOverview>('/api/v1/cms/dashboard/overview').then((r) => r.data),
  getRecentActivity: (limit = 20) =>
    api.get<RecentActivity[]>('/api/v1/cms/dashboard/recent-activity', { params: { limit } }).then((r) => r.data),
  getWorkflowSummary: () =>
    api.get<WorkflowSummary>('/api/v1/cms/dashboard/workflow-summary').then((r) => r.data),

  // ---- Content ----
  questions: entityApi<Question>('question'),
  questionGroups: entityApi<QuestionGroup>('question_group'),
  diseases: entityApi<Disease>('disease'),
  bodySystems: entityApi<BodySystem>('body_system'),
  symptoms: entityApi<Symptom>('symptom'),
  indicators: entityApi<ClinicalIndicator>('indicator'),
  labTests: entityApi<LaboratoryTest>('lab_test'),
  imagingTests: entityApi<ImagingTest>('imaging'),
  recommendations: entityApi<Recommendation>('recommendation'),
  lifestyleAdvice: entityApi<LifestyleAdvice>('lifestyle'),
  exercisePrograms: entityApi<ExerciseProgram>('exercise'),
  nutritionAdvice: entityApi<NutritionAdvice>('nutrition'),
  evidenceReferences: entityApi<EvidenceReference>('evidence'),
  templates: entityApi<Template>('template'),
  clinicalGuidelines: entityApi<ClinicalGuideline>('guideline'),
  medications: entityApi<MedicationRecommendation>('medication'),
  decisionRules: entityApi<DecisionRule>('rule'),
  severityThresholds: entityApi<SeverityThreshold>('severity_threshold'),

  // ---- Question Builder ----
  builder: {
    getGroups: (templateId?: string) =>
      api.get<QuestionGroupWithQuestions[]>('/api/v1/cms/builder/groups', { params: { template_id: templateId } }).then((r) => r.data),
    reorderGroups: (groupIds: string[]) =>
      api.put('/api/v1/cms/builder/groups/reorder', { group_ids: groupIds }),
    moveGroup: (groupId: string, direction: 'up' | 'down') =>
      api.put(`/api/v1/cms/builder/groups/${groupId}/move`, { direction }),
    cloneQuestion: (questionId: string, groupId?: string) =>
      api.post<Question>('/api/v1/cms/builder/questions/clone', { question_id: questionId, group_id: groupId }).then((r) => r.data),
    getDependencies: (questionId?: string) =>
      api.get<DependencyRule[]>('/api/v1/cms/builder/dependencies', { params: { question_id: questionId } }).then((r) => r.data),
    createDependency: (data: Partial<DependencyRule>) =>
      api.post<DependencyRule>('/api/v1/cms/builder/dependencies', data).then((r) => r.data),
    deleteDependency: (id: string) =>
      api.delete(`/api/v1/cms/builder/dependencies/${id}`),
    getBranchRules: (questionId?: string) =>
      api.get<BranchRule[]>('/api/v1/cms/builder/branch-rules', { params: { question_id: questionId } }).then((r) => r.data),
    createBranchRule: (data: Partial<BranchRule>) =>
      api.post<BranchRule>('/api/v1/cms/builder/branch-rules', data).then((r) => r.data),
    deleteBranchRule: (id: string) =>
      api.delete(`/api/v1/cms/builder/branch-rules/${id}`),
    simulate: (questionId: string, answers: Record<string, unknown>) =>
      api.post('/api/v1/cms/builder/simulate', { question_id: questionId, answers }).then((r) => r.data),
    getVersions: (templateId: string) =>
      api.get<BuilderVersion[]>('/api/v1/cms/builder/versions', { params: { template_id: templateId } }).then((r) => r.data),
    createVersion: (templateId: string, reason?: string) =>
      api.post<BuilderVersion>('/api/v1/cms/builder/versions', { template_id: templateId, reason }).then((r) => r.data),
  },

  // ---- Rule Engine ----
  rules: {
    getSets: () =>
      api.get<RuleSet[]>('/api/v1/cms/rules').then((r) => r.data),
    getSet: (id: string) =>
      api.get<RuleSet>(`/api/v1/cms/rules/${id}`).then((r) => r.data),
    createSet: (data: Partial<RuleSet>) =>
      api.post<RuleSet>('/api/v1/cms/rules', data).then((r) => r.data),
    updateSet: (id: string, data: Partial<RuleSet>) =>
      api.put<RuleSet>(`/api/v1/cms/rules/${id}`, data).then((r) => r.data),
    evaluate: (ruleSetId: string, context: Record<string, unknown>) =>
      api.post<RuleEvaluationResult[]>('/api/v1/cms/rules/evaluate', { rule_set_id: ruleSetId, context }).then((r) => r.data),
    batchEvaluate: (evaluations: { rule_set_id: string; context: Record<string, unknown> }[]) =>
      api.post<RuleEvaluationResult[][]>('/api/v1/cms/rules/batch-evaluate', { evaluations }).then((r) => r.data),
    simulate: (expression: unknown, context: Record<string, unknown>) =>
      api.post<RuleEvaluationResult>('/api/v1/cms/rules/simulate', { expression, context }).then((r) => r.data),
    validate: (expression: unknown) =>
      api.post('/api/v1/cms/rules/validate', { expression }).then((r) => r.data),
    compute: (bodySystemId: string, context: Record<string, unknown>) =>
      api.post('/api/v1/cms/rules/compute', { body_system_id: bodySystemId, context }).then((r) => r.data),
    detectConflicts: (ruleIds: string[]) =>
      api.post<RuleConflict[]>('/api/v1/cms/rules/detect-conflicts', { rule_ids: ruleIds }).then((r) => r.data),
  },

  // ---- Knowledge Graph ----
  knowledgeGraph: {
    listGraphs: (bodySystemId?: string) =>
      api.get<KnowledgeGraph[]>('/api/v1/cms/knowledge-graph/graphs', { params: { body_system_id: bodySystemId } }).then((r) => r.data),
    createGraph: (data: Partial<KnowledgeGraph>) =>
      api.post<KnowledgeGraph>('/api/v1/cms/knowledge-graph/graphs', data).then((r) => r.data),
    getGraph: (id: string) =>
      api.get(`/api/v1/cms/knowledge-graph/graphs/${id}`).then((r) => r.data),
    updateGraph: (id: string, data: Partial<KnowledgeGraph>) =>
      api.put(`/api/v1/cms/knowledge-graph/graphs/${id}`, data).then((r) => r.data),
    deleteGraph: (id: string) =>
      api.delete(`/api/v1/cms/knowledge-graph/graphs/${id}`),
    addNode: (graphId: string, data: Record<string, unknown>) =>
      api.post(`/api/v1/cms/knowledge-graph/graphs/${graphId}/nodes`, data).then((r) => r.data),
    updateNode: (nodeId: string, data: Record<string, unknown>) =>
      api.put(`/api/v1/cms/knowledge-graph/graphs/nodes/${nodeId}`, data).then((r) => r.data),
    removeNode: (nodeId: string) =>
      api.delete(`/api/v1/cms/knowledge-graph/graphs/nodes/${nodeId}`),
    addEdge: (graphId: string, data: Record<string, unknown>) =>
      api.post(`/api/v1/cms/knowledge-graph/graphs/${graphId}/edges`, data).then((r) => r.data),
    removeEdge: (edgeId: string) =>
      api.delete(`/api/v1/cms/knowledge-graph/graphs/edges/${edgeId}`),
    validateGraph: (graphId: string) =>
      api.post<GraphValidationResult>(`/api/v1/cms/knowledge-graph/graphs/${graphId}/validate`).then((r) => r.data),
    analyzeImpact: (entityType: string, entityId: string) =>
      api.get<ImpactAnalysis>(`/api/v1/cms/knowledge-graph/impact/${entityType}/${entityId}`).then((r) => r.data),
    searchEntities: (query: string, limit = 20) =>
      api.get<EntitySearchResult[]>('/api/v1/cms/knowledge-graph/search', { params: { query, limit } }).then((r) => r.data),
    bulkLink: (data: { entity_type: string; source_ids: string[]; target_type: string; target_ids: string[]; relationship_type?: string }) =>
      api.post('/api/v1/cms/knowledge-graph/bulk-link', data).then((r) => r.data),
  },

  // ---- Publishing ----
  publishing: {
    listWorkflows: (entityType?: string) =>
      api.get<Workflow[]>('/api/v1/cms/publishing/workflows', { params: { entity_type: entityType } }).then((r) => r.data),
    createWorkflow: (data: Partial<Workflow>) =>
      api.post<Workflow>('/api/v1/cms/publishing/workflows', data).then((r) => r.data),
    getWorkflow: (id: string) =>
      api.get<Workflow>(`/api/v1/cms/publishing/workflows/${id}`).then((r) => r.data),
    updateWorkflow: (id: string, data: Partial<Workflow>) =>
      api.put<Workflow>(`/api/v1/cms/publishing/workflows/${id}`, data).then((r) => r.data),
    listJobs: (status?: string, entityType?: string) =>
      api.get<PublishingJob[]>('/api/v1/cms/publishing/jobs', { params: { status, entity_type: entityType } }).then((r) => r.data),
    createJob: (data: Partial<PublishingJob>) =>
      api.post<PublishingJob>('/api/v1/cms/publishing/jobs', data).then((r) => r.data),
    getJob: (id: string) =>
      api.get<PublishingJob>(`/api/v1/cms/publishing/jobs/${id}`).then((r) => r.data),
    approveJob: (id: string) =>
      api.post(`/api/v1/cms/publishing/jobs/${id}/approve`).then((r) => r.data),
    executePublish: (id: string) =>
      api.post(`/api/v1/cms/publishing/jobs/${id}/publish`).then((r) => r.data),
    failJob: (id: string, reason: string) =>
      api.post(`/api/v1/cms/publishing/jobs/${id}/fail`, { reason }).then((r) => r.data),
    rollbackJob: (id: string, version: number) =>
      api.post(`/api/v1/cms/publishing/jobs/${id}/rollback`, { rollback_version: version }).then((r) => r.data),
    processScheduled: () =>
      api.post('/api/v1/cms/publishing/jobs/process-scheduled').then((r) => r.data),
    listApprovals: (status?: string, entityType?: string) =>
      api.get<Approval[]>('/api/v1/cms/publishing/approvals', { params: { status, entity_type: entityType } }).then((r) => r.data),
    createApproval: (data: Partial<Approval>) =>
      api.post<Approval>('/api/v1/cms/publishing/approvals', data).then((r) => r.data),
    approveEntity: (id: string, comment?: string) =>
      api.post(`/api/v1/cms/publishing/approvals/${id}/approve`, { comment }).then((r) => r.data),
    rejectApproval: (id: string, reason: string) =>
      api.post(`/api/v1/cms/publishing/approvals/${id}/reject`, { reason }).then((r) => r.data),
    addApprovalComment: (id: string, comment: string) =>
      api.post(`/api/v1/cms/publishing/approvals/${id}/comment`, { comment }).then((r) => r.data),
    listReviews: (status?: string, entityType?: string) =>
      api.get<Review[]>('/api/v1/cms/publishing/reviews', { params: { status, entity_type: entityType } }).then((r) => r.data),
    createReview: (data: Partial<Review>) =>
      api.post<Review>('/api/v1/cms/publishing/reviews', data).then((r) => r.data),
    completeReview: (id: string, decision: string, comments?: string, score?: number) =>
      api.post(`/api/v1/cms/publishing/reviews/${id}/complete`, { decision, comments, score }).then((r) => r.data),
    listChangeRequests: (status?: string, entityType?: string) =>
      api.get<ChangeRequest[]>('/api/v1/cms/publishing/change-requests', { params: { status, entity_type: entityType } }).then((r) => r.data),
    createChangeRequest: (data: Partial<ChangeRequest>) =>
      api.post<ChangeRequest>('/api/v1/cms/publishing/change-requests', data).then((r) => r.data),
    approveChangeRequest: (id: string) =>
      api.post(`/api/v1/cms/publishing/change-requests/${id}/approve`).then((r) => r.data),
    rejectChangeRequest: (id: string, reason: string) =>
      api.post(`/api/v1/cms/publishing/change-requests/${id}/reject`, { reason }).then((r) => r.data),
    detectConflicts: (entityType: string, entityId: string) =>
      api.get('/api/v1/cms/publishing/change-requests/conflicts', { params: { entity_type: entityType, entity_id: entityId } }).then((r) => r.data),
    listSnapshots: (entityType: string, entityId: string) =>
      api.get<VersionSnapshot[]>('/api/v1/cms/publishing/snapshots', { params: { entity_type: entityType, entity_id: entityId } }).then((r) => r.data),
    createSnapshot: (data: Partial<VersionSnapshot>) =>
      api.post<VersionSnapshot>('/api/v1/cms/publishing/snapshots', data).then((r) => r.data),
  },

  // ---- Audit ----
  audit: {
    search: (params?: Record<string, unknown>) =>
      api.get<{ items: AuditLogEntry[]; total: number; skip: number; limit: number }>('/api/v1/cms/audit/logs', { params }).then((r) => r.data),
    getTimeline: (entityType: string, entityId: string) =>
      api.get<AuditLogEntry[]>(`/api/v1/cms/audit/timeline/${entityType}/${entityId}`).then((r) => r.data),
    getDiffs: (entityType: string, entityId: string) =>
      api.get<AuditDiff[]>(`/api/v1/cms/audit/diffs/${entityType}/${entityId}`).then((r) => r.data),
    export: (entityType?: string, format = 'json') =>
      api.get('/api/v1/cms/audit/export', { params: { entity_type: entityType, format }, responseType: format === 'csv' ? 'blob' : 'json' }).then((r) => r.data),
    getStats: (days = 30) =>
      api.get<AuditStats>('/api/v1/cms/audit/stats', { params: { days } }).then((r) => r.data),
  },

  // ---- Users & Roles ----
  users: {
    list: (params?: Record<string, unknown>) =>
      api.get<PaginatedResponse<UserProfile>>('/api/v1/admin/users', { params }).then((r) => r.data),
    getById: (id: string) =>
      api.get<UserProfile>(`/api/v1/admin/users/${id}`).then((r) => r.data),
    updateRoles: (userId: string, roles: string[]) =>
      api.put(`/api/v1/admin/users/${userId}/roles`, { roles }).then((r) => r.data),
    toggleActive: (userId: string) =>
      api.post(`/api/v1/admin/users/${userId}/toggle-active`).then((r) => r.data),
  },
  roles: {
    list: () =>
      api.get<UserRole[]>('/api/v1/admin/roles').then((r) => r.data),
    create: (data: Partial<UserRole>) =>
      api.post<UserRole>('/api/v1/admin/roles', data).then((r) => r.data),
    update: (id: string, data: Partial<UserRole>) =>
      api.put<UserRole>(`/api/v1/admin/roles/${id}`, data).then((r) => r.data),
    getPermissions: (roleId: string) =>
      api.get<string[]>(`/api/v1/admin/roles/${roleId}/permissions`).then((r) => r.data),
    updatePermissions: (roleId: string, permissions: string[]) =>
      api.put(`/api/v1/admin/roles/${roleId}/permissions`, { permissions }).then((r) => r.data),
  },

  // ---- Search ----
  search: (query: string, entityType?: string, limit = 50) =>
    api.get('/api/v1/cms/content/search', { params: { query, entity_type: entityType, limit } }).then((r) => r.data),
}
