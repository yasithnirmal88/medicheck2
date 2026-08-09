import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { cmsApi, contentApi } from '../api/cmsApi'
import type {
  Approval, AuditDiff, AuditLogEntry, AuditStats, BodySystem,
  ChangeRequest, ClinicalIndicator, CMSDashboardOverview,
  Disease, EntityType, EvidenceReference, GraphValidationResult,
  ImagingTest, KnowledgeGraph, LaboratoryTest, PaginatedResponse,
  PublishingJob, Question, QuestionGroup, Recommendation,
  RecentActivity, Review, RuleSet, Symptom, Template, UserProfile,
  UserRole, VersionSnapshot, Workflow, WorkflowSummary,
} from '../types'

// ---- Dashboard ----
export function useDashboardOverview() {
  return useQuery<CMSDashboardOverview>({
    queryKey: ['cms', 'dashboard', 'overview'],
    queryFn: cmsApi.getDashboardOverview,
  })
}

export function useRecentActivity(limit = 20) {
  return useQuery<RecentActivity[]>({
    queryKey: ['cms', 'dashboard', 'recent-activity', limit],
    queryFn: () => cmsApi.getRecentActivity(limit),
  })
}

export function useWorkflowSummary() {
  return useQuery<WorkflowSummary>({
    queryKey: ['cms', 'dashboard', 'workflow-summary'],
    queryFn: cmsApi.getWorkflowSummary,
  })
}

// ---- Generic Content ----
function contentQueryKey(entityType: string, ...rest: unknown[]) {
  return ['cms', 'content', entityType, ...rest]
}

export function useContentList<T>(entityType: EntityType, params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<T>>({
    queryKey: contentQueryKey(entityType, 'list', params),
    queryFn: () => contentApi.list<T>(entityType, params),
  })
}

export function useContentItem<T>(entityType: EntityType, id: string | undefined) {
  return useQuery<T | null>({
    queryKey: contentQueryKey(entityType, id),
    queryFn: () => (id ? contentApi.getById<T>(entityType, id) : null),
    enabled: !!id,
  })
}

export function useCreateContent<T>(entityType: EntityType) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<T>) => contentApi.create<T>(entityType, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: contentQueryKey(entityType) })
      toast.success(`${entityType} created`)
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err?.response?.data?.detail || `Failed to create ${entityType}`)
    },
  })
}

export function useUpdateContent<T>(entityType: EntityType) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<T> }) => contentApi.update<T>(entityType, id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: contentQueryKey(entityType) })
      toast.success(`${entityType} updated`)
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err?.response?.data?.detail || `Failed to update ${entityType}`)
    },
  })
}

export function useDeleteContent(entityType: EntityType) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => contentApi.delete(entityType, id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: contentQueryKey(entityType) })
      toast.success(`${entityType} deleted`)
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err?.response?.data?.detail || `Failed to delete ${entityType}`)
    },
  })
}

// ---- Specific entity hooks ----
export function useQuestions(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<Question>>({
    queryKey: ['cms', 'questions', params],
    queryFn: () => cmsApi.questions.list(params),
  })
}

export function useQuestionGroups(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<QuestionGroup>>({
    queryKey: ['cms', 'question-groups', params],
    queryFn: () => cmsApi.questionGroups.list(params),
  })
}

export function useDiseases(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<Disease>>({
    queryKey: ['cms', 'diseases', params],
    queryFn: () => cmsApi.diseases.list(params),
  })
}

export function useBodySystems(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<BodySystem>>({
    queryKey: ['cms', 'body-systems', params],
    queryFn: () => cmsApi.bodySystems.list(params),
  })
}

export function useSymptoms(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<Symptom>>({
    queryKey: ['cms', 'symptoms', params],
    queryFn: () => cmsApi.symptoms.list(params),
  })
}

export function useIndicators(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<ClinicalIndicator>>({
    queryKey: ['cms', 'indicators', params],
    queryFn: () => cmsApi.indicators.list(params),
  })
}

export function useLabTests(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<LaboratoryTest>>({
    queryKey: ['cms', 'lab-tests', params],
    queryFn: () => cmsApi.labTests.list(params),
  })
}

export function useImagingTests(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<ImagingTest>>({
    queryKey: ['cms', 'imaging-tests', params],
    queryFn: () => cmsApi.imagingTests.list(params),
  })
}

export function useRecommendations(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<Recommendation>>({
    queryKey: ['cms', 'recommendations', params],
    queryFn: () => cmsApi.recommendations.list(params),
  })
}

export function useTemplates(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<Template>>({
    queryKey: ['cms', 'templates', params],
    queryFn: () => cmsApi.templates.list(params),
  })
}

export function useEvidenceReferences(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<EvidenceReference>>({
    queryKey: ['cms', 'evidence-references', params],
    queryFn: () => cmsApi.evidenceReferences.list(params),
  })
}

// ---- Knowledge Graph ----
export function useKnowledgeGraphs(bodySystemId?: string) {
  return useQuery<KnowledgeGraph[]>({
    queryKey: ['cms', 'kg', 'graphs', bodySystemId],
    queryFn: () => cmsApi.knowledgeGraph.listGraphs(bodySystemId),
  })
}

export function useKnowledgeGraphDetail(id: string | undefined) {
  return useQuery({
    queryKey: ['cms', 'kg', 'graph', id],
    queryFn: () => cmsApi.knowledgeGraph.getGraph(id!),
    enabled: !!id,
  })
}

export function useValidateGraph(id: string) {
  return useMutation({
    mutationFn: () => cmsApi.knowledgeGraph.validateGraph(id),
    onSuccess: (data: GraphValidationResult) => {
      if (data.is_valid) toast.success('Graph is valid')
      else toast.error(`Graph has ${data.issues.length + data.cycle_count} issues`)
    },
  })
}

// ---- Rules ----
export function useRuleSets() {
  return useQuery<RuleSet[]>({
    queryKey: ['cms', 'rules'],
    queryFn: () => cmsApi.rules.getSets(),
  })
}

export function useEvaluateRule() {
  return useMutation({
    mutationFn: ({ ruleSetId, context }: { ruleSetId: string; context: Record<string, unknown> }) =>
      cmsApi.rules.evaluate(ruleSetId, context),
  })
}

export function useDetectRuleConflicts() {
  return useMutation({
    mutationFn: (ruleIds: string[]) => cmsApi.rules.detectConflicts(ruleIds),
  })
}

// ---- Publishing ----
export function usePublishingJobs(status?: string, entityType?: string) {
  return useQuery<PublishingJob[]>({
    queryKey: ['cms', 'publishing', 'jobs', status, entityType],
    queryFn: () => cmsApi.publishing.listJobs(status, entityType),
  })
}

export function useApproveJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => cmsApi.publishing.approveJob(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cms', 'publishing'] }); toast.success('Job approved') },
  })
}

export function usePublishJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => cmsApi.publishing.executePublish(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cms', 'publishing'] }); toast.success('Published') },
  })
}

export function useRollbackJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, version }: { id: string; version: number }) => cmsApi.publishing.rollbackJob(id, version),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cms', 'publishing'] }); toast.success('Rolled back') },
  })
}

export function useWorkflows(entityType?: string) {
  return useQuery<Workflow[]>({
    queryKey: ['cms', 'workflows', entityType],
    queryFn: () => cmsApi.publishing.listWorkflows(entityType),
  })
}

export function useApprovals(status?: string, entityType?: string) {
  return useQuery<Approval[]>({
    queryKey: ['cms', 'approvals', status, entityType],
    queryFn: () => cmsApi.publishing.listApprovals(status, entityType),
  })
}

export function useReviews(status?: string, entityType?: string) {
  return useQuery<Review[]>({
    queryKey: ['cms', 'reviews', status, entityType],
    queryFn: () => cmsApi.publishing.listReviews(status, entityType),
  })
}

export function useChangeRequests(status?: string, entityType?: string) {
  return useQuery<ChangeRequest[]>({
    queryKey: ['cms', 'change-requests', status, entityType],
    queryFn: () => cmsApi.publishing.listChangeRequests(status, entityType),
  })
}

export function useSnapshots(entityType: string, entityId: string) {
  return useQuery<VersionSnapshot[]>({
    queryKey: ['cms', 'snapshots', entityType, entityId],
    queryFn: () => cmsApi.publishing.listSnapshots(entityType, entityId),
    enabled: !!entityType && !!entityId,
  })
}

// ---- Audit ----
export function useAuditLogs(params?: Record<string, unknown>) {
  return useQuery<{ items: AuditLogEntry[]; total: number }>({
    queryKey: ['cms', 'audit', params],
    queryFn: () => cmsApi.audit.search(params),
  })
}

export function useAuditTimeline(entityType: string, entityId: string) {
  return useQuery<AuditLogEntry[]>({
    queryKey: ['cms', 'audit', 'timeline', entityType, entityId],
    queryFn: () => cmsApi.audit.getTimeline(entityType, entityId),
    enabled: !!entityType && !!entityId,
  })
}

export function useAuditDiffs(entityType: string, entityId: string) {
  return useQuery<AuditDiff[]>({
    queryKey: ['cms', 'audit', 'diffs', entityType, entityId],
    queryFn: () => cmsApi.audit.getDiffs(entityType, entityId),
    enabled: !!entityType && !!entityId,
  })
}

export function useAuditStats(days = 30) {
  return useQuery<AuditStats>({
    queryKey: ['cms', 'audit', 'stats', days],
    queryFn: () => cmsApi.audit.getStats(days),
  })
}

// ---- Users & Roles ----
export function useUsers(params?: Record<string, unknown>) {
  return useQuery<PaginatedResponse<UserProfile>>({
    queryKey: ['cms', 'users', params],
    queryFn: () => cmsApi.users.list(params),
  })
}

export function useRoles() {
  return useQuery<UserRole[]>({
    queryKey: ['cms', 'roles'],
    queryFn: () => cmsApi.roles.list(),
  })
}

export function useUpdateUserRoles() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, roles }: { userId: string; roles: string[] }) => cmsApi.users.updateRoles(userId, roles),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cms', 'users'] }); toast.success('Roles updated') },
  })
}

// ---- Builder ----
export function useBuilderGroups(templateId?: string) {
  return useQuery({
    queryKey: ['cms', 'builder', 'groups', templateId],
    queryFn: () => cmsApi.builder.getGroups(templateId),
  })
}

export function useBuilderVersions(templateId: string) {
  return useQuery({
    queryKey: ['cms', 'builder', 'versions', templateId],
    queryFn: () => cmsApi.builder.getVersions(templateId),
    enabled: !!templateId,
  })
}

export function useCloneQuestion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ questionId, groupId }: { questionId: string; groupId?: string }) =>
      cmsApi.builder.cloneQuestion(questionId, groupId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cms', 'builder'] }); toast.success('Question cloned') },
  })
}

export function useReorderGroups() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (groupIds: string[]) => cmsApi.builder.reorderGroups(groupIds),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cms', 'builder'] }); toast.success('Groups reordered') },
  })
}
