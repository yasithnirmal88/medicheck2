import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTheme } from '../../providers/ThemeProvider'
import { getAuth, signOut } from 'firebase/auth'
import { cn } from '@/lib/utils'

const TopNav: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { theme, toggle } = useTheme()

  const onSignOut = async () => {
    const auth = getAuth()
    try {
      await signOut(auth)
      window.location.href = '/login'
    } catch (err) {
      console.error(err)
    }
  }

  const navLinks = [
    { path: '/', label: 'Dashboard' },
    { path: '/questionnaires', label: 'Questionnaires' },
    { path: '/profile', label: 'Profile' },
  ]

  return (
    <div className="flex items-center justify-between px-4 py-2 border-b bg-white dark:bg-slate-900">
      <div className="flex items-center gap-6">
        <div className="text-lg font-semibold">Medicheck</div>
        <nav className="hidden md:flex items-center gap-4">
          {navLinks.map((link) => (
            <button
              key={link.path}
              onClick={() => navigate(link.path)}
              className={cn(
                'text-sm transition-colors min-h-[44px] px-2',
                location.pathname === link.path || location.pathname.startsWith(link.path + '/')
                  ? 'text-indigo-600 font-medium'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              )}
            >
              {link.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="flex items-center gap-4">
        <button onClick={toggle} aria-label="Toggle theme" className="px-2 py-1 min-h-[44px]">
          {theme === 'dark' ? '🌙' : '☀️'}
        </button>
        <button onClick={onSignOut} className="px-3 py-1 text-sm text-red-600 min-h-[44px]">
          Sign out
        </button>
      </div>
    </div>
  )
}

export default TopNav
