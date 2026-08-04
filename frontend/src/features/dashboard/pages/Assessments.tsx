import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3,
  Bell,
  Bot,
  Clock,
  FileText,
  Grid2X2,
  History,
  LogOut,
  Menu,
  Search,
  Settings,
  ShieldHalf,
  User,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import Card from '@/shared/ui/Card'
import {
  AssessmentStatistics,
  AssessmentFilters,
  ContinueAssessmentCard,
  AssessmentCard,
  AssessmentTimeline,
  AssessmentHistoryTable,
  RecommendationCard,
  HealthJourneyStepper,
  AssessmentCategories,
  AIInsightsPreview,
} from '../assessments/components'
import { assessmentDefs, timelineEvents, completedAssessments } from '../assessments/mockData'
import type { AssessmentFilters as Filters, AssessmentDef } from '../assessments/types'
import { useTheme } from '@/providers/ThemeProvider'

const DEFAULT_FILTERS: Filters = {
  search: '',
  status: [],
  bodySystem: [],
  duration: '',
  difficulty: [],
  priority: [],
}

const Assessments: React.FC = () => {
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { theme, toggle } = useTheme()

  const visibleAssessments = useMemo(() => {
    return assessmentDefs.filter((a) => {
      if (filters.search && !a.title.toLowerCase().includes(filters.search.toLowerCase())) {
        return false
      }
      if (filters.status.length > 0 && !filters.status.includes(a.status)) return false
      if (filters.priority.length > 0 && !filters.priority.includes(a.priority)) return false
      if (filters.difficulty.length > 0 && !filters.difficulty.includes(a.difficulty)) return false
      if (filters.bodySystem.length > 0) {
        if (!a.bodySystems.some((b) => filters.bodySystem.includes(b.id))) return false
      }
      if (filters.duration) {
        const d = a.durationMinutes
        if (filters.duration === 'short' && d >= 6) return false
        if (filters.duration === 'medium' && (d < 6 || d > 10)) return false
        if (filters.duration === 'long' && d <= 10) return false
      }
      return true
    })
  }, [filters])

  const inProgress = visibleAssessments.filter((a) => a.status === 'in_progress')
  const completed = visibleAssessments.filter((a) => a.status === 'completed')
  const averageScore =
    completed.length > 0
      ? Math.round(completed.reduce((sum, a) => sum + (a.healthScore ?? 0), 0) / completed.length)
      : 0
  const nextAssessment =
    visibleAssessments.find((a) => a.status === 'recommended')?.title ?? completedAssessments[0]?.title ?? 'Heart Health'

  const handleReset = () => setFilters(DEFAULT_FILTERS)
  const handleFilterChange = (f: Partial<Filters>) => setFilters((prev) => ({ ...prev, ...f }))
  const handlePrimary = (a: AssessmentDef) => {
    if (a.status === 'in_progress' || a.status === 'recommended') {
      console.log('resume/start', a.slug)
    }
  }
  const handleEdit = (a: AssessmentDef) => console.log('edit', a.slug)
  const handleDiscard = (a: AssessmentDef) => console.log('discard', a.slug)

  return (
    <div className="flex h-screen flex-col bg-gray-50 dark:bg-slate-950">
      {/* Top Navigation */}
      <header className="flex h-14 items-center justify-between gap-2 border-b border-slate-200/80 bg-white/70 px-3 backdrop-blur dark:border-slate-700/60 dark:bg-slate-900/60">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 md:hidden"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <ShieldHalf className="h-6 w-6 text-indigo-600" />
            <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">Medicheck</span>
          </div>
        </div>

        <nav className="hidden items-center gap-5 md:flex">
          <a href="/dashboard" className="flex items-center gap-1.5 text-sm font-medium text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">
            <BarChart3 className="h-4 w-4" />
            Dashboard
          </a>
          <a
            href="/assessments"
            className="flex items-center gap-1.5 text-sm font-medium text-indigo-600 dark:text-white"
          >
            Assessments
          </a>
          <a href="/timeline" className="flex items-center gap-1.5 text-sm font-medium text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">
            <History className="h-4 w-4" />
            Timeline
          </a>
          <a href="/recommendations" className="flex items-center gap-1.5 text-sm font-medium text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">
            <Bot className="h-4 w-4" />
            Recommendations
          </a>
        </nav>

        <div className="flex items-center gap-2">
          <div className="relative hidden sm:block">
            <Search className="absolute left-2.5 top-2 h-4 w-4 text-gray-400" />
            <input
              type="search"
              placeholder="Search..."
              className={cn(
                'rounded-lg border border-slate-200 bg-white pl-8 pr-3 py-1.5 text-sm outline-none',
                'dark:border-slate-700 dark:bg-slate-800 dark:text-gray-100',
              )}
            />
          </div>
          <button
            type="button"
            onClick={toggle}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? '🌙' : '☀️'}
          </button>
          <button
            type="button"
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4" />
          </button>
          <div className="relative">
            <button
              type="button"
              id="profile-menu-button"
              className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-indigo-600 hover:bg-indigo-200 dark:bg-indigo-950/40"
              aria-label="User profile"
            >
              <User className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar (overlay on mobile) */}
        <motion.aside
          initial={false}
          animate={sidebarOpen ? 'open' : 'closed'}
          variants={{
            open: { x: 0 },
            closed: { x: '-100%' },
          }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
          className="fixed inset-y-0 left-0 z-40 w-64 overflow-y-auto md:relative md:translate-x-0"
        >
          <div
            className={cn(
              'absolute inset-0 bg-black/30',
              'md:hidden',
            )}
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
          <div
            className={cn(
              'flex h-full w-64 flex-col overflow-y-auto border-r border-slate-200/80 bg-white/70 pt-14 dark:border-slate-700/60 dark:bg-slate-900/60',
            )}
          >
            <nav className="flex flex-col gap-1 p-3 text-sm">
              <a
                href="/assessments"
                className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-indigo-600 bg-indigo-50/60 font-medium dark:bg-indigo-950/40"
              >
                <Grid2X2 className="h-4 w-4" />
                All Assessments
              </a>
              <a className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-gray-600 hover:bg-slate-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-slate-800 dark:hover:text-white">
                <Clock className="h-4 w-4" />
                In Progress
              </a>
              <a className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-gray-600 hover:bg-slate-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-slate-800 dark:hover:text-white">
                <CheckIcon className="h-4 w-4" />
                Completed
              </a>
              <a className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-gray-600 hover:bg-slate-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-slate-800 dark:hover:text-white">
                <History className="h-4 w-4" />
                History
              </a>
              <a className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-gray-600 hover:bg-slate-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-slate-800 dark:hover:text-white">
                <Settings className="h-4 w-4" />
                Settings
              </a>
              <button className="mt-2 flex items-center gap-2.5 rounded-lg px-3 py-2 text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40">
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </nav>
          </div>
        </motion.aside>

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl space-y-6 p-4 pb-24">
            {/* Hero Banner */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, ease: 'easeOut' }}
            >
              <Card
                className={cn(
                  'relative isolate overflow-hidden border-0 bg-gradient-to-br from-indigo-600 via-blue-600 to-teal-500 text-white',
                  'before:absolute before:inset-0 before:bg-[radial-gradient(ellipse_at_50%_-10%,theme(colors.white)_0.05),transparent_15%,theme(colors.white)_0.85,_transparent_100%]',
                )}
              >
                <div className="relative p-6 md:p-8">
                  <div className="flex items-center gap-2">
                    <ShieldHalf className="h-5 w-5" />
                    <span className="text-xs font-medium text-indigo-100">AI-Powered Preventive Health</span>
                  </div>
                  <h1 className="mt-2 text-2xl font-semibold md:text-3xl">Health Assessments</h1>
                  <p className="mt-1 max-w-xl text-sm text-indigo-50">
                    Complete AI-powered preventive health evaluations to understand your current health and identify future risks.
                  </p>
                  <div className="mt-2 flex flex-wrap gap-3">
                    <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-0.5 text-xs">
                      AI Enabled
                    </span>
                    <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-0.5 text-xs">
                      23 assessments
                    </span>
                  </div>
                </div>
              </Card>
            </motion.div>

            {/* KPIs + AI Insight */}
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-4 lg:items-start">
              <div className="lg:col-span-3 space-y-4">
                <AssessmentStatistics
                  completed={completed.length}
                  inProgress={inProgress.length}
                  averageScore={averageScore}
                  nextAssessment={nextAssessment}
                />
                {/* AI Insight strip above the grid for visibility */}
                <div className="hidden sm:block">
                  <AIInsightsPreview />
                </div>
              </div>
              <div className="lg:col-span-1">
                <RecommendationCard />
              </div>
            </div>

            {/* Continue card */}
            {inProgress.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45, ease: 'easeOut', delay: 0.05 }}
              >
                <ContinueAssessmentCard
                  assessment={inProgress[0]}
                  onResume={() => handlePrimary(inProgress[0])}
                  onDiscard={() => handleDiscard(inProgress[0])}
                />
              </motion.div>
            )}

            {/* Health Journey */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, ease: 'easeOut', delay: 0.1 }}
            >
              <HealthJourneyStepper assessments={assessmentDefs} />
            </motion.div>

            {/* Filters */}
            <div className="pt-2">
              <AssessmentFilters filters={filters} onChange={handleFilterChange} onReset={handleReset} />
            </div>

            {/* Available Assessments grid */}
            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Available Assessments</h2>
              {visibleAssessments.length === 0 ? (
                <div className="mt-4 text-sm text-gray-500">No assessments match your filters.</div>
              ) : (
                <motion.div
                  layout
                  className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"
                >
                  {visibleAssessments
                    .filter((a) => !inProgress.includes(a))
                    .map((a) => (
                      <AssessmentCard
                        key={a.id}
                        assessment={a}
                        onPrimary={() => handlePrimary(a)}
                        onEdit={() => handleEdit(a)}
                        onDiscard={() => handleDiscard(a)}
                      />
                    ))}
                </motion.div>
              )}
            </section>

            {/* AI Insights (mobile) */}
            <div className="block sm:hidden">
              <AIInsightsPreview />
            </div>

            {/* Timeline */}
            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Assessment Timeline</h2>
              <Card className="mt-3">
                <AssessmentTimeline items={timelineEvents} />
              </Card>
            </section>

            {/* Categories */}
            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Assessment Categories</h2>
              <div className="mt-3">
                <AssessmentCategories />
              </div>
            </section>

            {/* History */}
            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Assessment History</h2>
              <div className="mt-3 overflow-x-auto">
                <AssessmentHistoryTable
                  assessments={completed}
                  onView={() => console.log('view')}
                  onRetake={() => console.log('retake')}
                  onDownload={() => console.log('download')}
                  onCompare={() => console.log('compare')}
                />
              </div>
            </section>

            {/* Empty state */}
            {completed.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center gap-3 rounded-2xl border border-slate-200/80 bg-white p-8 text-center dark:border-slate-700/60 dark:bg-slate-800/60"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800">
                  <FileText className="h-6 w-6 text-slate-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Let&apos;s begin your health journey.</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  You haven&apos;t completed any assessments yet. Start your first one to generate a personalized report.
                </p>
                <button
                  type="button"
                  onClick={() => handlePrimary(assessmentDefs[0])}
                  className="rounded-xl bg-gradient-to-r from-indigo-500 to-teal-500 px-5 py-2 text-sm font-medium text-white hover:brightness-110"
                >
                  Start First Assessment
                </button>
              </motion.div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

function CheckIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  )
}

export default Assessments
