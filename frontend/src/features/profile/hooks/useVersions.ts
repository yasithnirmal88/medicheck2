import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { restoreVersion } from '../api/extendedService'
import api from '@/lib/api'

const fetchVersions = async () => {
  const resp = await api.get('/profiles/me/versions')
  return resp.data
}

export const useVersions = () => {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['profile_versions'], queryFn: fetchVersions })
  const restore = useMutation({
    mutationFn: (v: number) => restoreVersion(v),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['profile', 'profile_versions'] })
  })
  return { ...q, restore }
}
