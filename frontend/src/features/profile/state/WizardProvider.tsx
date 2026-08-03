import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import debounce from 'lodash/debounce'
import type { WizardState, SectionKey } from '../types/wizard'
import { createDefaultState, mergeDraft } from './defaults'

const STORAGE_KEY = 'medicheck-profile-draft-v1'
const VERSIONS_KEY = 'medicheck-profile-versions'
const AUTO_SAVE_INTERVAL = 5000

interface WizardContextValue {
  state: WizardState
  setSection: (key: SectionKey, value: unknown) => void
  saveDraft: () => void
  clearDraft: () => void
  isHydrated: boolean
  saveVersion: () => void
  autoSaveStatus: 'idle' | 'saving' | 'saved' | 'error'
  lastSavedAt: Date | null
  hasUnsavedChanges: boolean
  resumeFromDraft: () => boolean
  resetDraft: () => void
}

const WizardContext = createContext<WizardContextValue | null>(null)

function readDraft(): Partial<WizardState> | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as Partial<WizardState>) : null
  } catch {
    return null
  }
}

function readVersions(): { savedAt: string; state: WizardState }[] {
  try {
    return JSON.parse(localStorage.getItem(VERSIONS_KEY) ?? '[]') as {
      savedAt: string
      state: WizardState
    }[]
  } catch {
    return []
  }
}

export const WizardProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isHydrated, setIsHydrated] = useState(false)
  const [state, setState] = useState<WizardState>(createDefaultState)
  const [autoSaveStatus, setAutoSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null)
  const stateRef = useRef(state)
  stateRef.current = state
  const lastSavedRef = useRef<WizardState | null>(null)

  useEffect(() => {
    const draft = readDraft()
    if (draft) setState((prev) => mergeDraft(prev, draft))
    setIsHydrated(true)
  }, [])

  const persist = useCallback(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stateRef.current))
      setAutoSaveStatus('saved')
      setLastSavedAt(new Date())
      lastSavedRef.current = stateRef.current
    } catch {
      setAutoSaveStatus('error')
    }
  }, [])

  const autoPersist = useMemo(() => debounce(persist, 600), [persist])

  useEffect(() => {
    if (isHydrated) autoPersist()
  }, [state, isHydrated, autoPersist])

  useEffect(() => {
    const interval = setInterval(() => {
      if (isHydrated && stateRef.current !== lastSavedRef.current) {
        persist()
      }
    }, AUTO_SAVE_INTERVAL)
    return () => clearInterval(interval)
  }, [isHydrated, persist])

  useEffect(() => {
    const handler = () => {
      persist()
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [persist])

  const setSection = useCallback((key: SectionKey, value: unknown) => {
    setState((prev) => ({ ...prev, [key]: value as never }))
    setAutoSaveStatus('saving')
  }, [])

  const saveDraft = useCallback(() => {
    autoPersist.flush()
  }, [autoPersist])

  const clearDraft = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      // ignore storage errors
    }
  }, [])

  const saveVersion = useCallback(() => {
    try {
      const versions = readVersions()
      versions.push({ savedAt: new Date().toISOString(), state: stateRef.current })
      localStorage.setItem(VERSIONS_KEY, JSON.stringify(versions.slice(-10)))
    } catch {
      // ignore storage errors
    }
  }, [])

  const hasUnsavedChanges = useMemo(() => {
    if (!lastSavedRef.current) return true
    return JSON.stringify(state) !== JSON.stringify(lastSavedRef.current)
  }, [state])

  const resumeFromDraft = useCallback((): boolean => {
    const draft = readDraft()
    if (draft) {
      setState((prev) => mergeDraft(prev, draft))
      return true
    }
    return false
  }, [])

  const resetDraft = useCallback(() => {
    clearDraft()
    setState(createDefaultState())
    lastSavedRef.current = null
    setAutoSaveStatus('idle')
  }, [clearDraft])

  const value = useMemo<WizardContextValue>(
    () => ({
      state,
      setSection,
      saveDraft,
      clearDraft,
      isHydrated,
      saveVersion,
      autoSaveStatus,
      lastSavedAt,
      hasUnsavedChanges,
      resumeFromDraft,
      resetDraft,
    }),
    [state, setSection, saveDraft, clearDraft, isHydrated, saveVersion, autoSaveStatus, lastSavedAt, hasUnsavedChanges, resumeFromDraft, resetDraft],
  )

  return <WizardContext.Provider value={value}>{children}</WizardContext.Provider>
}

export const useWizard = (): WizardContextValue => {
  const ctx = useContext(WizardContext)
  if (!ctx) throw new Error('useWizard must be used within WizardProvider')
  return ctx
}