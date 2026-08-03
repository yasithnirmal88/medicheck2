import React, { useState } from 'react'
import { createPortal } from 'react-dom'
import { ChevronsLeft, ChevronsRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import Sidebar from '@/features/dashboard/components/layout/Sidebar'
import TopBar from '@/features/dashboard/components/layout/TopBar'
import MobileBottomNav from '@/features/dashboard/components/layout/MobileBottomNav'
import type { DashboardNotification } from '@/features/dashboard/components/layout/NotificationPanel'

interface DashboardLayoutProps {
  children: React.ReactNode
  notifications?: DashboardNotification[]
  userName?: string
  userEmail?: string
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  notifications = [],
  userName,
  userEmail,
}) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex min-h-screen">
      <aside
        className={cn(
          'sticky top-0 hidden h-screen shrink-0 flex-col border-r border-slate-200 bg-white transition-[width] duration-200 dark:border-slate-700 dark:bg-slate-900 lg:flex',
          sidebarCollapsed ? 'w-[76px]' : 'w-64',
        )}
      >
        <Sidebar collapsed={sidebarCollapsed} />
        <button
          onClick={() => setSidebarCollapsed((c) => !c)}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="flex h-11 items-center justify-center gap-2 border-t border-slate-200 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-700 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800"
        >
          {sidebarCollapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
          {!sidebarCollapsed ? <span>Collapse</span> : null}
        </button>
      </aside>

      <ResponsiveDrawer open={mobileOpen} onClose={() => setMobileOpen(false)} />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          onMenuClick={() => setMobileOpen(true)}
          notifications={notifications}
          userName={userName}
          userEmail={userEmail}
        />
        <main className="flex-1">
          <div className="mx-auto w-full max-w-[1400px] px-4 py-6 pb-24 sm:px-6 lg:px-8 lg:pb-8">
            {children}
          </div>
        </main>
        <footer className="hidden border-t border-slate-200 px-6 py-4 text-center text-xs text-slate-400 dark:border-slate-700 dark:text-slate-500 lg:block">
          © {new Date().getFullYear()} Medicheck · Preventive Healthcare Platform
        </footer>
      </div>

      <MobileBottomNav />
    </div>
  )
}

function ResponsiveDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null
  return createPortal(
    <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
      <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={onClose} />
      <div className="absolute inset-y-0 left-0 w-64 border-r border-slate-200 bg-white shadow-xl dark:border-slate-700 dark:bg-slate-900">
        <Sidebar mobile onClose={onClose} />
      </div>
    </div>,
    document.body,
  )
}

export default DashboardLayout