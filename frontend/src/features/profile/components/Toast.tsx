import React from 'react'
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ToastProps {
  message: string
  type?: 'success' | 'error' | 'info'
  onDismiss?: () => void
}

export function Toast({ message, type = 'info', onDismiss }: ToastProps) {
  const iconMap = {
    success: <CheckCircle className="h-5 w-5 text-emerald-500" />,
    error: <AlertCircle className="h-5 w-5 text-red-500" />,
    info: <Info className="h-5 w-5 text-blue-500" />,
  }

  const bgMap = {
    success: 'border-emerald-200 bg-emerald-50 dark:border-emerald-800/50 dark:bg-emerald-900/20',
    error: 'border-red-200 bg-red-50 dark:border-red-800/50 dark:bg-red-900/20',
    info: 'border-blue-200 bg-blue-50 dark:border-blue-800/50 dark:bg-blue-900/20',
  }

  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-xl border p-4 shadow-lg backdrop-blur-sm',
        bgMap[type],
      )}
      role="alert"
      aria-live="polite"
    >
      <span className="shrink-0">{iconMap[type]}</span>
      <p className="flex-1 text-sm text-slate-700 dark:text-slate-300">{message}</p>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          aria-label="Dismiss notification"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}