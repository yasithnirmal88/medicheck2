import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

type Theme = 'light' | 'dark'
type ThemePreference = Theme | 'system'

const STORAGE_KEY = 'medicheck-theme'

function getSystemTheme(): Theme {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function readPreference(): ThemePreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'light' || stored === 'dark' || stored === 'system') return stored
  } catch {
    // ignore storage errors
  }
  return 'system'
}

function resolveTheme(preference: ThemePreference): Theme {
  return preference === 'system' ? getSystemTheme() : preference
}

type ThemeContextValue = {
  theme: Theme
  preference: ThemePreference
  toggle: () => void
  cyclePreference: () => void
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: 'light',
  preference: 'system',
  toggle: () => {},
  cyclePreference: () => {},
})

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [preference, setPreference] = useState<ThemePreference>(() =>
    window.matchMedia?.('(prefers-color-scheme: dark)') ? readPreference() : 'light',
  )
  const [theme, setTheme] = useState<Theme>(() =>
    window.matchMedia?.('(prefers-color-scheme: dark)') ? resolveTheme(readPreference()) : 'light',
  )

  useEffect(() => {
    const mql = window.matchMedia?.('(prefers-color-scheme: dark)')
    if (!mql) return
    const onChange = () => {
      if (preference === 'system') setTheme(getSystemTheme())
    }
    mql.addEventListener?.('change', onChange)
    return () => mql.removeEventListener?.('change', onChange)
  }, [preference])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem(STORAGE_KEY, preference)
    } catch {
      // ignore storage errors
    }
  }, [theme, preference])

  const toggle = useCallback(() => {
    setPreference((p) => {
      const next = resolveTheme(p) === 'dark' ? 'light' : 'dark'
      setTheme(next)
      return next
    })
  }, [])

  const cyclePreference = useCallback(() => {
    setPreference((p) => {
      const next: ThemePreference = p === 'system' ? 'light' : p === 'light' ? 'dark' : 'system'
      setTheme(next === 'system' ? getSystemTheme() : next)
      return next
    })
  }, [])

  const value = useMemo<ThemeContextValue>(
    () => ({ theme, preference, toggle, cyclePreference }),
    [theme, preference, toggle, cyclePreference],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export const useTheme = () => useContext(ThemeContext)

export default ThemeProvider