import React from 'react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import { Link } from 'react-router-dom'

export default function BodySystemDashboard() {
  const systems = [
    'Cardiovascular',
    'Kidney',
    'Liver',
    'Respiratory',
    'Digestive',
    'Endocrine',
    'Neurological',
    'Eyes',
    'Skin',
    'Blood',
    'Musculoskeletal',
    'Mental Health',
  ]

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto p-4">
        <h1 className="text-2xl font-semibold mb-4">Body Systems</h1>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {systems.map((s) => (
            <Card key={s}>
              <div className="flex flex-col">
                <div className="font-medium">{s}</div>
                <div className="text-xs text-gray-500 mt-1">Status: Unknown</div>
                <div className="text-xs text-gray-500 mt-1">Last assessment: —</div>
                <div className="mt-3">
                  <Link to={`/body-systems/${s.toLowerCase().replace(/ /g, '-')}`} className="text-indigo-600 text-sm">Open</Link>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </AppLayout>
  )
}
