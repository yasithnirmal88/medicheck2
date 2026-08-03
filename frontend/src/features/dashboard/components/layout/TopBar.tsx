import React, { useState } from 'react'
import { Search, ShieldPlus } from 'lucide-react'
import ThemeToggle from '@/shared/ui/ThemeToggle'
import { NotificationPanel } from './NotificationPanel'
import { UserMenu } from './UserMenu'
import type { DashboardNotification } from './NotificationPanel'

interface TopBarProps {
  onMenuClick: () => void
  notifications: DashboardNotification[]
  userName?: string
  userEmail?: string
}

export const TopBar: React.FC<TopBarProps> = ({ onMenuClick, notifications, userName, userEmail }) => {
  const [query, setQuery] = useState('')

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-700 dark:bg-slate-900/80">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6">
        <button
          onClick={onMenuClick}
          aria-label="Open navigation"
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700 lg:hidden"
        >
          <MenuIcon />
          <span className="sr-only">Menu</span>
        </button>

        <span className="flex items-center gap-2 lg:hidden">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-teal-500 text-white">
            <ShieldPlus className="h-4 w-4" />
          </span>
        </span>

        <div className="relative ml-1 hidden flex-1 max-w-md sm:block">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search assessments, reports, recommendations…"
            aria-label="Search"
            className="h-9 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm text-slate-700 placeholder:text-slate-400 transition-colors focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:focus:bg-slate-800"
          />
        </div>

        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          <NotificationPanel items={notifications} />
          <UserMenu name={userName} email={userEmail} />
        </div>
      </div>
    </header>
  )
}

function MenuIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
      <path strokeLinecap="round" d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  )
}

export default TopBar