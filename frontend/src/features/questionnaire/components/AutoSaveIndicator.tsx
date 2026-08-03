import React from 'react'
import { cn } from '@/lib/utils'

interface AutoSaveIndicatorProps {
  status: 'saving' | 'saved' | 'error'
}

const AutoSaveIndicator: React.FC<AutoSaveIndicatorProps> = ({ status }) => {
  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs',
        status === 'saving' && 'bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400',
        status === 'saved' && 'bg-green-50 dark:bg-green-950 text-green-600 dark:text-green-400',
        status === 'error' && 'bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-400'
      )}
      role="status"
      aria-live="polite"
    >
      {status === 'saving' && (
        <>
          <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Saving...
        </>
      )}
      {status === 'saved' && (
        <>
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
          Saved
        </>
      )}
      {status === 'error' && (
        <>
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Save failed
        </>
      )}
    </div>
  )
}

export default AutoSaveIndicator
