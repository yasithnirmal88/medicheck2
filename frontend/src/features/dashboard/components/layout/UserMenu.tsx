import React, { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAuth, signOut } from 'firebase/auth'
import { ChevronDown, HelpCircle, LogOut, Settings, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/hooks/useAuth'
import { initials } from '../../utils/format'

export interface UserMenuProps {
  name?: string
  email?: string
}

export const UserMenu: React.FC<UserMenuProps> = ({ name, email }) => {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const { user } = useAuth()

  useEffect(() => {
    if (!open) return
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  const displayName = name || user?.displayName || 'User'
  const displayEmail = email || user?.email || ''

  const onLogout = async () => {
    try {
      await signOut(getAuth())
      window.location.href = '/login'
    } catch (err) {
      console.error(err)
    }
  }

  const go = (path: string) => {
    setOpen(false)
    navigate(path)
  }

  const items = [
    { label: 'Profile', icon: User, onClick: () => go('/profile') },
    { label: 'Settings', icon: Settings, onClick: () => go('/profile') },
    { label: 'Help', icon: HelpCircle, onClick: () => setOpen(false) },
  ]

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-full p-1 pr-2 transition-colors hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/60 dark:hover:bg-slate-700"
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-teal-500 text-xs font-semibold text-white">
          {initials(displayName) || 'MK'}
        </span>
        <ChevronDown className={cn('h-4 w-4 text-slate-400 transition-transform', open && 'rotate-180')} />
      </button>

      {open ? (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-60 overflow-hidden rounded-2xl border border-slate-200 bg-white py-1.5 shadow-xl dark:border-slate-700 dark:bg-slate-800"
        >
          <div className="border-b border-slate-100 px-4 py-3 dark:border-slate-700">
            <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">{displayName}</p>
            {displayEmail ? (
              <p className="truncate text-xs text-slate-500 dark:text-slate-400">{displayEmail}</p>
            ) : null}
          </div>
          <div className="py-1">
            {items.map((item) => (
              <button
                key={item.label}
                role="menuitem"
                onClick={item.onClick}
                className="flex w-full items-center gap-2.5 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </button>
            ))}
            <button
              role="menuitem"
              onClick={onLogout}
              className="flex w-full items-center gap-2.5 px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default UserMenu