import {
  CheckCircle,
  ChevronRight,
  Download,
  FileText,
  RefreshCw,
} from 'lucide-react'
import { motion } from 'framer-motion'
import type { AssessmentDef } from '../types'
import { StatusChip } from './StatusChip'

export const AssessmentHistoryTable = ({
  assessments,
  onView,
  onRetake,
  onDownload,
  onCompare,
}: {
  assessments: AssessmentDef[]
  onView?: (a: AssessmentDef) => void
  onRetake?: (a: AssessmentDef) => void
  onDownload?: (a: AssessmentDef) => void
  onCompare?: (a: AssessmentDef) => void
}) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
        <thead>
          <tr>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">Assessment</th>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">Completion Date</th>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">Health Score</th>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">Version</th>
            <th className="px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase">Doctor Reviewed</th>
            <th className="px-4 py-2.5 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
          {assessments.map((a) => (
            <tr key={a.id} className="group">
              <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{a.title}</span>
                  {a.aiEnabled && (
                    <span
                      title="AI-enabled"
                      className="inline-flex items-center justify-center rounded bg-indigo-100/60 p-0.5 text-indigo-600"
                    >
                      <span className="sr-only">AI</span>
                      <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="currentColor">
                        <path d="M12 2a2 2 0 0 1 2v5h-4V2h4Zm7.999 11H14v5h5.999A2 2 0 0 1 21 20v-5a2 2 0 0 0-1.001-1.732Z" />
                      </svg>
                    </span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                {a.completedDate ? new Date(a.completedDate).toLocaleDateString() : '—'}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{a.durationMinutes} min</td>
              <td className="px-4 py-3 text-sm font-medium text-emerald-700">{a.healthScore ?? '—'}</td>
              <td className="px-4 py-3"><StatusChip status={a.status} /></td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{a.version ?? '—'}</td>
              <td className="px-4 py-3">
                {a.doctorReviewed ? (
                  <CheckCircle className="h-4 w-4 text-emerald-500" />
                ) : (
                  <span className="text-xs text-gray-400 dark:text-gray-500">Pending</span>
                )}
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex items-center justify-end gap-1 opacity-100">
                  {onView && (
                    <motion.button
                      whileHover={{ scale: 1.08 }}
                      onClick={() => onView(a)}
                      className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800"
                      aria-label={`View ${a.title} report`}
                    >
                      <FileText className="h-4 w-4" />
                    </motion.button>
                  )}
                  {onRetake && (
                    <motion.button
                      whileHover={{ scale: 1.08 }}
                      onClick={() => onRetake(a)}
                      className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800"
                      aria-label={`Retake ${a.title}`}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </motion.button>
                  )}
                  {onDownload && (
                    <motion.button
                      whileHover={{ scale: 1.08 }}
                      onClick={() => onDownload(a)}
                      className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800"
                      aria-label={`Download ${a.title} PDF`}
                    >
                      <Download className="h-4 w-4" />
                    </motion.button>
                  )}
                  {onCompare && (
                    <motion.button
                      whileHover={{ scale: 1.08 }}
                      onClick={() => onCompare(a)}
                      className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800"
                      aria-label={`Compare ${a.title}`}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </motion.button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
