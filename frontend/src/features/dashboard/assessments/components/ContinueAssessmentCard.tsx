import { cn } from '@/lib/utils'
import type { AssessmentDef } from '../types'
import { Clock, FileText, Save, Zap } from 'lucide-react'
import { motion } from 'framer-motion'

export const ContinueAssessmentCard = ({
  assessment,
  onResume,
  onDiscard,
}: {
  assessment: AssessmentDef
  onResume?: () => void
  onDiscard?: () => void
}) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3, ease: 'easeOut' }}
  >
    <div
      className={cn(
        'relative rounded-2xl border border-slate-200/80 bg-white shadow-sm',
        'dark:border-slate-700/60 dark:bg-slate-800/70',
        'p-5',
      )}
    >
      <div className="absolute inset-0 -z-10">
        <div
          className={cn(
            'absolute -right-16 -top-16 h-64 w-64 rounded-full blur-3xl opacity-20',
            assessment.gradient,
          )}
        />
      </div>

      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Continue in progress assessment</h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Resume where you left off — your answers are saved.
          </p>
        </div>
        <span
          className={cn(
            'inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-medium',
            'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300',
          )}
        >
          {assessment.progressPct ?? 0}% complete
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 text-sm text-gray-600 dark:text-gray-300">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-indigo-500" />
          <span>Est. {assessment.durationMinutes} min left</span>
        </div>
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-indigo-500" />
          <span>{assessment.questionsCount} questions</span>
        </div>
        <div className="flex items-center gap-2">
          <Save className="h-4 w-4 text-indigo-500" />
          <span>Last saved {assessment.lastSaved ?? 'recently'}</span>
        </div>
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-indigo-500" />
          <span>{assessment.bodySystems.length} body systems</span>
        </div>
      </div>

      <div className="mt-5 flex items-center gap-3">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onResume}
          className={cn(
            'rounded-xl px-5 py-2 text-sm font-medium text-white shadow-sm shadow-black/5',
            `bg-gradient-to-r ${assessment.gradient}`,
            'hover:brightness-110',
          )}
        >
          Resume Assessment
        </motion.button>
        {onDiscard && (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onDiscard}
            className="rounded-xl border border-slate-200 px-5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Discard
          </motion.button>
        )}
      </div>
    </div>
  </motion.div>
)
