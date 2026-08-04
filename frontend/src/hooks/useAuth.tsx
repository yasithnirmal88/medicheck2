/**
 * Authentication Hook - Re-export from AuthContext
 * 
 * This file re-exports from the AuthContext for backwards compatibility.
 * Use this hook in components that need auth state and methods.
 */

export {
  useAuthContext as useAuth,
  AuthProvider,
} from '@/contexts/AuthContext'

export type {
  AuthState,
} from '@/contexts/AuthContext'

// Re-export Firebase auth utilities
export {
  useLogin,
  useGoogleLogin,
  useRegister,
  useSignOut,
  getAuthErrorMessage,
  getIdToken,
  getCurrentUser,
} from '@/features/auth/hooks/useLogin'

// Re-export error handler for convenience
export { toFriendlyAuthError } from '@/features/auth/utils/authErrors'

