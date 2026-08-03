import { useQuery } from '@tanstack/react-query'
import { fetchReports } from '../api/timelineService'

export function useReports(limit = 50, offset = 0) {
  return useQuery({ queryKey: ['reports', limit, offset], queryFn: () => fetchReports(limit, offset), staleTime: 1000 * 60 * 2 })
}

import { compareReports } from '../api/timelineService'

export function useCompareReports(id1: string, id2: string) {
  return useQuery({ queryKey: ['reports', 'compare', id1, id2], queryFn: () => compareReports(id1, id2), enabled: !!id1 && !!id2 })
}
