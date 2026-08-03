import React from 'react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'

export default function RecommendationCenter() {
  // placeholder — recommendations are fetched from the report/decision endpoints in real usage
  const recs: any[] = []

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto p-4">
        <h1 className="text-2xl font-semibold mb-4">Recommendation Center</h1>
        <Card>
          {recs.length === 0 ? (
            <div className="text-sm text-gray-500">No active recommendations</div>
          ) : (
            <ul>
              {recs.map((r) => (
                <li key={r.id}>{r.text}</li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
