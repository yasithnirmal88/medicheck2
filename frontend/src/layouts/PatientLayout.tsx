/**
 * Patient Layout - Main layout for patient users
 * 
 * Provides patient-specific navigation and structure.
 * Patients should ONLY see patient features - NO CMS, NO doctor tools.
 */

import React, { useState } from 'react'
import { createPortal } from 'react-dom'
import { NavLink, useNavigate, useLocation, Outlet } from 'react-router-dom'
import {
  Activity,
  BookOpen,
  ClipboardList,
  HeartPulse,
  LayoutDashboard,
  Layers,
  LogOut,
  Settings,
  ShieldPlus,
  Stethoscope,
  User,
  X,
  Calendar,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthContext } from '@/contexts/AuthContext'
import LoadingButton from '@/shared/ui/LoadingButton'

// Navigation items for PATIENTS ONLY
const patientNavItems = [
  {
    label: 'Dashboard',
    path: '/app',
    icon: LayoutDashboard,
  },
  {
    label: 'Health Profile',
    path: '/profile',
    icon: User,
  },
  {
    label: 'Questionnaires',
    path: '/questionnaires',
    icon: ClipboardList,
  },
  {
    label: 'Assessments',
    path: '/assessments',
    icon: Stethoscope,
  },
]

const patientSecondaryNavItems = [
  {
    label: 'Medical Timeline',
    path: '/timeline',
    icon: Activity,
  },
  {
    label: 'Recommendations',
    path: '/recommendations',
    icon: HeartPulse,
  },
  {
    label: 'Body Systems',
    path: '/body-systems',
    icon: Layers,
  },
]

const accountNavItems = [
  {
    label: 'Appointments',
    icon: Calendar,
    disabled: true,
    badge: 'Coming Soon',
  },
  {
    label: 'Settings',
    path: '/settings',
    icon: Settings,
  },
]

interface PatientLayoutProps {
  children?: React.ReactNode
}

export const PatientLayout: React.FC<PatientLayoutProps> = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)
  const { user, signOut } = useAuthContext()
  const navigate = useNavigate()

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

  const displayName = user?.displayName || user?.email || 'Patient'
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
          sidebarCollapsed ? 'w-[72px]' : 'w-64'
        )}
      >
        <SidebarContent
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
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
          <aside className="fixed left-0 top-0 h-screen w-72 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 z-50 lg:hidden">
            <SidebarContent
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
          !sidebarCollapsed && 'lg:ml-64'
        )}
      >
        {/* Top Bar */}
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/80 lg:px-6">
          <button
            onClick={() => setMobileOpen(true)}
            className="lg:hidden rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <div className="hidden lg:flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
            <span>Welcome back,</span>
            <span className="font-medium text-slate-900 dark:text-white">{displayName}</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-teal-500 to-cyan-600 text-sm font-semibold text-white">
              {initials}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 lg:p-6">
          {children ?? <Outlet />}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-200 px-6 py-4 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400 lg:text-left">
          © {new Date().getFullYear()} Medicheck · Patient Portal
        </footer>
      </div>
    </div>
  )
}

// Sidebar content component
interface SidebarContentProps {
  collapsed: boolean
  mobile?: boolean
  onToggle: () => void
  onLogout: () => void
  loggingOut: boolean
  displayName: string
  initials: string
  onCloseMobile?: () => void
}

const SidebarContent: React.FC<SidebarContentProps> = ({
  collapsed,
  mobile,
  onToggle,
  onLogout,
  loggingOut,
  displayName,
  initials,
  onCloseMobile,
}) => {
  const navClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
      collapsed && 'justify-center px-2',
      isActive
        ? 'bg-teal-50 text-teal-700 dark:bg-teal-500/15 dark:text-teal-300'
        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800/60 dark:hover:text-white'
    )

  return (
    <div className="flex h-full flex-col">
      {/* Brand */}
      <div className={cn(
        'flex items-center gap-3 border-b border-slate-200 px-4 py-4 dark:border-slate-800',
        collapsed && 'justify-center px-2'
      )}>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500 to-cyan-600 text-white shadow-sm">
          <ShieldPlus className="h-5 w-5" />
        </div>
        {!collapsed && (
          <div className="flex-1">
            <p className="text-sm font-semibold text-slate-900 dark:text-white">Medicheck</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Patient Portal</p>
          </div>
        )}
        {mobile && (
          <button
            onClick={onCloseMobile}
            className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="h-5 w-5 text-slate-500" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        <div className="space-y-1 px-3">
          {patientNavItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onCloseMobile}
              end={item.path === '/app'}
              className={navClass}
              title={collapsed ? item.label : undefined}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </div>

        {!collapsed && (
          <p className="mt-6 mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Health Tools
          </p>
        )}
        <div className="space-y-1 px-3">
          {patientSecondaryNavItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onCloseMobile}
              className={navClass}
              title={collapsed ? item.label : undefined}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </div>

        {!collapsed && (
          <p className="mt-6 mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Account
          </p>
        )}
        <div className="space-y-1 px-3">
          {accountNavItems.map((item, index) => (
            item.disabled ? (
              <span
                key={index}
                className={cn(
                  'flex cursor-not-allowed items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-400',
                  collapsed && 'justify-center px-2'
                )}
                title="Coming Soon"
              >
                <item.icon className="h-5 w-5 shrink-0" />
                {!collapsed && (
                  <span className="flex items-center gap-2">
                    <span>{item.label}</span>
                    {item.badge && (
                      <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] font-medium dark:bg-slate-700">
                        {item.badge}
                      </span>
                    )}
                  </span>
                )}
              </span>
            ) : (
              <NavLink
                key={item.path}
                to={item.path!}
                onClick={onCloseMobile}
                className={navClass}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            )
          ))}
        </div>
      </nav>

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

export default PatientLayout
