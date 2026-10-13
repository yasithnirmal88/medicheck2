import { useState, useRef, useCallback, useEffect } from 'react'

export type RecordingState = 'idle' | 'recording' | 'stopping' | 'error'

export interface UseVoiceRecorderResult {
  state: RecordingState
  errorMessage: string | null
  isSupported: boolean
  start: () => Promise<void>
  stop: () => Promise<Blob | null>
  reset: () => void
}

/**
 * Phase 5 — microphone recording hook.
 *
 * Uses the browser MediaRecorder API. Audio is held in memory only and handed
 * to the caller as a Blob on stop() — never persisted, never uploaded except
 * via the explicit transcribe call. Falls back gracefully: if the browser
 * does not support recording, `isSupported=false` and the UI offers typing.
 */
export function useVoiceRecorder(): UseVoiceRecorderResult {
  const [state, setState] = useState<RecordingState>('idle')
  const [errorMessage, setErrorMsg] = useState<string | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)

  const isSupported = typeof MediaRecorder !== 'undefined' && !!navigator.mediaDevices?.getUserMedia

  const start = useCallback(async () => {
    if (!isSupported) {
      setErrorMsg('Voice input is not supported in this browser. You can type instead.')
      setState('error')
      return
    }
    setState('recording')
    setErrorMsg(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      recorderRef.current = recorder
      recorder.start()
    } catch {
      setErrorMsg('Microphone access was denied. You can type instead.')
      setState('error')
    }
  }, [isSupported])

  const stop = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const recorder = recorderRef.current
      if (!recorder || recorder.state === 'inactive') {
        setState('idle')
        resolve(null)
        return
      }
      setState('stopping')
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        streamRef.current?.getTracks().forEach((t) => t.stop())
        streamRef.current = null
        recorderRef.current = null
        setState('idle')
        resolve(blob)
      }
      recorder.stop()
    })
  }, [])

  const reset = useCallback(() => {
    setErrorMsg(null)
    setState('idle')
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    recorderRef.current = null
  }, [])

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop())
    }
  }, [])

  return { state, errorMessage, isSupported, start, stop, reset }
}
