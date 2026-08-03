import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchMyProfile, savePersonalInfo } from '../api/profileService'

export const useProfile = () => {
  const qc = useQueryClient()
  const query = useQuery({ queryKey: ['profile'], queryFn: fetchMyProfile, staleTime: 1000 * 60 * 2 })

  const savePersonal = useMutation({
    mutationFn: (payload: Record<string, unknown>) => savePersonalInfo(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['profile'] })
  })

  return { ...query, savePersonal }
}
