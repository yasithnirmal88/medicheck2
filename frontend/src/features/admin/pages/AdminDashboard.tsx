import React, { useEffect, useState } from 'react'
import { listIndicators, listEvidence, listRecommendations, listAudit } from '../api/adminService'

interface Indicator {
  id: string
  name: string
  description?: string
  [key: string]: unknown
}

interface Evidence {
  id: string
  title: string
  source: string
  [key: string]: unknown
}

interface Recommendation {
  id: string
  title: string
  [key: string]: unknown
}

interface AuditLog {
  id: string
  changed_at: string
  entity_type: string
  action: string
  [key: string]: unknown
}

export default function AdminDashboard() {
  const [indicators, setIndicators] = useState<Indicator[]>([])
  const [evidence, setEvidence] = useState<Evidence[]>([])
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [audits, setAudits] = useState<AuditLog[]>([])

  useEffect(() => {
    listIndicators().then(setIndicators).catch(() => setIndicators([]))
    listEvidence().then(setEvidence).catch(() => setEvidence([]))
    listRecommendations().then(setRecommendations).catch(() => setRecommendations([]))
    listAudit().then(setAudits).catch(() => setAudits([]))
  }, [])

  return (
    <div className="p-4">
      <h1 className="text-2xl font-semibold mb-4">Medical Knowledge Management — Admin</h1>

      <section className="mb-6">
        <h2 className="text-lg font-medium">Indicators</h2>
        <div className="mt-2">
          {indicators.length === 0 && <div className="text-sm text-muted-foreground">No indicators</div>}
          <ul className="list-disc pl-6">
            {indicators.map((i) => (
              <li key={i.id}>{i.name} — {i.description}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mb-6">
        <h2 className="text-lg font-medium">Evidence</h2>
        <div className="mt-2">
          {evidence.length === 0 && <div className="text-sm text-muted-foreground">No evidence</div>}
          <ul className="list-disc pl-6">
            {evidence.map((e) => (
              <li key={e.id}>{e.title} — {e.source}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mb-6">
        <h2 className="text-lg font-medium">Recommendations</h2>
        <div className="mt-2">
          {recommendations.length === 0 && <div className="text-sm text-muted-foreground">No recommendations</div>}
          <ul className="list-disc pl-6">
            {recommendations.map((r) => (
              <li key={r.id}>{r.title}</li>
            ))}
          </ul>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-medium">Audit logs</h2>
        <div className="mt-2">
          {audits.length === 0 && <div className="text-sm text-muted-foreground">No audit logs</div>}
          <ul className="list-disc pl-6">
            {audits.map((a) => (
              <li key={a.id}>{a.changed_at} — {a.entity_type} — {a.action}</li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  )
}
