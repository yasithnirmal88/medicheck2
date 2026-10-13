/**
 * RootLayout — the single root layout for ALL authenticated routes.
 *
 * Mounted once at the route level (see routes/router.tsx) and never
 * unmounts on normal navigation, so sidebar/header chrome state
 * survives page transitions. Role-based switching happens INSIDE the
 * layout: the current user's role (from AuthContext) decides whether
 * the patient chrome (Sidebar + TopBar + MobileBottomNav) or the
 * doctor/CMS chrome (DoctorSidebar + CMS header) is rendered. Page
 * content is rendered via <Outlet />.
 *
 * Chrome data that used to be DashboardLayout props (TopBar
 * notifications, user name) is published by pages through
 * LayoutChromeContext.
 */

import React, { useState, useSyncExternalStore } from 'react'
import { createPortal } from 'react-dom'
import { Outlet, useNavigate } from 'react-router-dom'
import { ChevronsLeft, ChevronsRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthContext } from '@/contexts/AuthContext'
import Sidebar from '@/features/dashboard/components/layout/Sidebar'
import TopBar from '@/features/dashboard/components/layout/TopBar'
import MobileBottomNav from '@/features/dashboard/components/layout/MobileBottomNav'
import {
  getSidebarCollapsed,
  subscribeSidebarCollapsed,
  toggleSidebarCollapsed,
  getDoctorSidebarCollapsed,
  subscribeDoctorSidebarCollapsed,
  toggleDoctorSidebarCollapsed,
} from '@/features/dashboard/components/layout/sidebarCollapseStore'
import DoctorSidebar from '@/features/cms/components/layout/DoctorSidebar'
import { LayoutChromeProvider, useLayoutChrome } from './LayoutChromeContext'

export const RootLayout: React.FC = () => {
  const { canAccessCMS } = useAuthContext()

  return (
    <LayoutChromeProvider>
      {canAccessCMS ? <DoctorChrome /> : <PatientChrome />}
    </LayoutChromeProvider>
  )
}

export default RootLayout

// ============================================================================
// Patient chrome (formerly DashboardLayout)
// ============================================================================

const PatientChrome: React.FC = () => {
  // Collapse state is shared + persisted across navigations (see store).
  const sidebarCollapsed = useSyncExternalStore(
    subscribeSidebarCollapsed,
    getSidebarCollapsed,
    () => false, // server snapshot (SSR-safe)
  )
  const [mobileOpen, setMobileOpen] = useState(false)
  const { notifications, userName, userEmail } = useLayoutChrome()

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
          onClick={() => toggleSidebarCollapsed()}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-expanded={!sidebarCollapsed}
          className="flex h-11 items-center justify-center gap-2 border-t border-slate-200 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-700 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800"
        >
          {sidebarCollapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
          {!sidebarCollapsed ? <span>Collapse</span> : null}
        </button>
      </aside>

      <PatientDrawer open={mobileOpen} onClose={() => setMobileOpen(false)} />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          onMenuClick={() => setMobileOpen(true)}
          notifications={notifications}
          userName={userName}
          userEmail={userEmail}
        />
        <main className="flex-1">
          <div className="mx-auto w-full max-w-[1400px] px-4 py-6 pb-24 sm:px-6 lg:px-8 lg:pb-8">
            <Outlet />
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

function PatientDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
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

// ============================================================================
// Doctor/CMS chrome (formerly DoctorLayout)
// ============================================================================

const DoctorChrome: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)
  const { user, signOut } = useAuthContext()
  const navigate = useNavigate()

  // Collapse state is shared + persisted across navigations (see store).
  const collapsed = useSyncExternalStore(
    subscribeDoctorSidebarCollapsed,
    getDoctorSidebarCollapsed,
    () => false, // server snapshot (SSR-safe)
  )

  const handleLogout = async () => {
    setLoggingOut(true)
    try {
      await signOut()
      navigate('/login')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setLoggingOut(false)
    }
  }

  const displayName = user?.displayName || user?.email || 'Doctor'
  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          'hidden lg:flex flex-col fixed left-0 top-0 h-screen bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transition-all duration-200 z-30',
          collapsed ? 'w-[72px]' : 'w-64'
        )}
      >
        <DoctorSidebar
          collapsed={collapsed}
          onToggle={() => toggleDoctorSidebarCollapsed()}
          onLogout={handleLogout}
          loggingOut={loggingOut}
          displayName={displayName}
          initials={initials}
        />
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <>
          <div
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="fixed left-0 top-0 h-screen w-72 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 z-50 lg:hidden overflow-y-auto">
            <DoctorSidebar
              collapsed={false}
              onToggle={() => setMobileOpen(false)}
              onLogout={handleLogout}
              loggingOut={loggingOut}
              displayName={displayName}
              initials={initials}
              mobile
              onCloseMobile={() => setMobileOpen(false)}
            />
          </aside>
        </>
      )}

      {/* Main Content */}
      <div
        className={cn(
          'flex-1 transition-all duration-200',
          'lg:ml-[72px]',
          !collapsed && 'lg:ml-64'
        )}
      >
        {/* Top Bar */}
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-900 lg:px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
              <span className="hidden sm:inline">Doctor CMS</span>
              <span className="hidden sm:inline">·</span>
              <span className="hidden sm:inline">{displayName}</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 text-sm font-semibold text-white">
              {initials}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-200 px-6 py-4 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400">
          © {new Date().getFullYear()} Medicheck · Clinical Management System
        </footer>
      </div>
    </div>
  )
}
