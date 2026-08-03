import React from 'react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import { useVersions } from '../hooks/useVersions'

export default function ProfileVersions() {
  const { data: versions, isLoading, restore } = useVersions()

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto p-4 space-y-4">
        <Card>
          <h1 className="text-2xl">Profile Versions</h1>
          <p className="mt-2 text-sm">View history and restore previous versions of your profile.</p>
        </Card>

        <Card>
          {isLoading && <div>Loading...</div>}
          {!isLoading && (!versions || versions.length === 0) && <div>No versions yet</div>}
          {!isLoading && versions && (
            <ul className="space-y-3">
              {versions.map((v: any, idx: number) => (
                <li key={idx} className="flex items-start justify-between">
                  <div>
                    <div className="text-sm font-medium">Version {versions.length - idx}</div>
                    <div className="text-xs text-gray-600">Sections: {Object.keys(v).join(', ')}</div>
                  </div>
                  <div className="flex gap-2">
                    <button className="px-2 py-1 bg-indigo-600 text-white rounded" onClick={() => restore.mutate(versions.length - idx)}>
                      Restore
                    </button>
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
