/**
 * DEMO-ONLY fabricated data for the Assessment Results page.
 *
 * This module exists solely to support an EXPLICIT, OPT-IN demo mode. It is
 * NEVER shown by default and never overrides a real report. When it is shown,
 * the page renders a prominent "Demo data – not real clinical results" banner.
 *
 * Enable with either:
 *   - build-time:  VITE_DEMO_MODE=true
 *   - runtime:     append ?demo=1 to the page URL
 *
 * Real clinical results come exclusively from the report API. Do NOT import
 * these values into any production rendering path.
 */
import type { ReportDetail } from '../types/report'

export const DEMO_HEALTH_REPORT: ReportDetail = {
  id: 'demo-report',
  session_id: 'demo-session',
  summary: 'Synthetic demonstration report. Not produced by the clinical engine.',
  created_at: '2026-01-01T00:00:00Z',
  body_systems: [
    { id: 'demo-bs-1', body_system_id: 'bs_cardiovascular', category: 'Monitor', score: '2.0' },
    { id: 'demo-bs-2', body_system_id: 'bs_metabolic', category: 'Needs Attention', score: '4.0' },
  ],
  conditions: [
    { id: 'demo-cond-1', condition_id: 'cond_hypertension_risk', score: '3.0', confidence: 'Moderate' },
  ],
  advices: [
    { id: 'demo-adv-1', category: 'Activity', text: 'Sample recommendation for demonstration only.' },
  ],
  lifestyle: [{ id: 'demo-ls-1', data: '{"lifestyle":"Demo lifestyle snapshot"}' }],
}

/**
 * Whether the demo mode flag is enabled. Default is OFF; real data only.
 *
 * The env value is read defensively via a cast so an unset `VITE_DEMO_MODE`
 * (the normal case) is simply `undefined`.
 */
export function isResultsDemoMode(): boolean {
  const env = import.meta.env as Record<string, string | undefined>
  if (env.VITE_DEMO_MODE === 'true') return true

  if (typeof window !== 'undefined') {
    const flag = new URLSearchParams(window.location.search).get('demo')
    return flag === '1' || flag === 'true'
  }
  return false
}
