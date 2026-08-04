/**
 * AuthProvider - React Context for Firebase Authentication
 * 
 * Wraps the app and provides authentication state to all components.
 * Uses the centralized Firebase configuration from @/lib/firebase
 */

import React, { createContext, useContext, useEffect, useState } from 'react'
import { User } from 'firebase/auth'
import { getFirebaseAuth, onAuthStateChanged } from '@/lib/firebase'

// Auth context type
type AuthContextType = {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
}

// Default context value
const defaultContext: AuthContextType = {
  user: null,
  loading: true,
  isAuthenticated: false,
}

// Create context
const AuthContext = createContext<AuthContextType>(defaultContext)

// Provider component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let unsubscribe: (() => void) | null = null

    try {
      const auth = getFirebaseAuth()
      
      unsubscribe = onAuthStateChanged(
        auth,
        (firebaseUser) => {
          setUser(firebaseUser)
          setLoading(false)
        },
        (error) => {
          console.error('Auth state change error:', error)
          setLoading(false)
        }
      )
    } catch (error) {
      console.error('Firebase auth initialization error:', error)
      setLoading(false)
    }

    return () => {
      if (unsubscribe) {
        unsubscribe()
      }
    }
  }, [])

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
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
