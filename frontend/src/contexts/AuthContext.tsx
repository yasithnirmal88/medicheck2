/**
 * AuthContext - Enhanced Authentication Context with Role Support
 * 
 * Provides authentication state and role information throughout the application.
 * Integrates with Firebase Auth and backend API for role management.
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { User as FirebaseUser } from 'firebase/auth'
import { getFirebaseAuth, onAuthStateChanged, signOut as firebaseSignOut } from '@/lib/firebase'
import api from '@/lib/api'
import type { UserRole, AccountType } from '@/types/role'

// Shape of the /auth/me response (subset we consume).
interface MeResponse {
  role?: string
  roles?: string[]
}

// Query key for the current-user (/auth/me) query. Shared so any consumer
// can read, invalidate, or refetch the same cached result.
export const CURRENT_USER_QUERY_KEY = ['auth', 'me'] as const

// Auth state interface
export interface AuthState {
  user: FirebaseUser | null
  role: UserRole | null
  accountType: AccountType | null
  loading: boolean
  roleLoading: boolean
  error: string | null
  isAuthenticated: boolean
  isPatient: boolean
  isDoctor: boolean
  canAccessCMS: boolean
}

// Auth context type
interface AuthContextType extends AuthState {
  setRole: (role: UserRole) => void
  refreshRole: () => Promise<void>
  clearError: () => void
  signOut: () => Promise<void>
}

// Default context value
const defaultContext: AuthContextType = {
  user: null,
  role: null,
  accountType: null,
  loading: true,
  roleLoading: true,
  error: null,
  isAuthenticated: false,
  isPatient: false,
  isDoctor: false,
  canAccessCMS: false,
  setRole: () => {},
  refreshRole: async () => {},
  clearError: () => {},
  signOut: async () => {},
}

// Create context
const AuthContext = createContext<AuthContextType>(defaultContext)

// Determine account type from role
function getAccountType(role: UserRole | null): AccountType | null {
  if (!role) return null
  return role === 'patient' ? 'patient' : 'doctor'
}

// Check if role can access CMS
function checkCanAccessCMS(role: UserRole | null): boolean {
  if (!role) return false
  const clinicalRoles: UserRole[] = [
    'doctor',
    'super_admin',
    'medical_director',
    'specialist_doctor',
    'general_physician',
    'research_reviewer',
    'content_editor',
    'read_only_reviewer',
  ]
  return clinicalRoles.includes(role)
}

// Provider component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<FirebaseUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // roleOverride is set only by setRole() (direct override for testing/admin).
  // When null, the role is derived from the /auth/me query.
  const [roleOverride, setRoleOverride] = useState<UserRole | null>(null)
  const queryClient = useQueryClient()

  // /auth/me as a TanStack query. The axios request interceptor already
  // attaches the Firebase ID token, so the fetcher needs no manual auth
  // header. enabled: !!user prevents tokenless 401s before Firebase resolves.
  // staleTime inherits the 5 min global default, so navigation between pages
  // does NOT refetch /auth/me — the cached role is shared across consumers.
  const meQuery = useQuery<MeResponse>({
    queryKey: CURRENT_USER_QUERY_KEY,
    queryFn: async () => {
      const response = await api.get<MeResponse>('/auth/me', { timeout: 5000 })
      return response.data
    },
    enabled: !!user,
  })

  // Derive role from the query (or the direct override). role is null while
  // the user is unauthenticated OR the role has not yet resolved (loading),
  // preserving the prior `role === null` semantics that guards rely on for
  // "role unknown". On resolution (success or error) it falls back to the
  // stored role or 'patient' — matching prior behavior.
  const role: UserRole | null = roleOverride ?? (() => {
    if (!user) return null
    if (meQuery.isLoading) return null
    if (meQuery.data) {
      const inferred = meQuery.data.role || meQuery.data.roles?.[0]
      if (inferred) return inferred as UserRole
    }
    // Resolved without role data (or on error): fall back.
    const stored = localStorage.getItem('medicheck_role') as UserRole | null
    return stored ?? 'patient'
  })()

  // roleLoading: true while we have a user but role resolution is in flight
  // (and no override has been set). Mirrors the prior setRoleLoading(true)
  // until the first fetch settles, then false.
  const roleLoading = !!user && roleOverride === null && meQuery.isLoading

  // Persist role to localStorage whenever it resolves (matches prior behavior).
  useEffect(() => {
    if (user && role) {
      localStorage.setItem('medicheck_role', role)
      localStorage.setItem('medicheck_account_type', getAccountType(role) || 'patient')
    }
  }, [user, role])

  // Surface non-network auth errors. Network errors / 401 are expected when
  // the backend is unreachable and should not pollute the error state.
  useEffect(() => {
    if (!meQuery.error) {
      setError(null)
      return
    }
    const axiosError = meQuery.error as { message?: string; response?: { status?: number } }
    const message = axiosError.message || 'Unknown error'
    const isNetworkError =
      message.includes('Network Error') ||
      message.includes('ERR_CONNECTION_REFUSED') ||
      message.includes('timeout') ||
      message.includes('401') ||
      axiosError.response?.status === 401
    if (!isNetworkError) {
      console.warn('Failed to fetch user role from backend:', meQuery.error)
      setError(message)
    } else {
      setError(null)
    }
  }, [meQuery.error])

  // Initialize auth and listen for Firebase state changes. On login the query
  // auto-enables (user set); on logout it auto-disables and we clear state.
  useEffect(() => {
    let unsubscribe: (() => void) | null = null

    const initAuth = () => {
      try {
        const auth = getFirebaseAuth()

        unsubscribe = onAuthStateChanged(
          auth,
          (firebaseUser) => {
            setUser(firebaseUser)
            setLoading(false)

            if (!firebaseUser) {
              setRoleOverride(null)
              localStorage.removeItem('medicheck_role')
              localStorage.removeItem('medicheck_account_type')
              // Drop any cached /auth/me so a future login refetches fresh.
              queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY })
            }
          },
          (authError) => {
            console.error('Auth state change error:', authError)
            setError('Authentication error occurred')
            setLoading(false)
          }
        )
      } catch (err) {
        console.error('Firebase auth initialization error:', err)
        setError('Failed to initialize authentication')
        setLoading(false)
      }
    }

    initAuth()

    return () => {
      if (unsubscribe) {
        unsubscribe()
      }
    }
  }, [queryClient])

  // Refresh role from backend: invalidate the cached /auth/me so TanStack
  // refetches once. Shared key means every consumer sees the new value.
  const refreshRole = useCallback(async () => {
    if (user) {
      await queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY })
    }
  }, [user, queryClient])

  // Set role directly (for testing or admin purposes). Overrides the query
  // result until the next login/logout cycle.
  const handleSetRole = useCallback((newRole: UserRole) => {
    setRoleOverride(newRole)
    localStorage.setItem('medicheck_role', newRole)
    localStorage.setItem('medicheck_account_type', getAccountType(newRole) || 'patient')
  }, [])

  // Clear error
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Sign out
  const handleSignOut = useCallback(async () => {
    try {
      const auth = getFirebaseAuth()
      await firebaseSignOut(auth)
      setRoleOverride(null)
      localStorage.removeItem('medicheck_role')
      localStorage.removeItem('medicheck_account_type')
      queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY })
    } catch (err) {
      console.error('Sign out error:', err)
      throw err
    }
  }, [queryClient])

  const accountType = getAccountType(role)
  const value: AuthContextType = {
    user,
    role,
    accountType,
    loading,
    roleLoading,
    error,
    isAuthenticated: !!user,
    isPatient: role === 'patient',
    isDoctor: role !== 'patient' && role !== null,
    canAccessCMS: checkCanAccessCMS(role),
    setRole: handleSetRole,
    refreshRole,
    clearError,
    signOut: handleSignOut,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// Hook to access auth context
export const useAuthContext = (): AuthContextType => {
  const context = useContext(AuthContext)
  
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider')
  }
  
  return context
}

// Named export for backwards compatibility
export { useAuthContext as useAuth }
