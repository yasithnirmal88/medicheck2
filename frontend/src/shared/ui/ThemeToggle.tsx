import React from 'react'
import { useTheme } from '@/providers/ThemeProvider'
import { cn } from '@/lib/utils'
import { Moon, Sun } from 'lucide-react'

const ThemeToggle: React.FC<{ className?: string }> = ({ className }) => {
  const { theme, toggle } = useTheme()

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      className={cn(
        'inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 ',
        'transition-colors hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500/60 ',
        'dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700',
        className,
      )}
    >
      {theme === 'dark' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
      <span className="sr-only">Toggle theme</span>
    </button>
  )
}

export default React.memo(ThemeToggle)