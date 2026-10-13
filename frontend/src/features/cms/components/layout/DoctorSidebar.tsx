/**
 * DoctorSidebar — CMS/clinical navigation sidebar.
 *
 * Extracted from the former DoctorLayout so the single RootLayout can
 * render role-specific navigation. Rendering (brand, nav groups, collapse
 * toggle, sign-out) is byte-for-byte the old DoctorLayout SidebarContent.
 */

import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  LogOut,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { doctorNavGroups } from './doctorNavConfig'
import LoadingButton from '@/shared/ui/LoadingButton'

interface DoctorSidebarProps {
  collapsed: boolean
  mobile?: boolean
  onToggle: () => void
  onLogout: () => void
  loggingOut: boolean
  displayName: string
  initials: string
  onCloseMobile?: () => void
}

export const DoctorSidebar: React.FC<DoctorSidebarProps> = ({
  collapsed,
  mobile,
  onToggle,
  onLogout,
  loggingOut,
  displayName,
  initials,
  onCloseMobile,
}) => {
  return (
    <div className="flex h-full flex-col">
      {/* Brand */}
      <div
        className={cn(
          'flex items-center gap-3 border-b border-slate-200 px-4 py-4 dark:border-slate-800',
          collapsed && 'justify-center px-2',
        )}
      >
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-sm">
          <LayoutDashboard className="h-5 w-5" />
        </div>
        {!collapsed && (
          <div className="flex-1">
            <p className="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">Medicheck</p>
            <p className="text-sm font-semibold text-slate-900 dark:text-white">Doctor CMS</p>
          </div>
        )}
        {mobile && !collapsed && (
          <button
            onClick={onCloseMobile}
            className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <svg className="h-5 w-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 space-y-4">
        {doctorNavGroups.map((group) => (
          <div key={group.label}>
            {!collapsed && (
              <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                {group.label}
              </p>
            )}
            <div className="space-y-0.5 px-3">
              {group.items.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={onCloseMobile}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition',
                        collapsed && 'justify-center px-2',
                        isActive
                          ? 'bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300 font-semibold'
                          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-white'
                      )
                    }
                    title={collapsed ? item.label : undefined}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                  </NavLink>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        className={cn(
          'flex items-center gap-2 border-t border-slate-200 px-3 py-3 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-700 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white',
          collapsed ? 'justify-center' : 'justify-end',
          mobile && 'hidden',
        )}
      >
        {collapsed ? <ChevronRight className="h-4 w-4" /> : (
          <>
            <span>Collapse</span>
            <ChevronLeft className="h-4 w-4" />
          </>
        )}
      </button>

      {/* Footer */}
      <div className="border-t border-slate-200 p-3 dark:border-slate-800">
        {!collapsed ? (
          <LoadingButton
            variant="ghost"
            onClick={onLogout}
            loading={loggingOut}
            loadingText="Signing out..."
            className="w-full justify-start text-slate-600 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400"
            startIcon={<LogOut className="h-4 w-4" />}
          >
            Sign Out
          </LoadingButton>
        ) : (
          <button
            onClick={onLogout}
            className="flex w-full items-center justify-center rounded-xl p-2.5 text-slate-500 hover:bg-slate-100 hover:text-red-600 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-red-400"
            title="Sign Out"
          >
            <LogOut className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  )
}

export default DoctorSidebar
