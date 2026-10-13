import type { EntityType } from '../types'

const CONTENT_LIST_PATHS: Partial<Record<EntityType, string>> = {
  question: '/cms/questions',
  question_group: '/cms/question-groups',
  disease: '/cms/diseases',
  body_system: '/cms/body-systems',
  symptom: '/cms/symptoms',
  indicator: '/cms/indicators',
  lab_test: '/cms/lab-tests',
  imaging: '/cms/imaging',
  recommendation: '/cms/recommendations',
  lifestyle: '/cms/lifestyle',
  exercise: '/cms/exercise',
  nutrition: '/cms/nutrition',
  evidence: '/cms/evidence',
  template: '/cms/templates',
  medication: '/cms/medications',
  guideline: '/cms/guidelines',
  rule: '/cms/rules',
  severity_threshold: '/cms/thresholds',
}

export function getContentListPath(entityType: EntityType): string {
  return CONTENT_LIST_PATHS[entityType] ?? `/cms/content/${entityType}`
}
