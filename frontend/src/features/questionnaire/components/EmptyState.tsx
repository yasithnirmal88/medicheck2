import React from 'react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

type EmptyStateProps = {
  icon?: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, action, className }) => {
  const Icon = icon
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-gray-200 bg-gray-50/60 px-6 py-10 text-center dark:border-gray-700 dark:bg-gray-800/40',
        className,
      )}
    >
      {Icon ? (
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-200 text-gray-400 dark:bg-gray-700 dark:text-gray-500">
          <Icon className="h-6 w-6" aria-hidden="true" />
        </span>
      ) : null}
      <p className="text-base font-medium text-gray-700 dark:text-gray-200">{title}</p>
      {description ? (
        <p className="max-w-sm text-sm text-gray-500 dark:text-gray-400">{description}</p>
      ) : null}
      {action ? <div>{action}</div> : null}
    </div>
  )
}

export default React.memo(EmptyState)
