import React from 'react'
import { Link } from 'react-router-dom'
import { Layers, GitBranch, Network, CheckCircle2, Clock, ArrowRight } from 'lucide-react'
import { ContentLayout, StatsCard, CardSkeleton, DataTable, StatusBadge } from '../components/ContentLayout'
import { useDashboardOverview, useRecentActivity } from '../hooks/useCmsQueries'
import type { RecentActivity } from '../types'

const quickActions = [
  { to: '/cms/builder', label: 'Question Builder', desc: 'Build and manage questionnaire groups and questions', icon: Layers, color: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600' },
  { to: '/cms/rules', label: 'Rule Builder', desc: 'Create and evaluate clinical decision rules', icon: GitBranch, color: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600' },
  { to: '/cms/knowledge-graph', label: 'Knowledge Graph', desc: 'Visualize entity relationships and graph topology', icon: Network, color: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600' },
  { to: '/cms/approvals', label: 'Publishing', desc: 'Manage approvals, reviews, and publish content', icon: CheckCircle2, color: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600' },
]

export const CMSDashboardPage: React.FC = () => {
  const { data: overview, isLoading: overviewLoading } = useDashboardOverview()
  const { data: recentActivity, isLoading: activityLoading } = useRecentActivity()

  const totalQuestions = overview?.by_type?.question ?? 0
  const activeDiseases = overview?.by_type?.disease ?? 0
  const pendingApprovals = overview?.workflow_pending?.approvals ?? 0
  const publishedVersions = overview?.by_status?.question?.published ?? 0

  const activityColumns = [
    { key: 'actor_id', header: 'Actor', render: (item: RecentActivity) => <span className="font-mono text-xs">{item.actor_id}</span> },
    { key: 'entity_type', header: 'Entity Type', render: (item: RecentActivity) => <StatusBadge status={item.entity_type} /> },
    { key: 'action', header: 'Action', render: (item: RecentActivity) => <span className="capitalize">{item.action.replace(/_/g, ' ')}</span> },
    { key: 'changed_at', header: 'Changed At', render: (item: RecentActivity) => item.changed_at ? new Date(item.changed_at).toLocaleString() : '-' },
    { key: 'reason', header: 'Reason', render: (item: RecentActivity) => item.reason ?? '-' },
  ]

  return (
    <ContentLayout title="CMS Dashboard" description="Doctor CMS & Clinical Governance Portal">
      {overviewLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <CardSkeleton key={i} />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard label="Total Questions" value={totalQuestions} icon={<Layers className="w-5 h-5" />} color="bg-blue-50 dark:bg-blue-900/20" />
          <StatsCard label="Active Diseases" value={activeDiseases} icon={<Layers className="w-5 h-5" />} color="bg-amber-50 dark:bg-amber-900/20" />
          <StatsCard label="Pending Approvals" value={pendingApprovals} icon={<CheckCircle2 className="w-5 h-5" />} color="bg-emerald-50 dark:bg-emerald-900/20" />
          <StatsCard label="Published Versions" value={publishedVersions} icon={<Clock className="w-5 h-5" />} color="bg-purple-50 dark:bg-purple-900/20" />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600" /> Recent Activity
          </h3>
          <DataTable
            columns={activityColumns}
            data={recentActivity ?? []}
            keyExtractor={(item: RecentActivity) => item.id}
            loading={activityLoading}
            emptyMessage="No recent activity"
          />
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Quick Actions</h3>
          {quickActions.map((action) => {
            const Icon = action.icon
            return (
              <Link
                key={action.to}
                to={action.to}
                className="group block bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-blue-500 transition shadow-sm"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`p-2.5 rounded-lg ${action.color}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition" />
                </div>
                <h4 className="font-semibold text-slate-900 dark:text-white text-sm mb-1">{action.label}</h4>
                <p className="text-xs text-slate-500 dark:text-slate-400">{action.desc}</p>
              </Link>
            )
          })}
        </div>
      </div>
    </ContentLayout>
  )
}
