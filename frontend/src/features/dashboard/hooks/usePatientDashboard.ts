import { useQuery } from '@tanstack/react-query'
import { fetchProfile, fetchCompletion, fetchSessions } from '../api/patientService'

export function useProfile() {
  return useQuery({ queryKey: ['profile'], queryFn: fetchProfile, staleTime: 1000 * 60 * 5 })
}

export function useCompletion() {
  return useQuery({ queryKey: ['profile', 'completion'], queryFn: fetchCompletion, staleTime: 1000 * 60 * 2 })
}

export function useSessions() {
  return useQuery({ queryKey: ['sessions'], queryFn: fetchSessions, staleTime: 1000 * 30 })
}
