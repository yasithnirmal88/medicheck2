import { cn } from '@/lib/utils'
import { Bot, CheckCircle, ClipboardList, TestTube, User, Lightbulb } from 'lucide-react'
import { motion } from 'framer-motion'

type TimelineItem = {
  id: string
  type: 'completed' | 'started' | 'profile' | 'lab' | 'rec' | 'ai'
  title: string
  meta?: string
  date: string
  icon: string
  iconBg: string
}

const ICON_MAP: Record<TimelineItem['type'], JSX.Element> = {
  completed: <CheckCircle className="h-4 w-4 text-white" />,
  started: <Bot className="h-4 w-4 text-white" />,
  profile: <User className="h-4 w-4 text-white" />,
  lab: <TestTube className="h-4 w-4 text-white" />,
  rec: <Lightbulb className="h-4 w-4 text-white" />,
  ai: <Bot className="h-4 w-4 text-white" />,
}

export const AssessmentTimeline = ({ items }: { items: TimelineItem[] }) => {
  const resolved = items.map((it) => ({ ...it, iconEl: ICON_MAP[it.type] ?? <ClipboardList className="h-4 w-4 text-white" /> }))
  return (
    <div className="relative">
      <div className="absolute left-5 top-0 bottom-0 w-px bg-slate-300 dark:bg-slate-700" />
      <div className="space-y-6">
        {resolved.map((item, i) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06, duration: 0.28, ease: 'easeOut' }}
            className="relative pl-14"
          >
            <div
              className={cn(
                'absolute left-0 flex h-9 w-9 items-center justify-center rounded-xl',
                'shadow-md shadow-black/5',
                item.iconBg,
              )}
            >
              {item.iconEl}
            </div>
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.title}</p>
                {item.meta && <p className="text-xs text-gray-500 dark:text-gray-400">{item.meta}</p>}
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                {new Date(item.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
