import React, { useState } from 'react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import { useReports } from '../hooks/useTimeline'
import { Link } from 'react-router-dom'

interface BodySystem {
  id: string
  body_system_id?: string
  category?: string
}

interface TimelineReport {
  id: string
  session_id?: string
  summary?: string
  status?: string
  created_at?: string
  started_at?: string
  body_systems?: BodySystem[]
  [key: string]: unknown
}

export default function TimelinePage() {
  const [order, setOrder] = useState<'desc' | 'asc'>('desc')
  const { data: reports, isLoading } = useReports(50, 0)

  const sorted = reports ? [...reports].sort((a: TimelineReport, b: TimelineReport) => {
    const da = new Date(a.created_at || a.started_at || 0).getTime()
    const db = new Date(b.created_at || b.started_at || 0).getTime()
    return order === 'desc' ? db - da : da - db
  }) : []

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto p-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-semibold">Health Timeline</h1>
          <div className="flex items-center gap-4">
            <Link to="/timeline/trajectory" className="text-sm text-indigo-600">View trajectory</Link>
            <button onClick={() => setOrder(order === 'desc' ? 'asc' : 'desc')} className="text-sm text-indigo-600">Order: {order === 'desc' ? 'Newest' : 'Oldest'}</button>
          </div>
        </div>

        <Card>
          {isLoading ? (
            <div>Loading...</div>
          ) : sorted.length === 0 ? (
            <div className="text-sm text-gray-500">No assessments found.</div>
          ) : (
            <ul className="space-y-3">
              {sorted.map((r: TimelineReport) => (
                <li key={r.id} className="p-3 border rounded">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-medium">{new Date(r.created_at ?? r.started_at ?? Date.now()).toLocaleString()}</div>
                      <div className="text-xs text-gray-500">Session: {r.session_id ?? r.id}</div>
                      <div className="text-sm mt-2">Summary: {r.summary ?? '—'}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm">Status: {r.status ?? 'processed'}</div>
                      <div className="mt-2">
                        <Link to={`/report/${r.session_id || r.id}`} className="text-indigo-600">View report</Link>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 text-sm text-gray-700">
                    <strong>Body Systems:</strong>
                    <div className="mt-1">
                      {r.body_systems && r.body_systems.length > 0 ? (
                        r.body_systems.map((b: BodySystem) => (
                          <div key={b.id} className="text-xs">{b.body_system_id ?? 'Unknown'} — {b.category}</div>
                        ))
                      ) : (
                        <div className="text-xs text-gray-400">No body system data</div>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
