/**
 * LayoutChromeContext — page → root-layout communication.
 *
 * Previously, DashboardLayout accepted `notifications`, `userName` and
 * `userEmail` props, which forced pages to render the layout themselves.
 * Now the RootLayout renders the TopBar at the route level, so pages
 * publish that data through this context instead. The RootLayout's
 * TopBar consumes it; pages that don't publish simply leave the
 * defaults (empty notifications, auth-derived user info).
 */

import React, { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { DashboardNotification } from '@/features/dashboard/components/layout/NotificationPanel'

interface LayoutChromeState {
  notifications: DashboardNotification[]
  userName?: string
  userEmail?: string
}

interface LayoutChromeContextValue extends LayoutChromeState {
  setChrome: (patch: Partial<LayoutChromeState>) => void
}

const LayoutChromeContext = createContext<LayoutChromeContextValue | null>(null)

export const LayoutChromeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, setState] = useState<LayoutChromeState>({ notifications: [] })

  const setChrome = useCallback((patch: Partial<LayoutChromeState>) => {
    setState((prev) => ({ ...prev, ...patch }))
  }, [])

  const value = useMemo<LayoutChromeContextValue>(
    () => ({ ...state, setChrome }),
    [state, setChrome],
  )

  return (
    <LayoutChromeContext.Provider value={value}>
      {children}
    </LayoutChromeContext.Provider>
  )
}

export function useLayoutChrome(): LayoutChromeContextValue {
  const ctx = useContext(LayoutChromeContext)
  if (!ctx) {
    throw new Error('useLayoutChrome must be used within LayoutChromeProvider')
  }
  return ctx
}

/**
 * Optional accessor for pages that render outside the provider tree
 * (e.g. tests). Returns undefined instead of throwing.
 */
export function useLayoutChromeOptional(): LayoutChromeContextValue | null {
  return useContext(LayoutChromeContext)
}
