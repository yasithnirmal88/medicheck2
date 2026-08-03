import React, { useState } from 'react'
import { History, GitCompare, RotateCcw } from 'lucide-react'
import toast from 'react-hot-toast'
import { ContentLayout, StatusBadge, EmptyState, TableSkeleton, FormField } from '../components/ContentLayout'
import { useSnapshots } from '../hooks/useCmsQueries'
import type { VersionSnapshot } from '../types'

export const VersionHistoryPage: React.FC = () => {
  const [entityType, setEntityType] = useState('')
  const [entityId, setEntityId] = useState('')
  const [compareFrom, setCompareFrom] = useState<string | null>(null)
  const [compareTo, setCompareTo] = useState<string | null>(null)

  const { data: snapshots, isLoading } = useSnapshots(entityType, entityId)

  const fromSnapshot = snapshots?.find((s) => s.id === compareFrom)
  const toSnapshot = snapshots?.find((s) => s.id === compareTo)

  const diffs: { field: string; old_value: unknown; new_value: unknown }[] = []
  if (fromSnapshot && toSnapshot && compareFrom !== compareTo) {
    const fromData = fromSnapshot.snapshot ?? {}
    const toData = toSnapshot.snapshot ?? {}
    const allKeys = new Set([...Object.keys(fromData), ...Object.keys(toData)])
    for (const key of allKeys) {
      const oldVal = JSON.stringify(fromData[key as keyof typeof fromData])
      const newVal = JSON.stringify(toData[key as keyof typeof toData])
      if (oldVal !== newVal) {
        diffs.push({ field: key, old_value: fromData[key as keyof typeof fromData], new_value: toData[key as keyof typeof toData] })
      }
    }
  }

  return (
    <ContentLayout title="Version History" description="Browse snapshots, compare versions, and roll back content">
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
        <h3 className="font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
          <History className="w-4 h-4 text-blue-600" /> Search Snapshots
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FormField label="Entity Type">
            <input
              type="text"
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              placeholder="e.g. question"
              className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white"
            />
          </FormField>
          <FormField label="Entity ID">
            <input
              type="text"
              value={entityId}
              onChange={(e) => setEntityId(e.target.value)}
              placeholder="Entity UUID"
              className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white"
            />
          </FormField>
        </div>
      </div>

      {entityType && entityId && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
            <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Snapshots</h3>
            {isLoading ? (
              <TableSkeleton />
            ) : !snapshots?.length ? (
              <EmptyState title="No snapshots" description="No version snapshots found for this entity" />
            ) : (
              <div className="space-y-3">
                {snapshots.map((s) => (
                  <div key={s.id} className="p-4 border border-slate-200 dark:border-slate-800 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded font-semibold">
                          v{s.version}
                        </span>
                        <StatusBadge status={s.snapshot_type} />
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => setCompareFrom(compareFrom === s.id ? null : s.id)}
                          className={`px-2 py-1 text-xs rounded transition ${compareFrom === s.id ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 hover:bg-slate-200'}`}
                        >
                          From
                        </button>
                        <button
                          onClick={() => setCompareTo(compareTo === s.id ? null : s.id)}
                          className={`px-2 py-1 text-xs rounded transition ${compareTo === s.id ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 hover:bg-slate-200'}`}
                        >
                          To
                        </button>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500">
                      {s.reason ? `Reason: ${s.reason}` : ''} | By: {s.created_by ?? 'system'} | {s.created_at ? new Date(s.created_at).toLocaleString() : ''}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
            <h3 className="font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <GitCompare className="w-4 h-4 text-blue-600" /> Compare
            </h3>
            {!compareFrom || !compareTo ? (
              <EmptyState title="Select two versions" description="Choose a From and To version on each snapshot card" />
            ) : compareFrom === compareTo ? (
              <EmptyState title="Same version" description="Select two different versions to compare" />
            ) : !diffs.length ? (
              <EmptyState title="No differences" description="The selected versions are identical" />
            ) : (
              <div className="space-y-3">
                {diffs.map((diff, i) => (
                  <div key={i} className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg">
                    <p className="text-sm font-medium text-slate-900 dark:text-white mb-1">{diff.field}</p>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2 bg-red-50 dark:bg-red-900/20 rounded">
                        <span className="text-red-600 font-medium">Old:</span>
                        <pre className="text-red-700 dark:text-red-300 mt-0.5 whitespace-pre-wrap">{JSON.stringify(diff.old_value, null, 1) || 'null'}</pre>
                      </div>
                      <div className="p-2 bg-emerald-50 dark:bg-emerald-900/20 rounded">
                        <span className="text-emerald-600 font-medium">New:</span>
                        <pre className="text-emerald-700 dark:text-emerald-300 mt-0.5 whitespace-pre-wrap">{JSON.stringify(diff.new_value, null, 1) || 'null'}</pre>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {(!entityType || !entityId) && (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
          <EmptyState title="Enter search criteria" description="Provide entity type and entity ID to load version history" icon={<History className="w-8 h-8" />} />
        </div>
      )}
    </ContentLayout>
  )
}
