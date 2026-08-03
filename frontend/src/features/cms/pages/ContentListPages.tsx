import React from 'react'
import { ContentListPage } from './ContentListPage'
import { StatusBadge } from '../components/ContentLayout'
import type { Column } from '../components/ContentLayout'
import type {
  Question, Disease, BodySystem, Symptom, ClinicalIndicator,
  LaboratoryTest, ImagingTest, Recommendation, LifestyleAdvice,
  ExerciseProgram, NutritionAdvice, Template,
  ClinicalGuideline, MedicationRecommendation, DecisionRule,
  SeverityThreshold, EvidenceReference,
} from '../types'
import type { EntityType } from '../types'

function dateCell(value: string) {
  return <span className="text-slate-500 dark:text-slate-400 text-xs">{new Date(value).toLocaleDateString()}</span>
}

function statusCell(value: string) {
  return <StatusBadge status={value} />
}

function bodySystemCell(value: string | null | undefined) {
  return value ? (
    <span className="text-xs font-mono text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">{value.slice(0, 8)}</span>
  ) : (
    <span className="text-xs text-slate-400">—</span>
  )
}

function codeCell(value: string) {
  return <span className="font-mono text-xs font-medium text-slate-700 dark:text-slate-300">{value}</span>
}

function nameCell(value: string) {
  return <span className="font-medium text-slate-900 dark:text-white">{value}</span>
}

function textCell(value: string) {
  return <span className="text-xs text-slate-600 dark:text-slate-400 line-clamp-1">{value}</span>
}

// ---- Entity list pages ----
type ListPage = React.FC

function makeListPage<T extends { id: string }>(
  entityType: EntityType, title: string, description: string,
  columns: Column<T>[], basePath?: string,
): ListPage {
  const Page: ListPage = () => (
    <ContentListPage<T>
      entityType={entityType}
      columns={columns}
      title={title}
      description={description}
      basePath={basePath}
    />
  )
  Page.displayName = `${title.replace(/\s+/g, '')}ListPage`
  return Page
}

export const QuestionsListPage = makeListPage<Question>('question', 'Questions', 'Manage clinical questions and their options', [
  { key: 'code', header: 'Code', render: (q) => codeCell(q.code) },
  { key: 'text', header: 'Question', render: (q) => nameCell(q.text) },
  { key: 'body_system_id', header: 'Body System', render: (q) => bodySystemCell(q.body_system_id) },
  { key: 'question_type', header: 'Type', render: (q) => <span className="text-xs capitalize text-slate-500">{q.question_type}</span> },
  { key: 'status', header: 'Status', render: (q) => statusCell(q.status) },
  { key: 'created_at', header: 'Created', render: (q) => dateCell(q.created_at) },
])

export const DiseasesListPage = makeListPage<Disease>('disease', 'Diseases', 'Medical conditions and disease definitions', [
  { key: 'name', header: 'Name', render: (d) => nameCell(d.name) },
  { key: 'icd10_code', header: 'ICD-10', render: (d) => d.icd10_code ? codeCell(d.icd10_code) : <span className="text-xs text-slate-400">—</span> },
  { key: 'body_system_id', header: 'Body System', render: (d) => bodySystemCell(d.body_system_id) },
  { key: 'severity', header: 'Severity', render: (d) => d.severity ? <span className="text-xs capitalize text-slate-500">{d.severity}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'status', header: 'Status', render: (d) => statusCell(d.status) },
  { key: 'created_at', header: 'Created', render: (d) => dateCell(d.created_at) },
])

export const BodySystemsListPage = makeListPage<BodySystem>('body_system', 'Body Systems', 'Organ systems used for risk categorization', [
  { key: 'code', header: 'Code', render: (bs) => codeCell(bs.code) },
  { key: 'name', header: 'Name', render: (bs) => nameCell(bs.name) },
  { key: 'description', header: 'Description', render: (bs) => textCell(bs.description || '') },
  { key: 'status', header: 'Status', render: (bs) => statusCell(bs.status) },
  { key: 'created_at', header: 'Created', render: (bs) => dateCell(bs.created_at) },
])

export const SymptomsListPage = makeListPage<Symptom>('symptom', 'Symptoms', 'Clinical symptoms and patient-reported complaints', [
  { key: 'code', header: 'Code', render: (s) => codeCell(s.code) },
  { key: 'name', header: 'Name', render: (s) => nameCell(s.name) },
  { key: 'body_system_id', header: 'Body System', render: (s) => bodySystemCell(s.body_system_id) },
  { key: 'severity', header: 'Severity', render: (s) => s.severity ? <span className="text-xs capitalize text-slate-500">{s.severity}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'status', header: 'Status', render: (s) => statusCell(s.status) },
  { key: 'created_at', header: 'Created', render: (s) => dateCell(s.created_at) },
])

export const IndicatorsListPage = makeListPage<ClinicalIndicator>('indicator', 'Clinical Indicators', 'Measurable clinical signs and risk factors', [
  { key: 'code', header: 'Code', render: (i) => codeCell(i.code) },
  { key: 'name', header: 'Name', render: (i) => nameCell(i.name) },
  { key: 'body_system_id', header: 'Body System', render: (i) => bodySystemCell(i.body_system_id) },
  { key: 'indicator_type', header: 'Type', render: (i) => i.indicator_type ? <span className="text-xs capitalize text-slate-500">{i.indicator_type}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'status', header: 'Status', render: (i) => statusCell(i.status) },
  { key: 'created_at', header: 'Created', render: (i) => dateCell(i.created_at) },
])

export const LabTestsListPage = makeListPage<LaboratoryTest>('lab_test', 'Lab Tests', 'Laboratory test definitions and reference ranges', [
  { key: 'code', header: 'Code', render: (lt) => codeCell(lt.code) },
  { key: 'name', header: 'Name', render: (lt) => nameCell(lt.name) },
  { key: 'loinc_code', header: 'LOINC', render: (lt) => lt.loinc_code ? codeCell(lt.loinc_code) : <span className="text-xs text-slate-400">—</span> },
  { key: 'body_system_id', header: 'Body System', render: (lt) => bodySystemCell(lt.body_system_id) },
  { key: 'status', header: 'Status', render: (lt) => statusCell(lt.status) },
  { key: 'created_at', header: 'Created', render: (lt) => dateCell(lt.created_at) },
])

export const ImagingTestsListPage = makeListPage<ImagingTest>('imaging', 'Imaging Tests', 'Medical imaging and radiology procedures', [
  { key: 'code', header: 'Code', render: (it) => codeCell(it.code) },
  { key: 'name', header: 'Name', render: (it) => nameCell(it.name) },
  { key: 'modality', header: 'Modality', render: (it) => it.modality ? <span className="text-xs capitalize text-slate-500">{it.modality}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'body_system_id', header: 'Body System', render: (it) => bodySystemCell(it.body_system_id) },
  { key: 'status', header: 'Status', render: (it) => statusCell(it.status) },
  { key: 'created_at', header: 'Created', render: (it) => dateCell(it.created_at) },
])

export const RecommendationsListPage = makeListPage<Recommendation>('recommendation', 'Recommendations', 'Clinical recommendations and treatment plans', [
  { key: 'code', header: 'Code', render: (r) => codeCell(r.code) },
  { key: 'title', header: 'Title', render: (r) => nameCell(r.title) },
  { key: 'recommendation_type', header: 'Type', render: (r) => r.recommendation_type ? <span className="text-xs capitalize text-slate-500">{r.recommendation_type}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'urgency', header: 'Urgency', render: (r) => r.urgency ? <span className="text-xs capitalize font-medium text-slate-600">{r.urgency}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'status', header: 'Status', render: (r) => statusCell(r.status) },
  { key: 'created_at', header: 'Created', render: (r) => dateCell(r.created_at) },
])

export const LifestyleAdviceListPage = makeListPage<LifestyleAdvice>('lifestyle', 'Lifestyle Advice', 'Lifestyle recommendations for patients', [
  { key: 'code', header: 'Code', render: (la) => codeCell(la.code) },
  { key: 'name', header: 'Name', render: (la) => nameCell(la.name) },
  { key: 'category', header: 'Category', render: (la) => la.category ? <span className="text-xs capitalize text-slate-500">{la.category}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'body_system_id', header: 'Body System', render: (la) => bodySystemCell(la.body_system_id) },
  { key: 'status', header: 'Status', render: (la) => statusCell(la.status) },
  { key: 'created_at', header: 'Created', render: (la) => dateCell(la.created_at) },
])

export const ExerciseProgramsListPage = makeListPage<ExerciseProgram>('exercise', 'Exercise Programs', 'Exercise and physical activity programs', [
  { key: 'code', header: 'Code', render: (ep) => codeCell(ep.code) },
  { key: 'name', header: 'Name', render: (ep) => nameCell(ep.name) },
  { key: 'difficulty_level', header: 'Difficulty', render: (ep) => ep.difficulty_level ? <span className="text-xs capitalize text-slate-500">{ep.difficulty_level}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'duration_minutes', header: 'Duration', render: (ep) => ep.duration_minutes ? <span className="text-xs text-slate-500">{ep.duration_minutes}m</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'status', header: 'Status', render: (ep) => statusCell(ep.status) },
  { key: 'created_at', header: 'Created', render: (ep) => dateCell(ep.created_at) },
])

export const NutritionAdviceListPage = makeListPage<NutritionAdvice>('nutrition', 'Nutrition Advice', 'Dietary and nutrition recommendations', [
  { key: 'code', header: 'Code', render: (na) => codeCell(na.code) },
  { key: 'name', header: 'Name', render: (na) => nameCell(na.name) },
  { key: 'meal_type', header: 'Meal Type', render: (na) => na.meal_type ? <span className="text-xs capitalize text-slate-500">{na.meal_type}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'calories', header: 'Calories', render: (na) => na.calories ? <span className="text-xs text-slate-500">{na.calories} kcal</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'status', header: 'Status', render: (na) => statusCell(na.status) },
  { key: 'created_at', header: 'Created', render: (na) => dateCell(na.created_at) },
])

export const EvidenceListPage = makeListPage<EvidenceReference>('evidence', 'Evidence References', 'PubMed and clinical evidence references', [
  { key: 'title', header: 'Title', render: (e) => nameCell(e.title) },
  { key: 'evidence_level', header: 'Level', render: (e) => e.evidence_level ? <span className="text-xs font-medium text-slate-600">{e.evidence_level}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'pmid', header: 'PMID', render: (e) => e.pmid ? codeCell(e.pmid) : <span className="text-xs text-slate-400">—</span> },
  { key: 'confidence_score', header: 'Confidence', render: (e) => e.confidence_score != null ? <span className="text-xs text-slate-500">{e.confidence_score}%</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'created_at', header: 'Created', render: (e) => dateCell(e.created_at) },
])

export const TemplatesListPage = makeListPage<Template>('template', 'Templates', 'Questionnaire templates and forms', [
  { key: 'code', header: 'Code', render: (t) => codeCell(t.code) },
  { key: 'name', header: 'Name', render: (t) => nameCell(t.name) },
  { key: 'body_system_id', header: 'Body System', render: (t) => bodySystemCell(t.body_system_id) },
  { key: 'version', header: 'Version', render: (t) => <span className="text-xs text-slate-500">v{t.version}</span> },
  { key: 'status', header: 'Status', render: (t) => statusCell(t.status) },
  { key: 'created_at', header: 'Created', render: (t) => dateCell(t.created_at) },
])

export const MedicationsListPage = makeListPage<MedicationRecommendation>('medication', 'Medications', 'Medication recommendations and formularies', [
  { key: 'code', header: 'Code', render: (m) => codeCell(m.code) },
  { key: 'name', header: 'Name', render: (m) => nameCell(m.name) },
  { key: 'generic_name', header: 'Generic', render: (m) => m.generic_name ? textCell(m.generic_name) : <span className="text-xs text-slate-400">—</span> },
  { key: 'dosage', header: 'Dosage', render: (m) => m.dosage ? <span className="text-xs text-slate-500">{m.dosage}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'status', header: 'Status', render: (m) => statusCell(m.status) },
  { key: 'created_at', header: 'Created', render: (m) => dateCell(m.created_at) },
])

export const ClinicalGuidelinesListPage = makeListPage<ClinicalGuideline>('guideline', 'Clinical Guidelines', 'Evidence-based clinical practice guidelines', [
  { key: 'code', header: 'Code', render: (cg) => codeCell(cg.code) },
  { key: 'title', header: 'Title', render: (cg) => nameCell(cg.title) },
  { key: 'organization', header: 'Organization', render: (cg) => cg.organization ? textCell(cg.organization) : <span className="text-xs text-slate-400">—</span> },
  { key: 'evidence_level', header: 'Evidence Level', render: (cg) => cg.evidence_level ? <span className="text-xs font-medium text-slate-600">{cg.evidence_level}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'status', header: 'Status', render: (cg) => statusCell(cg.status) },
  { key: 'created_at', header: 'Created', render: (cg) => dateCell(cg.created_at) },
])

export const DecisionRulesListPage = makeListPage<DecisionRule>('rule', 'Decision Rules', 'Clinical decision rules for risk assessment', [
  { key: 'code', header: 'Code', render: (dr) => codeCell(dr.code) },
  { key: 'name', header: 'Name', render: (dr) => nameCell(dr.name) },
  { key: 'body_system_id', header: 'Body System', render: (dr) => bodySystemCell(dr.body_system_id) },
  { key: 'rule_type', header: 'Type', render: (dr) => dr.rule_type ? <span className="text-xs capitalize text-slate-500">{dr.rule_type}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'status', header: 'Status', render: (dr) => statusCell(dr.status) },
  { key: 'created_at', header: 'Created', render: (dr) => dateCell(dr.created_at) },
])

export const SeverityThresholdsListPage = makeListPage<SeverityThreshold>('severity_threshold', 'Severity Thresholds', 'Severity thresholds and alert levels', [
  { key: 'code', header: 'Code', render: (st) => codeCell(st.code) },
  { key: 'name', header: 'Name', render: (st) => nameCell(st.name) },
  { key: 'severity_level', header: 'Level', render: (st) => st.severity_level ? <span className="text-xs capitalize font-medium text-slate-600">{st.severity_level}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'min_value', header: 'Min', render: (st) => st.min_value != null ? <span className="text-xs text-slate-500">{st.min_value}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'max_value', header: 'Max', render: (st) => st.max_value != null ? <span className="text-xs text-slate-500">{st.max_value}</span> : <span className="text-xs text-slate-400">—</span> },
  { key: 'status', header: 'Status', render: (st) => statusCell(st.status) },
  { key: 'created_at', header: 'Created', render: (st) => dateCell(st.created_at) },
])
