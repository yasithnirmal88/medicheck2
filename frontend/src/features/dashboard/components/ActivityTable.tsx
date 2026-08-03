import React, { useMemo, useState } from 'react'
import type { LucideIcon } from 'lucide-react'
import { ChevronLeft, ChevronRight, FileText, FlaskConical, Search, Stethoscope } from 'lucide-react'
import { cn } from '@/lib/utils'
import Card from './Card'
import EmptyState from './EmptyState'
import { TableRowSkeleton } from './LoadingSkeleton'
import { formatRelative } from '../utils/format'

export type ActivityRow = {
  id: string
  date?: string
  action: string
  type: 'questionnaire' | 'report' | 'assessment' | 'lab'
  status: 'completed' | 'in_progress' | 'pending' | 'failed'
}

interface ActivityTableProps {
  rows: ActivityRow[]
  loading?: boolean
}

const typeMeta: Record<ActivityRow['type'], { icon: LucideIcon; label: string }> = {
  questionnaire: { icon: Stethoscope, label: 'Questionnaire' },
  assessment: { icon: FileText, label: 'Assessment' },
  lab: { icon: FlaskConical, label: 'Lab Report' },
  report: { icon: FileText, label: 'Health Report' },
}

const PAGESIZE = 5

const statusColor: Record<ActivityRow['status'], string> = {
  completed: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300',
  in_progress: 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300',
  pending: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300',
  failed: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300',
}

const statusLabel: Record<ActivityRow['status'], string> = {
  completed: 'Completed',
  in_progress: 'In progress',
  pending: 'Pending',
  failed: 'Failed',
}

const typeColor: Record<ActivityRow['type'], string> = {
  questionnaire: 'bg-blue-100 text-blue-600 dark:bg-blue-500/15 dark:text-blue-300',
  assessment: 'bg-teal-100 text-teal-600 dark:bg-teal-500/15 dark:text-teal-300',
  lab: 'bg-amber-100 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300',
  report: 'bg-violet-100 text-violet-600 dark:bg-violet-500/15 dark:text-violet-300',
}

export const ActivityTable: React.FC<ActivityTableProps> = ({ rows, loading }) => {
  const [query, setQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<'all' | ActivityRow['type']>('all')
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return rows.filter((row) => {
      const matchesType = typeFilter === 'all' || row.type === typeFilter
      const matchesQuery = !q || row.action.toLowerCase().includes(q)
      return matchesType && matchesQuery
    })
  }, [rows, query, typeFilter])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGESIZE))
  const safePage = Math.min(page, pageCount)
  const pageRows = filtered.slice((safePage - 1) * PAGESIZE, safePage * PAGESIZE)

  const totalPages = pageCount

  return (
    <Card className="flex h-full flex-col">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Recent Activity</h3>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value)
                setPage(1)
              }}
              placeholder="Search…"
              aria-label="Search activity"
              className="h-8 w-36 rounded-lg border border-slate-200 bg-slate-50 pl-7 pr-2 text-xs text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 sm:w-44"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value as 'all' | ActivityRow['type'])
              setPage(1)
            }}
            aria-label="Filter by type"
            className="h-8 rounded-lg border border-slate-200 bg-slate-50 px-2 text-xs text-slate-700 focus:border-blue-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <option value="all">All types</option>
            <option value="questionnaire">Questionnaire</option>
            <option value="assessment">Assessment</option>
            <option value="lab">Lab Report</option>
          </select>
        </div>
      </div>

      <div className="mt-4 flex-1">
        {loading ? (
          <TableRowSkeleton rows={4} />
        ) : pageRows.length === 0 ? (
          <EmptyState icon={Search} title="No activity yet" description="Your health events will appear here." />
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-100 dark:border-slate-700">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-400 dark:border-slate-700 dark:bg-slate-800">
                  <th className="px-3 py-2.5 font-medium">Date</th>
                  <th className="px-3 py-2.5 font-medium">Action</th>
                  <th className="hidden px-3 py-2.5 font-medium sm:table-cell">Type</th>
                  <th className="px-3 py-2.5 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {pageRows.map((row) => {
                  const type = typeMeta[row.type]
                  return (
                    <tr key={row.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                      <td className="whitespace-nowrap px-3 py-2.5 text-xs text-slate-500 dark:text-slate-400">
                        {formatRelative(row.date)}
                      </td>
                      <td className="px-3 py-2.5">
                        <div className="flex items-center gap-2">
                          <span className={cn('hidden h-6 w-6 items-center justify-center rounded-md sm:flex', typeColor[row.type])}>
                            <type.icon className="h-3.5 w-3.5" />
                          </span>
                          <span className="font-medium text-slate-700 dark:text-slate-200">{row.action}</span>
                        </div>
                      </td>
                      <td className="hidden px-3 py-2.5 sm:table-cell">
                        <span className="text-xs text-slate-500 dark:text-slate-400">{type.label}</span>
                      </td>
                      <td className="px-3 py-2.5">
                        <span className={cn('inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium', statusColor[row.status])}>
                          {statusLabel[row.status]}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {!loading && pageRows.length > 0 ? (
        <div className="mt-3 flex items-center justify-between">
          <p className="text-xs text-slate-400">
            Showing {(safePage - 1) * PAGESIZE + 1}–{Math.min(safePage * PAGESIZE, filtered.length)} of {filtered.length}
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={safePage <= 1}
              aria-label="Previous page"
              className="inline-flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-40 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-700"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="px-1 text-xs text-slate-500">
              {safePage} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={safePage >= totalPages}
              aria-label="Next page"
              className="inline-flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-40 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-700"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      ) : null}
    </Card>
  )
}

export default ActivityTable