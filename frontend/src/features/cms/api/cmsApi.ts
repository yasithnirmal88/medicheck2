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
  return `/cms/content/${entityType}`
}

// Entities that have dedicated CMS routers (backend/app/api/v1/cms/questions.py)
// rather than the generic /cms/content router. These return flat entity arrays
// (not the generic CMSEntityResponse), so they are wrapped into the
// PaginatedResponse shape the list pages expect. The dedicated routers hold the
// seeded data (questions, question_groups, body_systems, questionnaire_templates),
// while the generic content tables (e.g. template_libraries) are empty.
const DEDICATED_ENDPOINTS: Record<string, string> = {
  question: '/cms/questions',
  question_group: '/cms/question-groups',
  body_system: '/cms/body-systems',
  template: '/cms/templates',
}

function isDedicated(entityType: string): boolean {
  return entityType in DEDICATED_ENDPOINTS
}

// Generic content API used by useContentList/useContentItem/useCreateContent/
// useUpdateContent/useDeleteContent. The backend content router accepts both
// the abbreviated names used here and canonical names (it aliases them
// server-side), so the frontend keeps its existing EntityType values.
export const contentApi = {
  list: <T>(entityType: string, params?: Record<string, unknown>) => {
    if (isDedicated(entityType)) {
      return api.get<T[]>(DEDICATED_ENDPOINTS[entityType]).then((r) => ({
        items: r.data,
        total: r.data.length,
        skip: 0,
        limit: r.data.length,
      }))
    }
    return api.get<PaginatedResponse<T>>(contentBase(entityType), { params }).then((r) => r.data)
  },
  getById: <T>(entityType: string, id: string) => {
    if (isDedicated(entityType)) {
      // Dedicated routers expose list endpoints; find the item client-side.
      return api.get<T[]>(DEDICATED_ENDPOINTS[entityType]).then(
        (r) => r.data.find((item) => (item as { id?: string }).id === id) ?? null
      )
    }
    return api.get<T>(`${contentBase(entityType)}/${id}`).then((r) => r.data)
  },
  create: <T>(entityType: string, data: Partial<T>) => {
    if (isDedicated(entityType)) {
      return api.post<T>(DEDICATED_ENDPOINTS[entityType], data).then((r) => r.data)
    }
    return api.post<T>(contentBase(entityType), data).then((r) => r.data)
  },
  update: <T>(entityType: string, id: string, data: Partial<T>) => {
    if (isDedicated(entityType)) {
      // Dedicated routers use PUT /{collection}/{id} or /{collection}/{code}.
      return api.put<T>(`${DEDICATED_ENDPOINTS[entityType]}/${id}`, data).then((r) => r.data)
    }
    return api.put<T>(`${contentBase(entityType)}/${id}`, data).then((r) => r.data)
  },
  delete: (entityType: string, id: string) => {
    if (isDedicated(entityType)) {
      return api.delete(`${DEDICATED_ENDPOINTS[entityType]}/${id}`)
    }
    return api.delete(`${contentBase(entityType)}/${id}`)
  },
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
    api.get<CMSDashboardOverview>('/cms/dashboard/overview').then((r) => r.data),
  getRecentActivity: (limit = 20) =>
    api.get<RecentActivity[]>('/cms/dashboard/recent-activity', { params: { limit } }).then((r) => r.data),
  getWorkflowSummary: () =>
    api.get<WorkflowSummary>('/cms/dashboard/workflow-summary').then((r) => r.data),

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
  // Paths aligned with backend/app/api/v1/cms/builder.py (path params, not
  // query params, for ids). getGroups reuses the existing /cms/question-groups
  // endpoint since the builder has no dedicated groups list route.
  builder: {
    getGroups: (templateId?: string) =>
      api.get<QuestionGroupWithQuestions[]>('/cms/question-groups', { params: { body_system_id: templateId } }).then((r) => r.data),
    reorderGroups: (groupIds: string[]) =>
      api.put('/cms/builder/groups/reorder', { group_ids: groupIds }),
    moveGroup: (groupId: string, direction: 'up' | 'down') =>
      api.put(`/cms/builder/groups/${groupId}/move`, { direction }),
    cloneQuestion: (questionId: string, groupId?: string) =>
      api.post<Question>(`/cms/builder/questions/${questionId}/clone`, undefined, { params: { target_group_id: groupId } }).then((r) => r.data),
    getDependencies: (questionId?: string) =>
      questionId
        ? api.get<DependencyRule[]>(`/cms/builder/questions/${questionId}/dependencies`).then((r) => r.data)
        : Promise.resolve([] as DependencyRule[]),
    createDependency: (data: Partial<DependencyRule>) =>
      api.post<DependencyRule>('/cms/builder/dependencies', data).then((r) => r.data),
    deleteDependency: (id: string) =>
      api.delete(`/cms/builder/dependencies/${id}`),
    getBranchRules: (bodySystemId?: string) =>
      bodySystemId
        ? api.get<BranchRule[]>(`/cms/builder/branch-rules/${bodySystemId}`).then((r) => r.data)
        : Promise.resolve([] as BranchRule[]),
    createBranchRule: (bodySystemId: string, data: Partial<BranchRule>) =>
      api.post<BranchRule[]>(`/cms/builder/branch-rules/${bodySystemId}`, [data]).then((r) => r.data),
    deleteBranchRule: (id: string) =>
      api.delete(`/cms/builder/branch-rules/${id}`),
    simulate: (templateId: string, answers: Record<string, unknown>) =>
      api.post(`/cms/builder/simulate/${templateId}`, { answers }).then((r) => r.data),
    getVersions: (templateId: string) =>
      api.get<BuilderVersion[]>(`/cms/builder/versions/${templateId}`).then((r) => r.data),
    createVersion: (templateId: string, reason?: string) =>
      api.post<BuilderVersion>(`/cms/builder/versions/${templateId}`, { snapshot: {}, reason }).then((r) => r.data),
  },

  // ---- Rule Engine ----
  rules: {
    getSets: () =>
      api.get<RuleSet[]>('/cms/rules').then((r) => r.data),
    getSet: (id: string) =>
      api.get<RuleSet>(`/cms/rules/${id}`).then((r) => r.data),
    createSet: (data: Partial<RuleSet>) =>
      api.post<RuleSet>('/cms/rules', data).then((r) => r.data),
    updateSet: (id: string, data: Partial<RuleSet>) =>
      api.put<RuleSet>(`/cms/rules/${id}`, data).then((r) => r.data),
    evaluate: (ruleSetId: string, context: Record<string, unknown>) =>
      api.post<RuleEvaluationResult[]>('/cms/rules/evaluate', { rule_set_id: ruleSetId, context }).then((r) => r.data),
    batchEvaluate: (evaluations: { rule_set_id: string; context: Record<string, unknown> }[]) =>
      api.post<RuleEvaluationResult[][]>('/cms/rules/batch-evaluate', { evaluations }).then((r) => r.data),
    simulate: (expression: unknown, context: Record<string, unknown>) =>
      api.post<RuleEvaluationResult>('/cms/rules/simulate', { expression, context }).then((r) => r.data),
    validate: (expression: unknown) =>
      api.post('/cms/rules/validate', { expression }).then((r) => r.data),
    compute: (bodySystemId: string, context: Record<string, unknown>) =>
      api.post('/cms/rules/compute', { body_system_id: bodySystemId, context }).then((r) => r.data),
    detectConflicts: (ruleIds: string[]) =>
      api.post<RuleConflict[]>('/cms/rules/detect-conflicts', { rule_ids: ruleIds }).then((r) => r.data),
  },

  // ---- Knowledge Graph ----
  knowledgeGraph: {
    listGraphs: (bodySystemId?: string) =>
      api.get<KnowledgeGraph[]>('/cms/knowledge-graph/graphs', { params: { body_system_id: bodySystemId } }).then((r) => r.data),
    createGraph: (data: Partial<KnowledgeGraph>) =>
      api.post<KnowledgeGraph>('/cms/knowledge-graph/graphs', data).then((r) => r.data),
    getGraph: (id: string) =>
      api.get(`/cms/knowledge-graph/graphs/${id}`).then((r) => r.data),
    updateGraph: (id: string, data: Partial<KnowledgeGraph>) =>
      api.put(`/cms/knowledge-graph/graphs/${id}`, data).then((r) => r.data),
    deleteGraph: (id: string) =>
      api.delete(`/cms/knowledge-graph/graphs/${id}`),
    addNode: (graphId: string, data: Record<string, unknown>) =>
      api.post(`/cms/knowledge-graph/graphs/${graphId}/nodes`, data).then((r) => r.data),
    updateNode: (nodeId: string, data: Record<string, unknown>) =>
      api.put(`/cms/knowledge-graph/graphs/nodes/${nodeId}`, data).then((r) => r.data),
    removeNode: (nodeId: string) =>
      api.delete(`/cms/knowledge-graph/graphs/nodes/${nodeId}`),
    addEdge: (graphId: string, data: Record<string, unknown>) =>
      api.post(`/cms/knowledge-graph/graphs/${graphId}/edges`, data).then((r) => r.data),
    removeEdge: (edgeId: string) =>
      api.delete(`/cms/knowledge-graph/graphs/edges/${edgeId}`),
    validateGraph: (graphId: string) =>
      api.post<GraphValidationResult>(`/cms/knowledge-graph/graphs/${graphId}/validate`).then((r) => r.data),
    analyzeImpact: (entityType: string, entityId: string) =>
      api.get<ImpactAnalysis>(`/cms/knowledge-graph/impact/${entityType}/${entityId}`).then((r) => r.data),
    searchEntities: (query: string, limit = 20) =>
      api.get<EntitySearchResult[]>('/cms/knowledge-graph/search', { params: { query, limit } }).then((r) => r.data),
    bulkLink: (data: { entity_type: string; source_ids: string[]; target_type: string; target_ids: string[]; relationship_type?: string }) =>
      api.post('/cms/knowledge-graph/bulk-link', data).then((r) => r.data),
  },

  // ---- Publishing ----
  publishing: {
    listWorkflows: (entityType?: string) =>
      api.get<Workflow[]>('/cms/publishing/workflows', { params: { entity_type: entityType } }).then((r) => r.data),
    createWorkflow: (data: Partial<Workflow>) =>
      api.post<Workflow>('/cms/publishing/workflows', data).then((r) => r.data),
    getWorkflow: (id: string) =>
      api.get<Workflow>(`/cms/publishing/workflows/${id}`).then((r) => r.data),
    updateWorkflow: (id: string, data: Partial<Workflow>) =>
      api.put<Workflow>(`/cms/publishing/workflows/${id}`, data).then((r) => r.data),
    listJobs: (status?: string, entityType?: string) =>
      api.get<PublishingJob[]>('/cms/publishing/jobs', { params: { status, entity_type: entityType } }).then((r) => r.data),
    createJob: (data: Partial<PublishingJob>) =>
      api.post<PublishingJob>('/cms/publishing/jobs', data).then((r) => r.data),
    getJob: (id: string) =>
      api.get<PublishingJob>(`/cms/publishing/jobs/${id}`).then((r) => r.data),
    approveJob: (id: string) =>
      api.post(`/cms/publishing/jobs/${id}/approve`).then((r) => r.data),
    executePublish: (id: string) =>
      api.post(`/cms/publishing/jobs/${id}/publish`).then((r) => r.data),
    failJob: (id: string, reason: string) =>
      api.post(`/cms/publishing/jobs/${id}/fail`, { reason }).then((r) => r.data),
    rollbackJob: (id: string, version: number) =>
      api.post(`/cms/publishing/jobs/${id}/rollback`, { rollback_version: version }).then((r) => r.data),
    processScheduled: () =>
      api.post('/cms/publishing/jobs/process-scheduled').then((r) => r.data),
    listApprovals: (status?: string, entityType?: string) =>
      api.get<Approval[]>('/cms/publishing/approvals', { params: { status, entity_type: entityType } }).then((r) => r.data),
    createApproval: (data: Partial<Approval>) =>
      api.post<Approval>('/cms/publishing/approvals', data).then((r) => r.data),
    approveEntity: (id: string, comment?: string) =>
      api.post(`/cms/publishing/approvals/${id}/approve`, { comment }).then((r) => r.data),
    rejectApproval: (id: string, reason: string) =>
      api.post(`/cms/publishing/approvals/${id}/reject`, { reason }).then((r) => r.data),
    addApprovalComment: (id: string, comment: string) =>
      api.post(`/cms/publishing/approvals/${id}/comment`, { comment }).then((r) => r.data),
    listReviews: (status?: string, entityType?: string) =>
      api.get<Review[]>('/cms/publishing/reviews', { params: { status, entity_type: entityType } }).then((r) => r.data),
    createReview: (data: Partial<Review>) =>
      api.post<Review>('/cms/publishing/reviews', data).then((r) => r.data),
    completeReview: (id: string, decision: string, comments?: string, score?: number) =>
      api.post(`/cms/publishing/reviews/${id}/complete`, { decision, comments, score }).then((r) => r.data),
    listChangeRequests: (status?: string, entityType?: string) =>
      api.get<ChangeRequest[]>('/cms/publishing/change-requests', { params: { status, entity_type: entityType } }).then((r) => r.data),
    createChangeRequest: (data: Partial<ChangeRequest>) =>
      api.post<ChangeRequest>('/cms/publishing/change-requests', data).then((r) => r.data),
    approveChangeRequest: (id: string) =>
      api.post(`/cms/publishing/change-requests/${id}/approve`).then((r) => r.data),
    rejectChangeRequest: (id: string, reason: string) =>
      api.post(`/cms/publishing/change-requests/${id}/reject`, { reason }).then((r) => r.data),
    detectConflicts: (entityType: string, entityId: string) =>
      api.get('/cms/publishing/change-requests/conflicts', { params: { entity_type: entityType, entity_id: entityId } }).then((r) => r.data),
    listSnapshots: (entityType: string, entityId: string) =>
      api.get<VersionSnapshot[]>('/cms/publishing/snapshots', { params: { entity_type: entityType, entity_id: entityId } }).then((r) => r.data),
    createSnapshot: (data: Partial<VersionSnapshot>) =>
      api.post<VersionSnapshot>('/cms/publishing/snapshots', data).then((r) => r.data),
  },

  // ---- Audit ----
  audit: {
    search: (params?: Record<string, unknown>) =>
      api.get<{ items: AuditLogEntry[]; total: number; skip: number; limit: number }>('/cms/audit/logs', { params }).then((r) => r.data),
    getTimeline: (entityType: string, entityId: string) =>
      api.get<AuditLogEntry[]>(`/cms/audit/timeline/${entityType}/${entityId}`).then((r) => r.data),
    getDiffs: (entityType: string, entityId: string) =>
      api.get<AuditDiff[]>(`/cms/audit/diffs/${entityType}/${entityId}`).then((r) => r.data),
    export: (entityType?: string, format = 'json') =>
      api.get('/cms/audit/export', { params: { entity_type: entityType, format }, responseType: format === 'csv' ? 'blob' : 'json' }).then((r) => r.data),
    getStats: (days = 30) =>
      api.get<AuditStats>('/cms/audit/stats', { params: { days } }).then((r) => r.data),
  },

  // ---- Users & Roles ----
  users: {
    list: (params?: Record<string, unknown>) =>
      api.get<PaginatedResponse<UserProfile>>('/admin/users', { params }).then((r) => r.data),
    getById: (id: string) =>
      api.get<UserProfile>(`/admin/users/${id}`).then((r) => r.data),
    updateRoles: (userId: string, roles: string[]) =>
      api.put(`/admin/users/${userId}/roles`, { roles }).then((r) => r.data),
    toggleActive: (userId: string) =>
      api.post(`/admin/users/${userId}/toggle-active`).then((r) => r.data),
  },
  roles: {
    list: () =>
      api.get<UserRole[]>('/admin/roles').then((r) => r.data),
    create: (data: Partial<UserRole>) =>
      api.post<UserRole>('/admin/roles', data).then((r) => r.data),
    update: (id: string, data: Partial<UserRole>) =>
      api.put<UserRole>(`/admin/roles/${id}`, data).then((r) => r.data),
    getPermissions: (roleId: string) =>
      api.get<string[]>(`/admin/roles/${roleId}/permissions`).then((r) => r.data),
    updatePermissions: (roleId: string, permissions: string[]) =>
      api.put(`/admin/roles/${roleId}/permissions`, { permissions }).then((r) => r.data),
  },

  // ---- Search ----
  search: (query: string, entityType?: string, limit = 50) =>
    api.get('/cms/content/search', { params: { query, entity_type: entityType, limit } }).then((r) => r.data),
}
