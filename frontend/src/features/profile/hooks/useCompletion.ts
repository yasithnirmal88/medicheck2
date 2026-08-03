import { useQuery } from '@tanstack/react-query'
import { getProfileCompletion } from '../api/extendedService'

export const useProfileCompletion = () => {
  return useQuery({ queryKey: ['profile_completion'], queryFn: getProfileCompletion, staleTime: 1000 * 30 })
}
