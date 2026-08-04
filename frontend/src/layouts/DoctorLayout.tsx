/**
 * Doctor Layout - Main layout for doctor/clinical CMS users
 * 
 * Provides CMS-specific navigation and structure.
 * Doctors/Clinical staff should see clinical tools - NO patient dashboard.
 */

import React, { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  Activity,
  Beaker,
  BookOpen,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Dumbbell,
  FileText,
  GitBranch,
  GitMerge,
  Heart,
  History,
  Layers,
  LayoutDashboard,
  LogOut,
  Network,
  Apple,
  Pill,
  ScanLine,
  Search,
  Settings,
  Shield,
  Stethoscope,
  Users,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthContext } from '@/contexts/AuthContext'
import LoadingButton from '@/shared/ui/LoadingButton'

// CMS Navigation items
const cmsNavGroups = [
  {
    label: 'Overview',
    items: [
      { label: 'Dashboard', path: '/cms/dashboard', icon: LayoutDashboard },
    ],
  },
  {
    label: 'Content',
    items: [
      { label: 'Questions', path: '/cms/questions', icon: FileText },
      { label: 'Question Groups', path: '/cms/question-groups', icon: Layers },
      { label: 'Diseases', path: '/cms/diseases', icon: Activity },
      { label: 'Body Systems', path: '/cms/body-systems', icon: Stethoscope },
      { label: 'Symptoms', path: '/cms/symptoms', icon: Heart },
      { label: 'Indicators', path: '/cms/indicators', icon: Activity },
      { label: 'Lab Tests', path: '/cms/lab-tests', icon: Beaker },
      { label: 'Imaging', path: '/cms/imaging', icon: ScanLine },
      { label: 'Recommendations', path: '/cms/recommendations', icon: Heart },
      { label: 'Lifestyle Advice', path: '/cms/lifestyle', icon: Apple },
      { label: 'Exercise Programs', path: '/cms/exercise', icon: Dumbbell },
      { label: 'Nutrition Advice', path: '/cms/nutrition', icon: Apple },
      { label: 'Evidence', path: '/cms/evidence', icon: BookOpen },
      { label: 'Templates', path: '/cms/templates', icon: FileText },
      { label: 'Medications', path: '/cms/medications', icon: Pill },
      { label: 'Guidelines', path: '/cms/guidelines', icon: BookOpen },
      { label: 'Decision Rules', path: '/cms/rules', icon: GitBranch },
      { label: 'Thresholds', path: '/cms/thresholds', icon: Activity },
    ],
  },
  {
    label: 'Builders',
    items: [
      { label: 'Question Builder', path: '/cms/builder', icon: Layers },
      { label: 'Rule Builder', path: '/cms/rules-builder', icon: GitBranch },
      { label: 'Knowledge Graph', path: '/cms/graph', icon: Network },
    ],
  },
  {
    label: 'Workflow',
    items: [
      { label: 'Publishing', path: '/cms/publishing', icon: GitMerge },
      { label: 'Approvals', path: '/cms/approvals', icon: CheckCircle2 },
      { label: 'Version History', path: '/cms/history', icon: History },
    ],
  },
  {
    label: 'Operations',
    items: [
      { label: 'Audit Logs', path: '/cms/audit', icon: Shield },
      { label: 'Users & Roles', path: '/cms/users', icon: Users },
      { label: 'Search', path: '/cms/search', icon: Search },
      { label: 'Settings', path: '/cms/settings', icon: Settings },
    ],
  },
]

interface DoctorLayoutProps {
  children?: React.ReactNode
}

export const DoctorLayout: React.FC<DoctorLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
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
        <SidebarContent
          collapsed={collapsed}
          onToggle={() => setCollapsed(!collapsed)}
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
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-200 px-6 py-4 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400">
          © {new Date().getFullYear()} Medicheck · Clinical Management System
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
  return (
    <div className="flex h-full flex-col">
      {/* Brand */}
      <div className={cn(
        'flex items-center gap-3 border-b border-slate-200 px-4 py-4 dark:border-slate-800',
        collapsed && 'justify-center px-2'
      )}>
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
        {cmsNavGroups.map((group) => (
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

export default DoctorLayout
