import React from 'react'
import { Save, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AutoSaveIndicatorProps {
  status: 'idle' | 'saving' | 'saved' | 'error'
  lastSaved?: Date
}

export function AutoSaveIndicator({ status, lastSaved }: AutoSaveIndicatorProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium transition-colors',
        status === 'saving' && 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-300',
        status === 'saved' && 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300',
        status === 'error' && 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300',
        status === 'idle' && 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400',
      )}
      role="status"
      aria-live="polite"
    >
      {status === 'saving' && (
        <>
          <Save className="h-3 w-3 animate-pulse" />
          <span>Saving...</span>
        </>
      )}
      {status === 'saved' && (
        <>
          <CheckCircle2 className="h-3 w-3" />
          <span>
            Saved{lastSaved ? ` ${lastSaved.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : ''}
          </span>
        </>
      )}
      {status === 'error' && (
        <>
          <span className="text-red-500">!</span>
          <span>Save failed</span>
        </>
      )}
      {status === 'idle' && (
        <>
          <Save className="h-3 w-3" />
          <span>Draft</span>
        </>
      )}
    </div>
  )
}