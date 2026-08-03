import React from 'react'
import { cn } from '@/lib/utils'
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react'

type AlertVariant = 'error' | 'success' | 'info' | 'warning'

type AlertProps = {
  variant?: AlertVariant
  title?: string
  children: React.ReactNode
  className?: string
  live?: boolean
}

const config: Record<AlertVariant, { icon: React.ReactNode; classes: string; iconClass: string }> = {
  error: {
    icon: <AlertCircle className="h-4 w-4" />,
    classes: 'border-red-200 bg-red-50 text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300',
    iconClass: 'text-red-500 dark:text-red-400',
  },
  success: {
    icon: <CheckCircle2 className="h-4 w-4" />,
    classes: 'border-green-200 bg-green-50 text-green-800 dark:border-green-500/30 dark:bg-green-500/10 dark:text-green-300',
    iconClass: 'text-green-500 dark:text-green-400',
  },
  warning: {
    icon: <AlertTriangle className="h-4 w-4" />,
    classes: 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300',
    iconClass: 'text-amber-500 dark:text-amber-400',
  },
  info: {
    icon: <Info className="h-4 w-4" />,
    classes: 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-300',
    iconClass: 'text-blue-500 dark:text-blue-400',
  },
}

const Alert: React.FC<AlertProps> = ({ variant = 'error', title, children, className, live = false }) => {
  const c = config[variant]
  return (
    <div
      role={live ? 'alert' : undefined}
      className={cn('flex items-start gap-2.5 rounded-xl border px-3.5 py-3 text-sm', c.classes, className)}
    >
      <span className={cn('mt-0.5 shrink-0', c.iconClass)} aria-hidden="true">
        {c.icon}
      </span>
      <div className="space-y-0.5">
        {title && <p className="font-semibold">{title}</p>}
        <div className="leading-relaxed">{children}</div>
      </div>
    </div>
  )
}

export default React.memo(Alert)