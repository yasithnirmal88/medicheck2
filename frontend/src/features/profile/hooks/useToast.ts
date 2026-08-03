import { useCallback } from 'react'
import toast from 'react-hot-toast'

export function useToast() {
  const success = useCallback((message: string) => {
    toast.success(message, {
      duration: 4000,
      position: 'top-right',
      style: {
        borderRadius: '12px',
        background: '#10B981',
        color: '#fff',
        fontWeight: '500',
      },
    })
  }, [])

  const error = useCallback((message: string) => {
    toast.error(message, {
      duration: 5000,
      position: 'top-right',
      style: {
        borderRadius: '12px',
        background: '#EF4444',
        color: '#fff',
        fontWeight: '500',
      },
    })
  }, [])

  const info = useCallback((message: string) => {
    toast(message, {
      duration: 3000,
      position: 'top-right',
      style: {
        borderRadius: '12px',
        background: '#3B82F6',
        color: '#fff',
        fontWeight: '500',
      },
    })
  }, [])

  const loading = useCallback((message: string) => {
    return toast.loading(message, {
      duration: Infinity,
      position: 'top-right',
      style: {
        borderRadius: '12px',
        background: '#6B7280',
        color: '#fff',
        fontWeight: '500',
      },
    })
  }, [])

  const dismiss = useCallback((id?: string) => {
    toast.dismiss(id)
  }, [])

  return { success, error, info, loading, dismiss }
}