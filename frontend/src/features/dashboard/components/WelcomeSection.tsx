import React from 'react'
import { motion } from 'framer-motion'
import { CalendarClock, ShieldCheck, Sparkles, TrendingUp } from 'lucide-react'
import { Skeleton } from './LoadingSkeleton'

interface WelcomeSectionProps {
  greeting: string
  name: string
  healthScore: number | null
  nextAssessment?: string
  lastActivity?: string
  loading?: boolean
}

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

export const WelcomeSection: React.FC<WelcomeSectionProps> = ({
  greeting,
  name,
  healthScore,
  nextAssessment,
  lastActivity,
  loading,
}) => {
  return (
    <motion.div variants={fadeUp} initial="hidden" animate="show">
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600 via-blue-600 to-teal-500 p-6 text-white shadow-lg sm:p-8">
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-white/10 blur-2xl" />
        <div className="pointer-events-none absolute -bottom-20 right-24 h-56 w-56 rounded-full bg-teal-300/20 blur-2xl" />

        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex-1">
            <p className="flex items-center gap-2 text-sm font-medium text-blue-50">
              <Sparkles className="h-4 w-4" />
              Medicheck · AI Preventive Health
            </p>
            {loading ? (
              <div className="mt-3 space-y-2">
                <Skeleton className="h-8 w-56 bg-white/20" />
                <Skeleton className="h-4 w-80 bg-white/20" />
              </div>
            ) : (
              <>
                <h1 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
                  {greeting}, {name || 'there'}
                </h1>
                <p className="mt-1.5 text-sm text-blue-50">Welcome back to Medicheck · {todayLine()}</p>
              </>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 lg:flex lg:items-center lg:gap-4">
            <Metric icon={ShieldCheck} label="Today's status" value={statusLabel(healthScore)} />
            <Metric icon={CalendarClock} label="Next assessment" value={nextAssessment || '—'} />
            <Metric icon={TrendingUp} label="Last activity" value={lastActivity || '—'} />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function todayLine(): string {
  return new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })
}

function statusLabel(score: number | null): string {
  if (score === null) return 'Complete profile'
  if (score >= 80) return 'Excellent'
  if (score >= 60) return 'Good'
  if (score >= 40) return 'Moderate'
  return 'Needs attention'
}

function Metric({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string }) {
  return (
    <div className="rounded-xl bg-white/15 p-3 ring-1 ring-white/20 backdrop-blur-sm">
      <div className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-blue-100">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className="mt-1 text-sm font-semibold text-white">{value}</p>
    </div>
  )
}

export default WelcomeSection