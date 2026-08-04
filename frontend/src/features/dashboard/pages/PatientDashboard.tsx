import React from 'react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import { useProfile, useCompletion, useSessions } from '../hooks/usePatientDashboard'
import { Link } from 'react-router-dom'

interface Session {
  id: string
  started_at?: string
  status: string
  [key: string]: unknown
}

export default function PatientDashboard() {
  const { data: profile } = useProfile()
  const { data: completion } = useCompletion()
  const { data: sessions } = useSessions() as { data?: Session[] }

  const latestSession = sessions && sessions.length > 0 ? sessions[0] : null

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto p-4 space-y-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold">Hello{profile?.full_name ? `, ${profile.full_name}` : ''}</h1>
              <p className="text-sm text-muted-foreground mt-1">Welcome back &mdash; here&apos;s a snapshot of your health.</p>
            </div>
            <div className="text-right">
              <div className="text-sm">Profile completion</div>
              <div className="text-2xl font-bold">{completion?.overall ?? '--'}%</div>
              <div className="text-xs text-gray-500">{completion?.completed ?? 0}/{completion?.total ?? 0} sections</div>
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card>
            <h2 className="text-lg font-medium">Latest assessment</h2>
            {latestSession ? (
              <div className="mt-2">
                <div className="text-sm">Date: {latestSession.started_at ?? '—'}</div>
                <div className="text-sm">Status: {latestSession.status}</div>
                <div className="mt-3">
                  <Link to={`/assessments/${latestSession.id}`} className="text-indigo-600">Open assessment</Link>
                </div>
              </div>
            ) : (
              <div className="mt-2 text-sm text-gray-500">No recent assessments</div>
            )}
          </Card>

          <Card>
            <h2 className="text-lg font-medium">Body systems</h2>
            <div className="mt-2 text-sm text-gray-600">Open the Body System dashboard to view detailed status.</div>
            <div className="mt-3">
              <Link to="/body-systems" className="text-indigo-600">View body systems</Link>
            </div>
          </Card>

          <Card>
            <h2 className="text-lg font-medium">Recommendations</h2>
            <div className="mt-2 text-sm text-gray-600">See your active recommendations and mark them as completed.</div>
            <div className="mt-3">
              <Link to="/recommendations" className="text-indigo-600">Open Recommendation Center</Link>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <h3 className="text-base font-medium">Assessment History</h3>
            <div className="mt-2">
              {sessions && sessions.length > 0 ? (
                <ul className="space-y-2">
                  {sessions.slice(0, 5).map((s: Session) => (
                    <li key={s.id} className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">{s.id}</div>
                        <div className="text-xs text-gray-500">{s.started_at ?? '—'}</div>
                      </div>
                      <div>
                        <Link to={`/assessments/${s.id}`} className="text-indigo-600 text-sm">Open</Link>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-sm text-gray-500">No assessments yet</div>
              )}
            </div>
          </Card>

          <Card>
            <h3 className="text-base font-medium">Health Timeline</h3>
            <div className="mt-2 text-sm text-gray-600">A timeline view of past assessments and events.</div>
            <div className="mt-3">
              <Link to="/timeline" className="text-indigo-600">Open timeline</Link>
            </div>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}
