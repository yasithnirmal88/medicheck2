import React from 'react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import { useCompareReports } from '../hooks/useTimeline'
import { useSearchParams } from 'react-router-dom'

export default function ComparePage() {
  const [searchParams] = useSearchParams()
  const id1 = searchParams.get('a') || ''
  const id2 = searchParams.get('b') || ''
  const { data: compare, isLoading } = useCompareReports(id1, id2)

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto p-4">
        <h1 className="text-2xl font-semibold mb-4">Compare Assessments</h1>
        <Card>
          {isLoading ? (
            <div>Loading comparison...</div>
          ) : !compare ? (
            <div className="text-sm text-gray-500">Provide two report ids via query params ?a=ID1&b=ID2</div>
          ) : (
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-medium">Added Conditions</h2>
                <ul className="mt-2 list-disc list-inside text-sm">
                  {compare.added_conditions && compare.added_conditions.length > 0 ? (
                    compare.added_conditions.map((c: string) => <li key={c}>{c}</li>)
                  ) : (
                    <li className="text-gray-500">None</li>
                  )}
                </ul>
              </div>

              <div>
                <h2 className="text-lg font-medium">Removed Conditions</h2>
                <ul className="mt-2 list-disc list-inside text-sm">
                  {compare.removed_conditions && compare.removed_conditions.length > 0 ? (
                    compare.removed_conditions.map((c: string) => <li key={c}>{c}</li>)
                  ) : (
                    <li className="text-gray-500">None</li>
                  )}
                </ul>
              </div>

              <div>
                <h2 className="text-lg font-medium">Added Advices</h2>
                <ul className="mt-2 list-disc list-inside text-sm">
                  {compare.added_advices && compare.added_advices.length > 0 ? (
                    compare.added_advices.map((c: string) => <li key={c}>{c}</li>)
                  ) : (
                    <li className="text-gray-500">None</li>
                  )}
                </ul>
              </div>
            </div>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
