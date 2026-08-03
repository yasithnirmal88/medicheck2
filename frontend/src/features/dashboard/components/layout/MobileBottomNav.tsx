import React from 'react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'

const items = [
  { label: 'Dashboard', to: '/app', icon: HomeIcon },
  { label: 'Questionnaires', to: '/questionnaires', icon: ListIcon },
  { label: 'Assessments', to: '/assessments', icon: StethoscopeIcon },
  { label: 'Timeline', to: '/timeline', icon: ClockIcon },
  { label: 'Profile', to: '/profile', icon: UserIcon },
]

export const MobileBottomNav: React.FC = () => {
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-slate-200 bg-white/95 pb-safe backdrop-blur dark:border-slate-700 dark:bg-slate-900/95 lg:hidden"
    >
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/app'}
          className={({ isActive }) =>
            cn(
              'flex flex-col items-center gap-1 py-2.5 text-[10px] font-medium',
              isActive ? 'text-blue-600 dark:text-blue-300' : 'text-slate-500 dark:text-slate-400',
            )
          }
        >
          {({ isActive }) => (
            <>
              <item.icon className={cn('h-5 w-5', isActive && 'text-blue-600 dark:text-blue-300')} />
              <span>{item.label}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}

function HomeIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className={className}>
      <path d="M3 10.5 12 3l9 7.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5 9.5V21h14V9.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
function ListIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className={className}>
      <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
function StethoscopeIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className={className}>
      <path d="M5 3v5a5 5 0 0 0 10 0V3M10 3v5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M15 8a4 4 0 0 0 4 4 3 3 0 0 1 0 6h-1a6 6 0 0 1-6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
function ClockIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className={className}>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v4l2.5 2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
function UserIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className={className}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c.8-3.5 4-5 8-5s7.2 1.5 8 5" strokeLinecap="round" />
    </svg>
  )
}

export default MobileBottomNav