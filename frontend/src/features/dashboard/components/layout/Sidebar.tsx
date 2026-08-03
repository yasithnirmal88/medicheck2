import React from 'react'
import { NavLink } from 'react-router-dom'
import { ChevronRight, ShieldPlus, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { primaryNav, secondaryNav, tertiaryNav } from './navConfig'
import type { NavItem } from './navConfig'

interface SidebarProps {
  collapsed?: boolean
  mobile?: boolean
  onClose?: () => void
}

function NavRow({
  item,
  collapsed,
  onNavigate,
}: {
  item: NavItem
  collapsed: boolean
  onNavigate?: () => void
}) {
  const inner = (isActive: boolean) => (
    <>
      <span className="flex h-5 w-5 shrink-0 items-center justify-center">
        <item.icon className="h-[18px] w-[18px]" />
      </span>
      {!collapsed ? (
        <span className="flex-1 truncate text-left">{item.label}</span>
      ) : (
        <span className="sr-only">{item.label}</span>
      )}
      {item.badge ? (
        <span className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-blue-600 px-1.5 text-[10px] font-semibold text-white">
          {item.badge}
        </span>
      ) : null}
      {isActive && !collapsed ? (
        <ChevronRight className="h-4 w-4 text-blue-600 dark:text-blue-300" />
      ) : null}
    </>
  )

  if (item.disabled || !item.to) {
    return (
      <span
        title="Coming soon"
        className={cn(
          'flex w-full cursor-not-allowed items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-400',
          'dark:text-slate-500',
          collapsed && 'justify-center px-2',
        )}
      >
        {inner(false)}
      </span>
    )
  }

  const linkClass = (isActive: boolean) =>
    cn(
      'group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
      collapsed ? 'justify-center px-2' : 'justify-start',
      isActive
        ? 'bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300'
        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-700/60 dark:hover:text-white',
    )

  return (
    <NavLink
      to={item.to}
      onClick={onNavigate}
      end={item.to === '/app'}
      title={collapsed ? item.label : undefined}
      className={({ isActive }) => linkClass(isActive)}
    >
      {({ isActive }) => inner(isActive)}
    </NavLink>
  )
}

function NavSection({
  items,
  collapsed,
  onNavigate,
}: {
  items: NavItem[]
  collapsed: boolean
  onNavigate?: () => void
}) {
  return (
    <div className={cn('space-y-1', collapsed && 'flex flex-col items-center gap-1')}>
      {items.map((item) => (
        <NavRow key={item.label} item={item} collapsed={collapsed} onNavigate={onNavigate} />
      ))}
    </div>
  )
}

function SectionLabel({ children, collapsed }: { children: React.ReactNode; collapsed: boolean }) {
  if (collapsed) return <span className="sr-only">{children}</span>
  return (
    <p className="mb-2 mt-5 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
      {children}
    </p>
  )
}

function Brand({ collapsed, mobile, onClose }: SidebarProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-2.5 border-b border-slate-200 dark:border-slate-700',
        collapsed ? 'px-2 py-4' : 'px-4 py-4',
      )}
    >
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-teal-500 text-white shadow-sm">
        <ShieldPlus className="h-5 w-5" />
      </span>
      {!collapsed ? (
        <div className="flex-1">
          <p className="text-sm font-semibold leading-tight text-slate-900 dark:text-white">Medicheck</p>
          <p className="text-[11px] text-slate-400 dark:text-slate-500">Preventive Health Platform</p>
        </div>
      ) : null}
      {mobile && !collapsed ? (
        <button
          onClick={onClose}
          aria-label="Close navigation"
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-700"
        >
          <X className="h-5 w-5" />
        </button>
      ) : null}
    </div>
  )
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed = false, mobile = false, onClose }) => {
  return (
    <div className="flex flex-col bg-white dark:bg-slate-900">
      <Brand collapsed={collapsed} mobile={mobile} onClose={onClose} />
      <div className="flex-1 overflow-y-auto py-3">
        <NavSection items={primaryNav} collapsed={collapsed} onNavigate={mobile ? onClose : undefined} />
        <SectionLabel collapsed={collapsed}>Clinical</SectionLabel>
        <NavSection items={secondaryNav} collapsed={collapsed} onNavigate={mobile ? onClose : undefined} />
        <SectionLabel collapsed={collapsed}>Account</SectionLabel>
        <NavSection items={tertiaryNav} collapsed={collapsed} onNavigate={mobile ? onClose : undefined} />
      </div>
    </div>
  )
}

export default Sidebar