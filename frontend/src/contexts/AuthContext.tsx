/**
 * AuthContext - Enhanced Authentication Context with Role Support
 * 
 * Provides authentication state and role information throughout the application.
 * Integrates with Firebase Auth and backend API for role management.
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { User as FirebaseUser } from 'firebase/auth'
import { getFirebaseAuth, onAuthStateChanged, signOut as firebaseSignOut } from '@/lib/firebase'
import api from '@/lib/api'
import type { UserRole, AccountType } from '@/types/role'

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
  const [role, setRole] = useState<UserRole | null>(null)
  const [loading, setLoading] = useState(true)
  const [roleLoading, setRoleLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch user role from backend
  const fetchUserRole = useCallback(async (firebaseUser: FirebaseUser) => {
    setRoleLoading(true)
    try {
      const token = await firebaseUser.getIdToken()
      const response = await api.get('/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      
      // Backend returns role in the response
      const userData = response.data
      const userRole: UserRole = userData.role || userData.roles?.[0] || 'patient'
      setRole(userRole)
      
      // Store role in localStorage for persistence
      localStorage.setItem('medicheck_role', userRole)
      localStorage.setItem('medicheck_account_type', getAccountType(userRole) || 'patient')
      
      setError(null)
    } catch (err: unknown) {
      console.error('Failed to fetch user role:', err)
      // Fall back to stored role or default
      const storedRole = localStorage.getItem('medicheck_role') as UserRole | null
      if (storedRole) {
        setRole(storedRole)
      } else {
        // Default to patient if no role found
        setRole('patient')
      }
    } finally {
      setRoleLoading(false)
    }
  }, [])

  // Initialize auth and listen for changes
  useEffect(() => {
    let unsubscribe: (() => void) | null = null

    const initAuth = () => {
      try {
        const auth = getFirebaseAuth()
        
        unsubscribe = onAuthStateChanged(
          auth,
          async (firebaseUser) => {
            setUser(firebaseUser)
            setLoading(false)
            
            if (firebaseUser) {
              await fetchUserRole(firebaseUser)
            } else {
              setRole(null)
              setRoleLoading(false)
              // Clear stored role on logout
              localStorage.removeItem('medicheck_role')
              localStorage.removeItem('medicheck_account_type')
            }
          },
          (authError) => {
            console.error('Auth state change error:', authError)
            setError('Authentication error occurred')
            setLoading(false)
            setRoleLoading(false)
          }
        )
      } catch (err) {
        console.error('Firebase auth initialization error:', err)
        setError('Failed to initialize authentication')
        setLoading(false)
        setRoleLoading(false)
      }
    }

    initAuth()

    return () => {
      if (unsubscribe) {
        unsubscribe()
      }
    }
  }, [fetchUserRole])

  // Refresh role from backend
  const refreshRole = useCallback(async () => {
    if (user) {
      await fetchUserRole(user)
    }
  }, [user, fetchUserRole])

  // Set role directly (for testing or admin purposes)
  const handleSetRole = useCallback((newRole: UserRole) => {
    setRole(newRole)
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
      // Clear stored role on logout
      localStorage.removeItem('medicheck_role')
      localStorage.removeItem('medicheck_account_type')
    } catch (err) {
      console.error('Sign out error:', err)
      throw err
    }
  }, [])

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
