import React, { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Sparkles, X } from 'lucide-react'
import AppLayout from '@/layouts/AppLayout'
import AssessmentCard from '../components/AssessmentSelector'
import { assessments } from '../data/assessments'
import { useTemplates, useStartSession } from '../hooks/useQuestionnaire'
import type { QuestionnaireTemplate } from '../types'
import Skeleton from '@/shared/ui/Skeleton'

const AssessmentSelectionPage: React.FC = () => {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const { data: templates, isLoading } = useTemplates()
  const startSession = useStartSession()

  const handleStart = (code: string, templateId?: string) => {
    let id = templateId
    if (!id && templates?.length) {
      const match = templates.find((t) => t.code === code)
      id = match?.id
    }
    if (id) {
      startSession.mutate(id, {
        onSuccess: (session) => navigate(`/questionnaires/${session.id}`),
      })
    } else if (templates?.length) {
      // Fallback: start the first matching template by name
      const match = templates.find((t) => t.name.toLowerCase().includes(code.replace(/-/g, ' ')))
      if (match) {
        startSession.mutate(match.id, {
          onSuccess: (session) => navigate(`/questionnaires/${session.id}`),
        })
        return
      }
    }
    // No backend template wired up — still route to a session-less questionnaire view if available
    void id
  }

  const matched = useMemo(() => {
    const map = new Map<string, QuestionnaireTemplate>()
    templates?.forEach((t) => map.set(t.code, t))
    return map
  }, [templates])

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim()
    if (!q) return assessments
    return assessments.filter(
      (a) =>
        a.title.toLowerCase().includes(q) ||
        a.description.toLowerCase().includes(q) ||
        a.bodySystems.some((b) => b.name.toLowerCase().includes(q)),
    )
  }, [query])

  return (
    <AppLayout>
      <div className="mx-auto max-w-7xl space-y-8 py-2">
        {/* Hero */}
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-600 via-blue-600 to-indigo-700 px-8 py-12 text-white shadow-xl">
          <div
            className="absolute -bottom-20 -left-20 hidden h-52 w-52 rounded-full bg-white/10 blur-3xl md:block"
            aria-hidden="true"
          />
          <div className="relative flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-yellow-300" aria-hidden="true" />
              <span className="text-lg font-semibold">Personalized Health Assessments</span>
            </div>
            <p className="text-3xl font-bold md:text-4xl">Pick an assessment</p>
            <p className="max-w-2xl text-sm text-indigo-100">
              AI-powered questionnaires that adapt to your health profile. Each assessment gives you a personalized risk
              score, body-system breakdowns, and actionable recommendations.
            </p>
          </div>
          <div className="mt-8 flex flex-wrap items-center gap-4 text-sm">
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-green-300" />
              {assessments.length} Assessments
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-indigo-300" />
              5–25 min each
            </span>
          </div>
        </section>

        {/* AI intake entry point (Phase 3) */}
        <section className="rounded-2xl border border-indigo-200 bg-indigo-50/60 p-5 dark:border-indigo-900/40 dark:bg-indigo-900/10">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-indigo-500" aria-hidden="true" />
              <div>
                <h2 className="text-sm font-semibold text-indigo-900 dark:text-indigo-200">
                  Not sure where to start? Describe what you&apos;re experiencing
                </h2>
                <p className="mt-1 text-sm text-indigo-700/80 dark:text-indigo-300/80">
                  AI-assisted intake can help identify relevant information and suggest a few questions. It&apos;s optional —
                  you can always pick an assessment below.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => navigate('/assessments/intake')}
              className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              Try AI intake
            </button>
          </div>
        </section>

        {/* Search */}
        <section className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="relative max-w-md flex-1">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search assessments, body systems..."
              className="w-full rounded-xl border border-gray-300 bg-white py-2 pl-10 pr-3 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/60 focus:border-blue-500 dark:border-gray-600 dark:bg-slate-900 dark:text-gray-100 dark:placeholder:text-gray-500"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                aria-label="Clear search"
                className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded p-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
              >
                <X className="h-3.5 w-3.5" aria-hidden="true" />
              </button>
            )}
          </div>
          <span className="text-sm text-gray-500 dark:text-gray-400">{filtered.length} available</span>
        </section>

        {/* Assessments grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {assessments.map((_, i) => (
              <Skeleton key={assessments[i].code ?? i} className="h-72 w-full rounded-2xl" />
            ))}
          </div>
        ) : filtered.length > 0 ? (
          <section
            aria-label="Available assessments"
            className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
          >
            {filtered.map((entry, i) => (
              <AssessmentCard
                key={entry.code}
                entry={entry}
                template={matched.get(entry.code)}
                onStart={handleStart}
                delay={i * 50}
              />
            ))}
          </section>
        ) : (
          <section className="rounded-2xl border border-dashed border-gray-200 bg-white py-14 text-center dark:border-gray-700 dark:bg-slate-800">
            <Search className="mx-auto h-10 w-10 text-gray-300 dark:text-gray-600" aria-hidden="true" />
            <p className="mt-3 text-lg font-medium text-gray-700 dark:text-gray-200">No assessments found</p>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Try a different search term or check back soon.
            </p>
          </section>
        )}
      </div>
    </AppLayout>
  )
}

export default AssessmentSelectionPage
