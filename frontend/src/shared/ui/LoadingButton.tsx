import React from 'react'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

type LoadingButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean
  loadingText?: string
  variant?: 'primary' | 'google' | 'ghost'
  fullWidth?: boolean
  startIcon?: React.ReactNode
}

const TextWithIcon: React.FC<{ icon?: React.ReactNode; children: React.ReactNode }> = ({ icon, children }) => (
  <>
    {icon}
    {children}
  </>
)

const base =
  'inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-all ' +
  'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500/60 active:scale-[0.98] ' +
  'disabled:cursor-not-allowed disabled:opacity-60'

const variants = {
  primary:
    'bg-blue-600 text-white shadow-sm shadow-blue-600/20 hover:bg-blue-700 enabled:hover:shadow-md enabled:hover:shadow-blue-600/30 focus:ring-blue-500 dark:bg-blue-600 dark:hover:bg-blue-500',
  google:
    'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 hover:text-slate-900 shadow-sm ' +
    'dark:bg-slate-800 dark:text-slate-100 dark:border-slate-600 dark:hover:bg-slate-700 focus:ring-slate-400',
  ghost: 'bg-transparent text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-slate-800 focus:ring-blue-500',
}

const LoadingButton: React.FC<LoadingButtonProps> = ({
  loading = false,
  loadingText,
  variant = 'primary',
  fullWidth = false,
  startIcon,
  className = '',
  children,
  disabled,
  ...rest
}) => {
  return (
    <button
      className={cn(base, variants[variant], fullWidth && 'w-full', className)}
      disabled={disabled || loading}
      aria-busy={loading}
      {...rest}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
      {loading ? (loadingText ?? children) : <TextWithIcon icon={startIcon}>{children}</TextWithIcon>}
    </button>
  )
}

export default React.memo(LoadingButton)