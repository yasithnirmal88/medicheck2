import React, { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import AppLayout from '@/layouts/AppLayout'
import Skeleton from '@/shared/ui/Skeleton'
import Button from '@/shared/ui/Button'
import SessionCard from '../components/SessionCard'
import { useSessions } from '../hooks/useQuestionnaire'
import { cn } from '@/lib/utils'

type StatusFilter = 'all' | 'in_progress' | 'paused' | 'completed'

const QuestionnaireHistoryPage: React.FC = () => {
  const navigate = useNavigate()
  const { data: sessions, isLoading, error } = useSessions()
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [sortAsc, setSortAsc] = useState(false)

  const filtered = useMemo(() => {
    if (!sessions) return []
    let result = [...sessions]
    if (statusFilter !== 'all') {
      result = result.filter((s) => s.status === statusFilter)
    }
    result.sort((a, b) => {
      const dateA = new Date(a.updated_at ?? a.created_at).getTime()
      const dateB = new Date(b.updated_at ?? b.created_at).getTime()
      return sortAsc ? dateA - dateB : dateB - dateA
    })
    return result
  }, [sessions, statusFilter, sortAsc])

  const handleResume = (sessionId: string) => {
    navigate(`/questionnaires/${sessionId}`)
  }

  const handleViewResult = (sessionId: string) => {
    navigate(`/questionnaires/${sessionId}`)
  }

  const filters: { value: StatusFilter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'paused', label: 'Paused' },
    { value: 'completed', label: 'Completed' },
  ]

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto p-4">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Assessment History</h1>
            <p className="text-sm text-gray-500">View and resume your past assessments</p>
          </div>
          <Button variant="ghost" onClick={() => navigate('/questionnaires')} className="min-h-[44px]">
            New Assessment
          </Button>
        </div>

        <div className="flex items-center gap-2 mb-4 flex-wrap">
          {filters.map((f) => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={cn(
                'px-3 py-1.5 rounded-full text-sm border transition-colors min-h-[36px]',
                statusFilter === f.value
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-transparent text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:border-indigo-300'
              )}
            >
              {f.label}
            </button>
          ))}
          <button
            onClick={() => setSortAsc(!sortAsc)}
            className="ml-auto px-3 py-1.5 rounded-full text-sm border border-gray-300 dark:border-gray-600 hover:border-indigo-300 min-h-[36px] flex items-center gap-1"
            aria-label="Toggle sort order"
          >
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {sortAsc ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              )}
            </svg>
            {sortAsc ? 'Oldest' : 'Newest'}
          </button>
        </div>

        {isLoading && (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg text-center">
            <p className="text-red-600 dark:text-red-400 mb-2">Failed to load history</p>
            <Button variant="ghost" onClick={() => window.location.reload()}>
              Try Again
            </Button>
          </div>
        )}

        {filtered.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <svg className="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <p className="text-gray-500">
              {statusFilter === 'all'
                ? 'No assessment sessions yet'
                : `No ${statusFilter.replace('_', ' ')} sessions`}
            </p>
            <Button onClick={() => navigate('/questionnaires')} className="mt-4 min-h-[44px]">
              Start an Assessment
            </Button>
          </div>
        )}

        <div className="space-y-4">
          {filtered.map((session) => (
            <SessionCard
              key={session.id}
              session={session}
              onResume={handleResume}
              onViewResult={handleViewResult}
            />
          ))}
        </div>
      </div>
    </AppLayout>
  )
}

export default QuestionnaireHistoryPage
