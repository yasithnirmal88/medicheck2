import { useAuthContext } from '../providers/AuthProvider'

export const useAuth = () => {
  const ctx = useAuthContext()
  return ctx
}
