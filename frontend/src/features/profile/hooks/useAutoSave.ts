import { useEffect, useRef, useCallback } from 'react'
import { useWizard } from '../state/WizardProvider'

const AUTO_SAVE_INTERVAL = 5000
const DRAFT_KEY = 'medicheck-profile-draft-v1'

export function useAutoSave(enabled: boolean = true) {
  const { state, saveDraft } = useWizard()
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const lastSaveRef = useRef<number>(0)

  const save = useCallback(() => {
    const now = Date.now()
    if (now - lastSaveRef.current < 1000) return
    lastSaveRef.current = now
    try {
      localStorage.setItem(DRAFT_KEY, JSON.stringify(state))
    } catch {
      // localStorage quota exceeded or unavailable
    }
  }, [state])

  useEffect(() => {
    if (!enabled) return
    intervalRef.current = setInterval(save, AUTO_SAVE_INTERVAL)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [enabled, save])

  useEffect(() => {
    const handleBeforeUnload = () => {
      save()
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [save])

  return { save, saveDraft }
}