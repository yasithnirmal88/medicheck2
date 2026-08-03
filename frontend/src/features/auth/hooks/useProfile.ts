import { useQuery } from '@tanstack/react-query'
import { fetchProfile } from './useAuthService'

export const useProfile = () => useQuery({ queryKey: ['profile'], queryFn: fetchProfile, staleTime: 1000 * 60 * 5 })
