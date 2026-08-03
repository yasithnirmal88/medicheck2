import React, { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ClipboardList, History, PauseCircle, Play, Search, TrendingUp, Loader2 } from 'lucide-react'
import AppLayout from '@/layouts/AppLayout'
import ProgressBar from '../components/ProgressBar'
import AssessmentCard from '../components/AssessmentCard'
import StatTile from '../components/StatTile'
import SearchFilters, { type QuestionnaireFilter } from '../components/SearchFilters'
import RecentAssessmentRow from '../components/RecentAssessmentRow'
import EmptyState from '../components/EmptyState'
import Skeleton from '@/shared/ui/Skeleton'
import Button from '@/shared/ui/Button'
import { useTemplates, useStartSession, useSessions } from '../hooks/useQuestionnaire'
import type { QuestionnaireTemplate, AssessmentSession } from '../types'

const HeroSection: React.FC<{
  templates: QuestionnaireTemplate[] | undefined
  sessions: AssessmentSession[] | undefined
}> = ({ templates, sessions }) => {
  const inProgress = sessions?.find((s) => s.status === 'in_progress' || s.status === 'paused')
  const completedCount = sessions?.filter((s) => s.status === 'completed').length ?? 0

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-600 via-blue-600 to-indigo-700 px-6 py-10 text-white shadow-lg">
      <div
        className="absolute -bottom-16 -left-16 hidden h-40 w-40 rounded-full bg-white/10 blur-2xl md:block"
        aria-hidden="true"
      />
      <div className="relative flex flex-col gap-1.5">
        <p className="text-2xl font-bold md:text-3xl">Health Assessments</p>
        <p className="max-w-2xl text-sm text-indigo-100">
          AI-driven medical questionnaires that adapt to your health profile. Track your risk factors, continue
          where you left off, and review your assessment history.
        </p>
      </div>
      <div className="mt-6 flex flex-wrap items-center gap-6 text-sm">
        <span className="inline-flex items-center gap-2">
          <TrendingUp className="h-4 w-4" aria-hidden="true" />
          {templates?.length ?? 0} Assessments available
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-green-300" />
          {completedCount} Completed
        </span>
      </div>
      <div className="mt-6">
        <div className="text-xs uppercase tracking-wider text-indigo-200">
          {inProgress ? 'Session in progress' : 'Ready to begin'}
        </div>
        <div className="mt-1 text-sm text-indigo-100">
          {inProgress
            ? 'Your last assessment is still open and can be resumed at any time.'
            : 'Pick an assessment below to get started.'}
        </div>
      </div>
    </div>
  )
}

type Stat = { label: string; value: number }

const QuestionnaireListPage: React.FC = () => {
  const navigate = useNavigate()
  const [filter, setFilter] = useState<QuestionnaireFilter>({ query: '', status: 'all' })

  const { data: templates, isLoading: isLoadingTemplates } = useTemplates()
  const { data: sessions, isLoading: isLoadingSessions } = useSessions()
  const startSession = useStartSession()

  const isLoading = isLoadingTemplates || isLoadingSessions

  const inProgressSession = sessions?.find((s) => s.status === 'in_progress' || s.status === 'paused')
  const recentSessions = sessions?.filter((s) => s.status !== 'cancelled').slice(0, 5) ?? []

  const availableTemplates = templates ?? []

  const statusStats: Stat[] = useMemo(() => {
    const all = sessions ?? []
    const byStatus = (s: AssessmentSession['status']) => all.filter((x) => x.status === s).length
    return [
      { label: 'Completed', value: byStatus('completed') },
      { label: 'In Progress', value: byStatus('in_progress') },
      { label: 'Paused', value: byStatus('paused') },
    ]
  }, [sessions])

  const avgCompletion = useMemo(() => {
    const comps = sessions?.filter((s) => s.status === 'completed' || s.status === 'in_progress')
    if (!comps || comps.length === 0) return 0
    const sum = comps.reduce((acc, s) => acc + (s.progress?.completion_percentage ?? 0), 0)
    return Math.round(sum / comps.length)
  }, [sessions])

  const handleStart = (templateId: string) => {
    startSession.mutate(templateId, {
      onSuccess: (session) => navigate(`/questionnaires/${session.id}`),
    })
  }

  const handleContinue = (sessionId: string) => navigate(`/questionnaires/${sessionId}`)

  const filteredTemplates = useMemo(() => {
    let list = availableTemplates
    if (filter.status !== 'all') {
      list = list.filter((t) => {
        if (filter.status === 'completed') return false
        if (filter.status === 'available') return !sessions?.some((s) => s.questionnaire_template_id === t.id)
        return sessions?.some(
          (s) => s.questionnaire_template_id === t.id && (filter.status === 'in_progress' ? s.status === 'in_progress' : s.status === filter.status),
        )
      })
    }
    if (filter.query) {
      const q = filter.query.toLowerCase()
      list = list.filter((t) => (t.name + ' ' + (t.description ?? '') + ' ' + (t.target_audience ?? '')).toLowerCase().includes(q))
    }
    return list
  }, [availableTemplates, filter, sessions])

  return (
    <AppLayout>
      <div className="mx-auto max-w-7xl space-y-8 py-2">
        {/* Hero */}
        <HeroSection templates={templates} sessions={sessions} />

        {/* Quick actions */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant="primary"
            className="min-h-[44px]"
            onClick={() => {
              if (filteredTemplates.length > 0) {
                handleStart(filteredTemplates[0].id)
              }
            }}
            disabled={isLoading || filteredTemplates.length === 0}
          >
            New Assessment
          </Button>
          <Button variant="ghost" className="min-h-[44px]" onClick={() => navigate('/questionnaires/history')}>
            <History className="h-4 w-4" />
            View History
          </Button>
        </div>

        {/* Assessment statistics */}
        <section aria-labelledby="stats-heading">
          <h2 id="stats-heading" className="sr-only">
            Assessment statistics
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {isLoading ? (
              <>
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full rounded-xl" />
                ))}
              </>
            ) : (
              <>
                <StatTile icon={TrendingUp} label="Avg. Completion" value={`${avgCompletion}%`} trend="up" />
                <StatTile icon={Play} label="In Progress" value={statusStats[1].value} trend="flat" />
                <StatTile icon={PauseCircle} label="Paused" value={statusStats[2].value} trend="flat" />
                <StatTile icon={ClipboardList} label="Completed" value={statusStats[0].value} trend="up" />
              </>
            )}
          </div>
        </section>

        {/* Continue Assessment card */}
        <section aria-labelledby="continue-heading">
          {inProgressSession ? (
            <div className="rounded-xl border border-yellow-200 bg-gradient-to-r from-yellow-50 via-amber-50 to-yellow-50 p-5 shadow-sm dark:border-yellow-900/50 dark:from-yellow-900/30 dark:to-amber-900/30">
              <div className="mb-3 flex items-center justify-between">
                <h2 id="continue-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Continue your assessment
                </h2>
                <span className="text-xs font-medium text-yellow-700 dark:text-yellow-300">
                  {inProgressSession.status === 'in_progress' ? 'In progress' : 'Paused'}
                </span>
              </div>
              <div className="mb-4">
                <p className="font-medium text-gray-800 dark:text-gray-200">
                  {sessions?.find((s) => s.id === inProgressSession.id)?.questionnaire_template_id ??
                    inProgressSession.questionnaire_template_id}
                </p>
                <ProgressBar
                  current={inProgressSession.progress?.completed_questions ?? 0}
                  total={inProgressSession.progress?.total_questions ?? 0}
                  percentage={inProgressSession.progress?.completion_percentage ?? 0}
                />
                <div className="mt-1 text-right text-xs text-gray-500 dark:text-gray-400">
                  {inProgressSession.progress?.skipped_questions ?? 0} questions skipped
                </div>
              </div>
              <Button
                variant="ghost"
                className="min-h-[44px] bg-white dark:bg-slate-800"
                onClick={() => handleContinue(inProgressSession.id)}
              >
                <Play className="h-4 w-4" />
                Resume Assessment
              </Button>
            </div>
          ) : (
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-800">
              <h2 id="continue-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                You have no assessments in progress
              </h2>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Start a new assessment below or pick up a previous one from your history.
              </p>
            </div>
          )}
        </section>

        {/* Search + Filters */}
        <section aria-labelledby="available-heading">
          <div className="flex items-center justify-between">
            <h2 id="available-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Available Assessments
            </h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">{filteredTemplates.length} shown</span>
          </div>
          <SearchFilters value={filter} onChange={setFilter} className="mt-3" />

          {isLoading ? (
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-48 w-full rounded-xl" />
              ))}
            </div>
          ) : filteredTemplates.length > 0 ? (
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredTemplates.map((template) => {
                const latest = sessions?.find((s) => s.questionnaire_template_id === template.id)
                return (
                  <AssessmentCard
                    key={template.id}
                    template={template}
                    status={latest ? (latest.status as any) : 'available'}
                    progress={
                      latest && latest.status !== 'completed'
                        ? {
                            current: latest.progress?.current_section ? 1 : 0,
                            total: latest.progress?.total_questions ?? 1,
                            percentage: latest.progress?.completion_percentage ?? 0,
                          }
                        : undefined
                    }
                    lastTaken={latest ? formatDate(latest.updated_at) : undefined}
                    onStart={handleStart}
                  />
                )
              })}
            </div>
          ) : (
            <EmptyState
              icon={Search}
              title="No assessments found"
              description={filter.query ? 'Try a different search term or reset your filters.' : 'No assessments are currently available.'}
              action={
                filter.query || filter.status !== 'all' ? (
                  <Button variant="ghost" onClick={() => setFilter({ query: '', status: 'all' })}>
                    Reset filters
                  </Button>
                ) : undefined
              }
            />
          )}
        </section>

        {/* Recent assessments */}
        <section aria-labelledby="recent-heading">
          <div className="flex items-center justify-between">
            <h2 id="recent-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Recent Assessments
            </h2>
            {recentSessions.length > 0 && (
              <Button variant="ghost" className="min-h-[44px]" onClick={() => navigate('/questionnaires/history')}>
                See all
              </Button>
            )}
          </div>
          {isLoading ? (
            <div className="mt-3 space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full rounded-lg" />
              ))}
            </div>
          ) : recentSessions.length > 0 ? (
            <ul className="mt-3 space-y-2">
              {recentSessions.map((s) => (
                <RecentAssessmentRow
                  key={s.id}
                  session={s}
                  template={templates?.find((t) => t.id === s.questionnaire_template_id)}
                  onOpen={handleContinue}
                />
              ))}
            </ul>
          ) : (
            <EmptyState
              icon={History}
              title="No recent assessments"
              description="Once you start an assessment, it will appear here for quick access."
            />
          )}
        </section>
      </div>
    </AppLayout>
  )
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })

export default QuestionnaireListPage
