import React, { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, Layers, GitBranch, Network, CheckCircle2,
  History, BookOpen, FileText, Activity, Stethoscope, Beaker,
  ScanLine, Heart, Apple, Dumbbell, Pill,
  Shield, Users, Search, Settings, GitMerge,
  ChevronLeft, ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  label: string
  path: string
  icon: React.ComponentType<{ className?: string }>
  children?: NavItem[]
}

const navGroups: { label: string; items: NavItem[] }[] = [
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
      { label: 'Body Systems', path: '/cms/body-systems', icon: LayoutDashboard },
      { label: 'Symptoms', path: '/cms/symptoms', icon: Stethoscope },
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

export const CMSLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950">
      <aside className={cn(
        'bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col transition-all duration-200',
        collapsed ? 'w-16' : 'w-64',
      )}>
        <div className="flex items-center justify-between px-3 py-3 border-b border-slate-200 dark:border-slate-800">
          {!collapsed && (
            <div>
              <span className="text-xs font-bold text-blue-600 dark:text-blue-400 tracking-wider uppercase">Medicheck</span>
              <h2 className="font-bold text-slate-900 dark:text-white text-sm">Doctor CMS</h2>
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            {collapsed ? <ChevronRight className="w-4 h-4 text-slate-500" /> : <ChevronLeft className="w-4 h-4 text-slate-500" />}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto p-2 space-y-4">
          {navGroups.map((group) => (
            <div key={group.label}>
              {!collapsed && (
                <p className="px-3 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">
                  {group.label}
                </p>
              )}
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      className={({ isActive }) => cn(
                        'flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition',
                        collapsed && 'justify-center px-2',
                        isActive
                          ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 font-semibold'
                          : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60',
                      )}
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </NavLink>
                  )
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      <main className="flex-1 overflow-x-auto">
        <Outlet />
      </main>
    </div>
  )
}
