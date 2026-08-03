import React from 'react'
import { cn } from '@/lib/utils'

export const logoMark =
  'data:image/svg+xml,' +
  encodeURIComponent(
    [
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none">`,
      `<rect x="4" y="4" width="40" height="40" rx="12" fill="url(#g)"/>`,
      `<path d="M14 26h5l3-7 5 13 3-8h4" stroke="white" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>`,
      `<defs><linearGradient id="g" x1="0" y1="0" x2="48" y2="48"><stop stop-color="#2563EB"/><stop offset="1" stop-color="#14B8A6"/></linearGradient></defs>`,
      `</svg>`,
    ].join(''),
  )

type LogoProps = {
  className?: string
  variant?: 'default' | 'light'
  showText?: boolean
}

const Logo: React.FC<LogoProps> = ({ className, variant = 'default', showText = true }) => {
  const textColor =
    variant === 'light'
      ? 'text-white'
      : 'text-slate-900 dark:text-white'

  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <img
        src={logoMark}
        alt="Medicheck logo"
        className="h-9 w-9 rounded-[10px] object-contain drop-shadow-sm"
        aria-hidden="true"
      />
      {showText && <span className={cn('text-xl font-bold tracking-tight', textColor)}>Medicheck</span>}
    </div>
  )
}

export default Logo