import { cn } from '@/lib/utils'
import { CheckCircle, ChevronDown, Circle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import type { AssessmentDef } from '../types'
import { assessmentCategories } from '../mockData'

export const HealthJourneyStepper = ({ assessments }: { assessments: Pick<AssessmentDef, 'status'>[] }) => {
  const completed = assessments.filter((a) => a.status === 'completed').length
  const steps = [
    { label: 'Profile Completed', done: completed >= 0 },
    { label: 'Questionnaires', done: completed >= 0 },
    { label: 'Assessments', done: completed >= 1 },
    { label: 'Laboratory Results', done: completed >= 2 },
    { label: 'AI Analysis', done: completed >= 3 },
    { label: 'Health Report', done: completed >= 3 },
    { label: 'Recommendations', done: completed >= 3 },
  ]
  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Your health journey</p>
      <div className="relative flex items-center justify-between">
        <div className="absolute left-0 top-3 h-0.5 w-full -z-10 bg-slate-200 dark:bg-slate-700" />
        {steps.map((s, i) => (
          <div key={s.label} className="flex flex-col items-center">
            <motion.div
              className={cn(
                'flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold',
                s.done
                  ? 'bg-emerald-500 text-white'
                  : i === completed
                    ? 'bg-indigo-500 text-white'
                    : 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
              )}
            >
              {s.done ? <CheckCircle className="h-3.5 w-3.5" /> : <Circle className="h-3.5 w-3.5" />}
            </motion.div>
            <span className="mt-1.5 max-w-[90px] text-center text-[10px] text-gray-600 dark:text-gray-300">
              {s.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export const AssessmentCategories = ({ onCategoryClick }: { onCategoryClick?: (cat: (typeof assessmentCategories)[number]) => void }) => {
  const [open, setOpen] = useState(true)
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Assessment Categories</p>
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
          aria-label={open ? 'Collapse' : 'Expand'}
        >
          <ChevronDown className={cn('h-4 w-4 transition-transform', open && 'rotate-180')} />
        </button>
      </div>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4"
          >
            {assessmentCategories.map((c) => (
              <motion.button
                key={c.id}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onCategoryClick?.(c)}
                className={cn(
                  'flex flex-col items-center gap-1.5 rounded-xl border border-slate-200/80 bg-white p-3 text-center',
                  'dark:border-slate-700/60 dark:bg-slate-800/60',
                  'transition-shadow hover:shadow-md',
                )}
              >
                <span
                  className={cn(
                    'flex h-8 w-8 items-center justify-center rounded-lg text-white shadow-md shadow-black/5',
                    `bg-gradient-to-br ${c.gradient}`,
                  )}
                >
                  <span className="sr-only">{c.title}</span>
                  <span className="text-xs">★</span>
                </span>
                <span className="text-xs font-medium text-gray-800 dark:text-gray-200">{c.title}</span>
                <span className="text-[10px] text-gray-500">{c.count} available</span>
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
