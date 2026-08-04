import React, { useState } from 'react'
import { Clock, Search } from 'lucide-react'
import { ContentLayout, Tabs, StatusBadge, EmptyState, TableSkeleton, Pagination, DataTable } from '../components/ContentLayout'
import { useAuditLogs, useAuditStats } from '../hooks/useCmsQueries'
import type { AuditLogEntry, AuditStats } from '../types'

const auditTabs = [
  { id: 'logs', label: 'Audit Logs' },
  { id: 'timeline', label: 'Timeline' },
  { id: 'stats', label: 'Stats' },
]

export const AuditViewerPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('logs')
  const [skip, setSkip] = useState(0)
  const [logSearch, setLogSearch] = useState('')
  const [timelineEntityType, setTimelineEntityType] = useState('')
  const [timelineEntityId, setTimelineEntityId] = useState('')

  const filterParams: Record<string, unknown> = { skip, limit: 20 }
  if (logSearch) filterParams.search = logSearch

  const { data: auditData, isLoading: logsLoading } = useAuditLogs(filterParams)
  const { data: stats, isLoading: statsLoading } = useAuditStats(30)

  const auditLogs = auditData?.items ?? []
  const total = auditData?.total ?? 0

  const logColumns = [
    { key: 'actor_id', header: 'Actor', render: (item: AuditLogEntry) => <span className="font-mono text-xs">{item.actor_id || '-'}</span> },
    { key: 'entity_type', header: 'Entity Type', render: (item: AuditLogEntry) => <StatusBadge status={item.entity_type} /> },
    { key: 'entity_id', header: 'Entity ID', render: (item: AuditLogEntry) => <span className="font-mono text-xs">{item.entity_id || '-'}</span> },
    { key: 'action', header: 'Action', render: (item: AuditLogEntry) => <span className="capitalize">{item.action.replace(/_/g, ' ')}</span> },
    { key: 'changed_at', header: 'Changed At', render: (item: AuditLogEntry) => item.changed_at ? new Date(item.changed_at).toLocaleString() : '-' },
    { key: 'method', header: 'Method', render: (item: AuditLogEntry) => <span className="font-mono text-xs">{item.method || '-'}</span> },
    { key: 'path', header: 'Path', render: (item: AuditLogEntry) => <span className="font-mono text-xs text-slate-500">{item.path || '-'}</span> },
    { key: 'ip_address', header: 'IP', render: (item: AuditLogEntry) => <span className="text-xs">{item.ip_address || '-'}</span> },
  ]

  return (
    <ContentLayout title="Audit Viewer" description="View audit logs, timelines, and statistics">
      <Tabs tabs={auditTabs} active={activeTab} onChange={setActiveTab} />

      {activeTab === 'logs' && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center gap-2">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={logSearch}
                onChange={(e) => { setLogSearch(e.target.value); setSkip(0) }}
                placeholder="Search logs..."
                className="w-full pl-8 pr-3 py-2 text-sm border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
          </div>
          <DataTable
            columns={logColumns}
            data={auditLogs}
            keyExtractor={(item: AuditLogEntry) => item.id}
            loading={logsLoading}
            emptyMessage="No audit logs found"
          />
          <Pagination skip={skip} limit={20} total={total} onChange={setSkip} />
        </div>
      )}

      {activeTab === 'timeline' && (
        <div className="mt-6 space-y-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Entity Type</label>
                <input type="text" value={timelineEntityType} onChange={(e) => setTimelineEntityType(e.target.value)} placeholder="e.g. question" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Entity ID</label>
                <input type="text" value={timelineEntityId} onChange={(e) => setTimelineEntityId(e.target.value)} placeholder="Entity UUID" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
              </div>
            </div>
          </div>
          {!timelineEntityType || !timelineEntityId ? (
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
              <EmptyState title="Enter entity details" description="Provide entity type and ID to view timeline" icon={<Clock className="w-8 h-8" />} />
            </div>
          ) : (
            <AuditTimelineSection entityType={timelineEntityType} entityId={timelineEntityId} />
          )}
        </div>
      )}

      {activeTab === 'stats' && (
        <div className="mt-6 space-y-6">
          {statsLoading ? (
            <TableSkeleton rows={6} />
          ) : !stats ? (
            <EmptyState title="No stats available" />
          ) : (
            <AuditStatsSection stats={stats} />
          )}
        </div>
      )}
    </ContentLayout>
  )
}

const AuditTimelineSection: React.FC<{ entityType: string; entityId: string }> = ({ entityType, entityId }) => {
  const { data: timeline, isLoading } = useAuditLogs({ entity_type: entityType, entity_id: entityId })

  if (isLoading) return <TableSkeleton />
  if (!timeline?.items?.length) return <EmptyState title="No timeline events" description="No audit events found for this entity" />

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
      <div className="space-y-3">
        {timeline.items.map((entry) => (
          <div key={entry.id} className="flex items-start gap-3 p-3 border-l-2 border-blue-500 ml-2">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <StatusBadge status={entry.action} />
                <span className="text-xs text-slate-500">{entry.changed_at ? new Date(entry.changed_at).toLocaleString() : '-'}</span>
              </div>
              <p className="text-sm text-slate-900 dark:text-white">
                Actor: <span className="font-mono text-xs">{entry.actor_id || 'system'}</span>
                {entry.reason && <span className="text-slate-500 ml-2">— {entry.reason}</span>}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const AuditStatsSection: React.FC<{ stats: AuditStats }> = ({ stats }) => (
  <>
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <p className="text-sm text-slate-500">Period (days)</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-white">{stats.period_days}</p>
      </div>
      <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <p className="text-sm text-slate-500">Total Actions</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-white">{stats.total_actions}</p>
      </div>
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
        <h4 className="font-semibold text-slate-900 dark:text-white mb-3">By Action</h4>
        <div className="space-y-2">
          {Object.entries(stats.by_action).map(([action, count]) => (
            <div key={action} className="flex items-center justify-between text-sm">
              <span className="capitalize text-slate-700 dark:text-slate-300">{action.replace(/_/g, ' ')}</span>
              <span className="font-semibold text-slate-900 dark:text-white">{count}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
        <h4 className="font-semibold text-slate-900 dark:text-white mb-3">By Entity Type</h4>
        <div className="space-y-2">
          {Object.entries(stats.by_entity_type).map(([type, count]) => (
            <div key={type} className="flex items-center justify-between text-sm">
              <span className="text-slate-700 dark:text-slate-300">{type}</span>
              <span className="font-semibold text-slate-900 dark:text-white">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>

    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
      <h4 className="font-semibold text-slate-900 dark:text-white mb-3">Top Actors</h4>
      {!stats.top_actors?.length ? (
        <EmptyState title="No actor data" />
      ) : (
        <div className="space-y-2">
          {stats.top_actors.map((actor, _i) => (
            <div key={actor.actor_id} className="flex items-center justify-between text-sm">
              <span className="font-mono text-xs text-slate-700 dark:text-slate-300">{actor.actor_id}</span>
              <span className="font-semibold text-slate-900 dark:text-white">{actor.actions} actions</span>
            </div>
          ))}
        </div>
      )}
    </div>
  </>
)
