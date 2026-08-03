import { Award, CalendarDays, CheckCircle, Clock, FileText } from 'lucide-react'
import Card from '@/shared/ui/Card'
import { cn } from '@/lib/utils'

export const AssessmentStatistics = ({
  completed,
  inProgress,
  averageScore,
  nextAssessment,
}: {
  completed: number
  inProgress: number
  averageScore: number
  nextAssessment: string
}) => {
  const cards = [
    {
      label: 'Completed Assessments',
      value: completed,
      icon: <CheckCircle className="h-5 w-5 text-emerald-500" />,
      tone: 'emerald',
    },
    {
      label: 'In Progress',
      value: inProgress,
      icon: <Clock className="h-5 w-5 text-indigo-500" />,
      tone: 'indigo',
    },
    {
      label: 'Average Health Score',
      value: `${averageScore}%`,
      icon: <Award className="h-5 w-5 text-amber-500" />,
      tone: 'amber',
    },
    {
      label: 'Next Recommended Assessment',
      value: nextAssessment,
      icon: <CalendarDays className="h-5 w-5 text-cyan-500" />,
      tone: 'cyan',
    },
  ]
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((c) => (
        <Card
          key={c.label}
          className={cn(
            'border border-slate-200/80 bg-white/70 backdrop-blur-sm',
            'dark:border-slate-700/60 dark:bg-slate-800/60',
          )}
        >
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white shadow dark:bg-slate-900/50">
              {c.icon}
            </div>
            <div className="truncate">
              <p className="text-xs text-gray-500 dark:text-gray-400">{c.label}</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">{c.value}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}
