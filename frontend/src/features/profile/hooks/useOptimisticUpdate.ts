import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

export function useOptimisticUpdate<T>(
  queryKey: readonly unknown[],
  getData: () => T | undefined,
  updateData: (prev: T | undefined, newData: T) => T,
) {
  const qc = useQueryClient()

  const optimisticUpdate = useCallback(
    (newData: T, onSuccess: () => void, onError: () => void) => {
      const previous = getData()
      qc.setQueryData(queryKey, updateData(previous, newData))

      return {
        onSuccess: () => {
          qc.invalidateQueries({ queryKey })
          onSuccess()
        },
        onError: () => {
          if (previous !== undefined) {
            qc.setQueryData(queryKey, previous)
          }
          onError()
        },
      }
    },
    [qc, queryKey, getData, updateData],
  )

  return { optimisticUpdate }
}