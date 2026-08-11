import { useQuery } from '@tanstack/react-query'
import {
  fetchTrajectory,
  fetchTrajectoryExplanation,
  type ExplanationRequest,
} from '../api/trajectoryService'

export function useTrajectory(limit = 20) {
  return useQuery({
    queryKey: ['trajectory', limit],
    queryFn: () => fetchTrajectory(limit),
    staleTime: 1000 * 60 * 2,
  })
}

export function useTrajectoryExplanation(req: ExplanationRequest = {}, enabled = true) {
  return useQuery({
    queryKey: ['trajectory', 'explanation', req],
    queryFn: () => fetchTrajectoryExplanation(req),
    enabled,
    staleTime: 1000 * 60 * 2,
  })
}
