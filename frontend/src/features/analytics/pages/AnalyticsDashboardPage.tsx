/**
 * Phase 6 — Population Health + SDG Analytics Dashboard page.
 *
 * Renders de-identified, aggregated population metrics for authorized
 * analytics users (RESEARCH_REVIEWER+). All values are small-cell-suppressed
 * by the backend; suppressed cohorts show "Suppressed" rather than a count.
 */
import React, { useState } from 'react'
import { Activity, Users, TrendingUp, Globe, Mic, HeartPulse } from 'lucide-react'
import {
  useAnalyticsOverview,
  useSeverityDistribution,
  useTrajectoryDistribution,
  useAccessibilityMetrics,
  useSDGDashboard,
} from '../hooks/useAnalyticsQueries'

const SuppressedBadge: React.FC = () => (
  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
    Suppressed
  </span>
)

const MetricCard: React.FC<{
  label: string
  value: number | null
  suppressed?: boolean
  icon: React.ComponentType<{ className?: string }>
  color: string
}> = ({ label, value, suppressed, icon: Icon, color }) => (
  <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4">
    <div className="flex items-center justify-between">
      <span className={`p-2 rounded-lg ${color}`}>
        <Icon className="h-5 w-5" />
      </span>
      {suppressed && <SuppressedBadge />}
    </div>
    <p className="mt-3 text-2xl font-bold text-slate-900 dark:text-white">
      {suppressed ? '—' : value?.toLocaleString() ?? '—'}
    </p>
    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{label}</p>
  </div>
)

const SectionCard: React.FC<{
  title: string
  disclaimer?: string
  children: React.ReactNode
}> = ({ title, disclaimer, children }) => (
  <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5">
    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{title}</h3>
    {disclaimer && (
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 italic">{disclaimer}</p>
    )}
    <div className="mt-4">{children}</div>
  </div>
)

const Bar: React.FC<{ label: string; count: number; max: number; suppressed: boolean; percentage?: number | null }> = ({
  label, count, max, suppressed, percentage,
}) => {
  const width = suppressed ? 0 : max > 0 ? Math.max((count / max) * 100, 2) : 0
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="w-40 text-sm text-slate-600 dark:text-slate-400 truncate">{label}</span>
      <div className="flex-1 h-6 bg-slate-100 dark:bg-slate-800 rounded overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded transition-all"
          style={{ width: `${width}%` }}
        />
      </div>
      <span className="w-24 text-right text-sm font-medium text-slate-900 dark:text-white">
        {suppressed ? <SuppressedBadge /> : `${count}${percentage != null ? ` (${percentage}%)` : ''}`}
      </span>
    </div>
  )
}

export const AnalyticsDashboardPage: React.FC = () => {
  const [language, setLanguage] = useState<string>('')

  const filters = language ? { language } : undefined

  const overview = useAnalyticsOverview(filters)
  const severity = useSeverityDistribution(filters)
  const trajectory = useTrajectoryDistribution(filters)
  const accessibility = useAccessibilityMetrics(filters)
  const sdg = useSDGDashboard(filters)

  const ov = overview.data?.overview
  const sevMax = Math.max(1, ...(severity.data?.distribution ?? []).map((d) => d.count))

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Population Health & SDG Analytics
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            De-identified, aggregated population metrics. Small cohorts are suppressed for privacy.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="lang-filter" className="text-sm text-slate-500 dark:text-slate-400">Language:</label>
          <select
            id="lang-filter"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
          >
            <option value="">All</option>
            <option value="en">English</option>
            <option value="si">Sinhala</option>
            <option value="ta">Tamil</option>
          </select>
        </div>
      </div>

      {/* Overview metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Assessments"
          value={ov?.total_assessments ?? null}
          icon={Activity}
          color="bg-blue-50 dark:bg-blue-900/20 text-blue-600"
        />
        <MetricCard
          label="Completed Assessments"
          value={ov?.completed_assessments ?? null}
          icon={TrendingUp}
          color="bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600"
        />
        <MetricCard
          label="Unique Participants"
          value={ov?.unique_participants ?? null}
          icon={Users}
          color="bg-purple-50 dark:bg-purple-900/20 text-purple-600"
        />
        <MetricCard
          label="Completion Rate"
          value={ov?.completion_rate ?? null}
          suppressed={ov?.completion_rate_suppressed}
          icon={HeartPulse}
          color="bg-amber-50 dark:bg-amber-900/20 text-amber-600"
        />
      </div>

      {/* Severity distribution */}
      {severity.data && (
        <SectionCard
          title="Assessment Findings Distribution"
          disclaimer={severity.data.disclaimer}
        >
          <div>
            {severity.data.distribution.map((b) => (
              <Bar
                key={b.category}
                label={b.category}
                count={b.count}
                max={sevMax}
                suppressed={b.suppressed}
                percentage={b.percentage}
              />
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
            Total completed assessments: {severity.data.total_assessments}
          </p>
        </SectionCard>
      )}

      {/* Trajectory distribution (Phase 4 integration) */}
      {trajectory.data && (
        <SectionCard
          title="Health Trajectory Distribution"
          disclaimer={trajectory.data.disclaimer}
        >
          <div>
            {trajectory.data.distribution.map((b) => (
              <Bar
                key={b.trend}
                label={b.trend.charAt(0).toUpperCase() + b.trend.slice(1)}
                count={b.count}
                max={Math.max(1, ...trajectory.data!.distribution.map((d) => d.count))}
                suppressed={b.suppressed}
                percentage={b.percentage}
              />
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
            Patients with multiple assessments: {trajectory.data.patients_with_trajectory}
          </p>
        </SectionCard>
      )}

      {/* Accessibility (Phase 5 integration) */}
      {accessibility.data && (
        <SectionCard
          title="Accessibility Metrics"
          disclaimer={accessibility.data.disclaimer}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-3">
              <span className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800">
                <Globe className="h-5 w-5 text-slate-600 dark:text-slate-400" />
              </span>
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Languages with data</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-white">
                  {accessibility.data.accessibility.by_language.filter((l) => !l.suppressed).length}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800">
                <Mic className="h-5 w-5 text-slate-600 dark:text-slate-400" />
              </span>
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Voice intake sessions</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-white">
                  {accessibility.data.accessibility.voice_suppressed
                    ? 'Suppressed'
                    : accessibility.data.accessibility.voice_intake_count}
                </p>
              </div>
            </div>
          </div>
        </SectionCard>
      )}

      {/* SDG dashboard */}
      {sdg.data && (
        <SectionCard title="SDG-Aligned Digital Health Indicators" disclaimer={sdg.data.disclaimer}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sdg.data.sections.map((section) => (
              <div
                key={section.goal}
                className="border border-slate-200 dark:border-slate-800 rounded-lg p-4"
              >
                <h4 className="font-semibold text-slate-900 dark:text-white">
                  {section.goal} — {section.title}
                </h4>
                <dl className="mt-3 space-y-2">
                  {section.metrics.map((m) => (
                    <div key={m.label} className="flex items-start justify-between gap-2">
                      <dt className="text-sm text-slate-600 dark:text-slate-400">{m.label}</dt>
                      <dd className="text-sm font-medium text-slate-900 dark:text-white">
                        {m.suppressed ? <SuppressedBadge /> : (m.value !== null ? m.value.toLocaleString() : '—')}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  )
}

export default AnalyticsDashboardPage
