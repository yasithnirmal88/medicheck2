import React from 'react'
import Button from '@/shared/ui/Button'
import Card from '@/shared/ui/Card'
import type { AssessmentSession } from '../types'
import { cn } from '@/lib/utils'

interface SessionCardProps {
  session: AssessmentSession
  onResume?: (id: string) => void
  onViewResult?: (id: string) => void
}

const statusConfig: Record<string, { label: string; color: string }> = {
  in_progress: { label: 'In Progress', color: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950 dark:text-yellow-400' },
  paused: { label: 'Paused', color: 'text-blue-600 bg-blue-50 dark:bg-blue-950 dark:text-blue-400' },
  completed: { label: 'Completed', color: 'text-green-600 bg-green-50 dark:bg-green-950 dark:text-green-400' },
  cancelled: { label: 'Cancelled', color: 'text-gray-600 bg-gray-50 dark:bg-gray-950 dark:text-gray-400' },
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}

const SessionCard: React.FC<SessionCardProps> = ({ session, onResume, onViewResult }) => {
  const config = statusConfig[session.status] ?? statusConfig.cancelled
  const pct = session.progress ? Math.round(session.progress.completion_percentage) : 0

  return (
    <Card className="space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">
            Session
          </h3>
          <p className="text-xs text-gray-500">ID: {session.id.slice(0, 8)}...</p>
        </div>
        <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', config.color)}>
          {config.label}
        </span>
      </div>

      <div>
        <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
          <span>Progress</span>
          <span>{pct}%</span>
        </div>
        <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full rounded-full transition-all',
              pct === 100 ? 'bg-green-500' : pct > 50 ? 'bg-yellow-500' : 'bg-indigo-500'
            )}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center text-xs text-gray-500">
        <div>
          <p className="font-medium text-gray-900 dark:text-gray-100">{session.progress?.answered_questions ?? 0}</p>
          <p>Answered</p>
        </div>
        <div>
          <p className="font-medium text-gray-900 dark:text-gray-100">{session.progress?.total_questions ?? 0}</p>
          <p>Total</p>
        </div>
        <div>
          <p className="font-medium text-gray-900 dark:text-gray-100">{formatDate(session.updated_at ?? session.created_at)}</p>
          <p>Updated</p>
        </div>
      </div>

      <div className="flex gap-2 pt-1">
        {(session.status === 'in_progress' || session.status === 'paused') && onResume && (
          <Button onClick={() => onResume(session.id)} className="flex-1 min-h-[44px] text-sm">
            Resume
          </Button>
        )}
        {session.status === 'completed' && onViewResult && (
          <Button onClick={() => onViewResult(session.id)} variant="ghost" className="flex-1 min-h-[44px] text-sm">
            View Result
          </Button>
        )}
      </div>
    </Card>
  )
}

export default SessionCard
