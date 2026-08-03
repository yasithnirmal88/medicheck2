import React, { useEffect, useRef, useState } from 'react'
import type { LucideIcon } from 'lucide-react'
import { Bell, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import EmptyState from '../EmptyState'
import { formatRelative } from '../../utils/format'

export interface DashboardNotification {
  id: string
  title: string
  description: string
  time?: string
  tone?: 'info' | 'warning' | 'success' | 'danger'
  icon: LucideIcon
  read?: boolean
}

interface NotificationPanelProps {
  items: DashboardNotification[]
  className?: string
}

const toneText: Record<string, string> = {
  info: 'text-blue-600 dark:text-blue-300',
  warning: 'text-amber-600 dark:text-amber-300',
  success: 'text-emerald-600 dark:text-emerald-300',
  danger: 'text-red-600 dark:text-red-300',
}

export const NotificationPanel: React.FC<NotificationPanelProps> = ({ items, className }) => {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const unread = items.filter((i) => !i.read).length

  useEffect(() => {
    if (!open) return
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  return (
    <div className={cn('relative', className)} ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={`Notifications${unread ? `, ${unread} unread` : ''}`}
        aria-expanded={open}
        className="relative inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
      >
        <Bell className="h-[18px] w-[18px]" />
        {unread > 0 ? (
          <span className="absolute right-1.5 top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
            {unread}
          </span>
        ) : null}
      </button>

      {open ? (
        <div className="absolute right-0 z-50 mt-2 w-80 origin-top-right overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl dark:border-slate-700 dark:bg-slate-800 sm:w-96">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-slate-700">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Notifications</h3>
            {unread > 0 ? (
              <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-500/15 dark:text-blue-300">
                {unread} unread
              </span>
            ) : null}
          </div>

          <div className="max-h-[22rem] overflow-y-auto">
            {items.length === 0 ? (
              <div className="p-4">
                <EmptyState icon={CheckCircle2} title="You're all caught up" description="No new notifications." />
              </div>
            ) : (
              <ul className="divide-y divide-slate-100 dark:divide-slate-700">
                {items.slice(0, 6).map((item) => (
                  <li key={item.id} className="flex gap-3 px-4 py-3">
                    <span
                      className={cn(
                        'mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg',
                        toneText[item.tone ?? 'info'] || 'text-blue-600',
                        'bg-slate-100 dark:bg-slate-700',
                      )}
                    >
                      <item.icon className="h-4 w-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">{item.title}</p>
                        {!item.read ? <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" /> : null}
                      </div>
                      <p className="mt-0.5 line-clamp-2 text-xs text-slate-500 dark:text-slate-400">{item.description}</p>
                      <p className="mt-1 text-[11px] text-slate-400 dark:text-slate-500">{formatRelative(item.time)}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default NotificationPanel