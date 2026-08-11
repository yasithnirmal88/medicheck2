import React from 'react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import { useQuery } from '@tanstack/react-query'
import { fetchReportBySession } from '../api/patientService'
import { useParams } from 'react-router-dom'
import ReportExplanation from '../components/ReportExplanation'

interface BodySystemAssessment {
  id: string
  body_system_id?: string
  category?: string
  notes?: string
  [key: string]: unknown
}

interface Condition {
  id: string
  condition_id?: string
  confidence?: number
  notes?: string
}

interface Advice {
  id: string
  category?: string
  text?: string
}

interface HealthReport {
  summary?: string
  body_systems?: BodySystemAssessment[]
  conditions?: Condition[]
  advices?: Advice[]
  [key: string]: unknown
}

export default function ReportViewer() {
  const { id } = useParams<{ id: string }>()
  const { data: report, isLoading } = useQuery<HealthReport>({ queryKey: ['report', id], queryFn: () => fetchReportBySession(id || ''), enabled: !!id })

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto p-4">
        <h1 className="text-2xl font-semibold mb-4">Health Report</h1>
        <Card>
          {isLoading ? (
            <div>Loading report...</div>
          ) : !report ? (
            <div className="text-sm text-gray-500">Report not found. You can generate a report from an assessment.</div>
          ) : (
            <div className="space-y-4">
              <section>
                <h2 className="text-lg font-medium">Overview</h2>
                <div className="text-sm text-gray-700 mt-2">{report.summary ?? 'No summary available'}</div>
              </section>

              <section>
                <h2 className="text-lg font-medium mt-4">Body Systems</h2>
                <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-3">
                  {report.body_systems && report.body_systems.length > 0 ? (
                    report.body_systems.map((b: BodySystemAssessment) => (
                      <div key={b.id} className="p-3 border rounded">
                        <div className="text-sm font-medium">Body system: {b.body_system_id ?? 'Unknown'}</div>
                        <div className="text-xs text-gray-500">Category: {b.category}</div>
                        <div className="text-xs text-gray-500">Notes: {b.notes}</div>
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-gray-500">No body system assessments found.</div>
                  )}
                </div>
              </section>

              <section>
                <h2 className="text-lg font-medium mt-4">Condition Assessments</h2>
                {report.conditions && report.conditions.length > 0 ? (
                  <ul className="mt-2 space-y-2">
                    {report.conditions.map((c: Condition) => (
                      <li key={c.id} className="p-3 border rounded">
                        <div className="text-sm font-medium">Condition: {c.condition_id}</div>
                        <div className="text-xs text-gray-500">Confidence: {c.confidence}</div>
                        <div className="text-xs text-gray-500">Notes: {c.notes}</div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-sm text-gray-500">No condition assessments found.</div>
                )}
              </section>

              <section>
                <h2 className="text-lg font-medium mt-4">Recommendations & Advice</h2>
                {report.advices && report.advices.length > 0 ? (
                  <ul className="mt-2 space-y-2">
                    {report.advices.map((a: Advice) => (
                      <li key={a.id} className="p-3 border rounded">
                        <div className="text-sm font-medium">{a.category ?? 'Advice'}</div>
                        <div className="text-xs text-gray-500">{a.text}</div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-sm text-gray-500">No recommendations generated.</div>
                )}
              </section>
            </div>
          )}
        </Card>

        {/* AI explanation is a clearly separated, additive section. The
            deterministic clinical report above is never replaced or hidden. */}
        {!isLoading && report ? (
          <ReportExplanation sessionId={id} />
        ) : null}
      </div>
    </AppLayout>
  )
}
