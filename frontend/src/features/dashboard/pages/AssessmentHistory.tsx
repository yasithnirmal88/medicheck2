import React from 'react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import { useSessions } from '../hooks/usePatientDashboard'
import { Link } from 'react-router-dom'

interface Session {
  id: string
  started_at?: string
  status: string
  [key: string]: unknown
}

export default function AssessmentHistory() {
  const { data: sessions, isLoading } = useSessions()

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto p-4">
        <h1 className="text-2xl font-semibold mb-4">Assessment History</h1>
        <Card>
          {isLoading ? (
            <div>Loading...</div>
          ) : sessions && sessions.length > 0 ? (
            <ul className="divide-y">
              {sessions.map((s: Session) => (
                <li key={s.id} className="py-3 flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium">Assessment</div>
                    <div className="text-xs text-gray-500">{s.started_at ?? '—'}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm">Status: {s.status}</div>
                    <div className="mt-2">
                      <Link to={`/assessments/${s.id}`} className="text-indigo-600">Open</Link>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-sm text-gray-500">No assessments found.</div>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
