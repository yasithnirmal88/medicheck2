import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchProfile, savePersonalInfo, saveLifestyle, saveNutrition, fetchCompletion } from '../api/profileApi'
import type { WizardState } from '../types/wizard'
import { mapPersonalFromWizard } from '../api/profileApi'

const QUERY_KEY = ['profile'] as const

export function useProfileQuery() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: fetchProfile,
    staleTime: 1000 * 60 * 5,
    retry: 2,
  })
}

export function useSavePersonalInfo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: savePersonalInfo,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}

export function useSaveLifestyle() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: saveLifestyle,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}

export function useSaveNutrition() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: saveNutrition,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}

export function useSaveProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: WizardState) => {
      const payload = mapPersonalFromWizard(data.personal)
      return savePersonalInfo(payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}

export function useCompletionQuery() {
  return useQuery({
    queryKey: ['profile-completion'],
    queryFn: fetchCompletion,
    staleTime: 1000 * 30,
    refetchInterval: 1000 * 60,
  })
}