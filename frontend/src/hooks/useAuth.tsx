/**
 * Authentication Hook
 * 
 * Provides authentication state and methods using Firebase Auth.
 * Use this hook instead of directly importing Firebase auth.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  GoogleAuthProvider,
  signInWithPopup,
  updateProfile,
  updateEmail,
  updatePassword,
  sendPasswordResetEmail,
  reauthenticateWithCredential,
  EmailAuthProvider,
  AuthError,
} from 'firebase/auth'
import {
  getFirebaseAuth,
  initializeFirebase,
} from '@/lib/firebase'

// Auth state interface
export interface AuthState {
  user: User | null
  loading: boolean
  error: string | null
  isAuthenticated: boolean
}

// Sign in credentials
export interface SignInCredentials {
  email: string
  password: string
}

// Sign up credentials
export interface SignUpCredentials {
  email: string
  password: string
  displayName?: string
}

/**
 * Main authentication hook
 * 
 * Provides:
 * - user: Current authenticated user (null if not authenticated)
 * - loading: Loading state while checking auth status
 * - error: Error message if last operation failed
 * - isAuthenticated: Boolean indicating auth status
 * 
 * Methods:
 * - signIn: Sign in with email and password
 * - signUp: Create new account
 * - signInWithGoogle: Sign in with Google
 * - signOut: Sign out current user
 * - resetPassword: Send password reset email
 * - updateUserProfile: Update user display name
 * - getIdToken: Get Firebase ID token for API calls
 */
export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Initialize auth and listen for changes
  useEffect(() => {
    let unsubscribe: (() => void) | null = null

    const initAuth = () => {
      try {
        const auth = getFirebaseAuth()
        
        unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
          setUser(firebaseUser)
          setLoading(false)
        }, (authError) => {
          console.error('Auth state error:', authError)
          setError('Authentication error occurred')
          setLoading(false)
        })
      } catch (err) {
        console.error('Firebase auth initialization error:', err)
        // Try to initialize and retry
        try {
          initializeFirebase()
          const auth = getFirebaseAuth()
          unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
            setUser(firebaseUser)
            setLoading(false)
          })
        } catch (retryErr) {
          console.error('Retry failed:', retryErr)
          setError('Failed to initialize authentication')
          setLoading(false)
        }
      }
    }

    initAuth()

    return () => {
      if (unsubscribe) {
        unsubscribe()
      }
    }
  }, [])

  // Clear error when user performs new action
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Sign in with email and password
  const signIn = useCallback(async ({ email, password }: SignInCredentials): Promise<User | null> => {
    setLoading(true)
    setError(null)

    try {
      const auth = getFirebaseAuth()
      const result = await signInWithEmailAndPassword(auth, email, password)
      setUser(result.user)
      setLoading(false)
      return result.user
    } catch (err) {
      const errorMessage = getAuthErrorMessage(err as AuthError)
      setError(errorMessage)
      setLoading(false)
      throw new Error(errorMessage)
    }
  }, [])

  // Sign up with email and password
  const signUp = useCallback(async ({ email, password, displayName }: SignUpCredentials): Promise<User | null> => {
    setLoading(true)
    setError(null)

    try {
      const auth = getFirebaseAuth()
      const result = await createUserWithEmailAndPassword(auth, email, password)
      
      // Update display name if provided
      if (displayName && result.user) {
        await updateProfile(result.user, { displayName })
        // Refresh user object
        setUser({ ...result.user, displayName } as User)
      }
      
      setLoading(false)
      return result.user
    } catch (err) {
      const errorMessage = getAuthErrorMessage(err as AuthError)
      setError(errorMessage)
      setLoading(false)
      throw new Error(errorMessage)
    }
  }, [])

  // Sign in with Google
  const signInWithGoogle = useCallback(async (): Promise<User | null> => {
    setLoading(true)
    setError(null)

    try {
      const auth = getFirebaseAuth()
      const provider = new GoogleAuthProvider()
      
      // Add custom claims or scopes if needed
      // provider.addScope('profile')
      // provider.addScope('email')
      
      const result = await signInWithPopup(auth, provider)
      setUser(result.user)
      setLoading(false)
      return result.user
    } catch (err) {
      const errorMessage = getAuthErrorMessage(err as AuthError)
      setError(errorMessage)
      setLoading(false)
      throw new Error(errorMessage)
    }
  }, [])

  // Sign out
  const signOut = useCallback(async (): Promise<void> => {
    setLoading(true)
    setError(null)

    try {
      const auth = getFirebaseAuth()
      await firebaseSignOut(auth)
      setUser(null)
      setLoading(false)
    } catch (err) {
      const errorMessage = getAuthErrorMessage(err as AuthError)
      setError(errorMessage)
      setLoading(false)
      throw new Error(errorMessage)
    }
  }, [])

  // Reset password
  const resetPassword = useCallback(async (email: string): Promise<void> => {
    setLoading(true)
    setError(null)

    try {
      const auth = getFirebaseAuth()
      await sendPasswordResetEmail(auth, email)
      setLoading(false)
    } catch (err) {
      const errorMessage = getAuthErrorMessage(err as AuthError)
      setError(errorMessage)
      setLoading(false)
      throw new Error(errorMessage)
    }
  }, [])

  // Update user profile
  const updateUserProfile = useCallback(async (displayName: string): Promise<void> => {
    if (!user) {
      throw new Error('No user logged in')
    }

    setLoading(true)
    setError(null)

    try {
      const auth = getFirebaseAuth()
      await updateProfile(auth.currentUser!, { displayName })
      
      // Refresh user state
      setUser({ ...user, displayName } as User)
      setLoading(false)
    } catch (err) {
      const errorMessage = getAuthErrorMessage(err as AuthError)
      setError(errorMessage)
      setLoading(false)
      throw new Error(errorMessage)
    }
  }, [user])

  // Update user email
  const updateUserEmail = useCallback(async (email: string): Promise<void> => {
    if (!user) {
      throw new Error('No user logged in')
    }

    setLoading(true)
    setError(null)

    try {
      const auth = getFirebaseAuth()
      await updateEmail(auth.currentUser!, email)
      setUser({ ...user, email } as User)
      setLoading(false)
    } catch (err) {
      const errorMessage = getAuthErrorMessage(err as AuthError)
      setError(errorMessage)
      setLoading(false)
      throw new Error(errorMessage)
    }
  }, [user])

  // Update user password
  const updateUserPassword = useCallback(async (newPassword: string): Promise<void> => {
    if (!user) {
      throw new Error('No user logged in')
    }

    setLoading(true)
    setError(null)

    try {
      const auth = getFirebaseAuth()
      await updatePassword(auth.currentUser!, newPassword)
      setLoading(false)
    } catch (err) {
      const errorMessage = getAuthErrorMessage(err as AuthError)
      setError(errorMessage)
      setLoading(false)
      throw new Error(errorMessage)
    }
  }, [user])

  // Re-authenticate user (needed for sensitive operations)
  const reauthenticate = useCallback(async (password: string): Promise<void> => {
    if (!user?.email) {
      throw new Error('No user logged in')
    }

    setLoading(true)
    setError(null)

    try {
      const auth = getFirebaseAuth()
      const credential = EmailAuthProvider.credential(user.email, password)
      await reauthenticateWithCredential(auth.currentUser!, credential)
      setLoading(false)
    } catch (err) {
      const errorMessage = getAuthErrorMessage(err as AuthError)
      setError(errorMessage)
      setLoading(false)
      throw new Error(errorMessage)
    }
  }, [user])

  // Get Firebase ID token
  const getIdToken = useCallback(async (forceRefresh = false): Promise<string | null> => {
    if (!user) {
      return null
    }

    try {
      return await user.getIdToken(forceRefresh)
    } catch (err) {
      console.error('Error getting ID token:', err)
      return null
    }
  }, [user])

  // Get current user
  const getCurrentUser = useCallback((): User | null => {
    return user
  }, [user])

  return {
    // State
    user,
    loading,
    error,
    isAuthenticated: !!user,

    // Auth methods
    signIn,
    signUp,
    signInWithGoogle,
    signOut,
    resetPassword,
    updateUserProfile,
    updateUserEmail,
    updateUserPassword,
    reauthenticate,
    getIdToken,
    getCurrentUser,
    clearError,
  }
}

// Convert Firebase auth error codes to user-friendly messages
export const getAuthErrorMessage = (error: AuthError): string => {
  switch (error.code) {
    case 'auth/email-already-in-use':
      return 'This email address is already registered. Please sign in or use a different email.'
    case 'auth/invalid-email':
      return 'The email address is not valid. Please check and try again.'
    case 'auth/operation-not-allowed':
      return 'This sign-in method is not enabled. Please contact support.'
    case 'auth/weak-password':
      return 'The password is too weak. Please use at least 6 characters.'
    case 'auth/user-disabled':
      return 'This account has been disabled. Please contact support.'
    case 'auth/user-not-found':
    case 'auth/wrong-password':
    case 'auth/invalid-credential':
      return 'Invalid email or password. Please try again.'
    case 'auth/too-many-requests':
      return 'Too many failed attempts. Please try again later or reset your password.'
    case 'auth/network-request-failed':
      return 'Network error. Please check your internet connection.'
    case 'auth/popup-closed-by-user':
      return 'Sign-in was cancelled. Please try again.'
    case 'auth/cancelled-popup-request':
      return 'Only one sign-in popup is allowed at a time.'
    case 'auth/requires-recent-login':
      return 'Please sign in again to complete this action.'
    case 'auth/invalid-verification-code':
      return 'The verification code is invalid.'
    case 'auth/invalid-verification-id':
      return 'The verification ID is invalid.'
    case 'auth/credential-already-in-use':
      return 'This credential is already associated with another account.'
    case 'auth/invalid-api-key':
      return 'Firebase configuration error. Please refresh the page.'
    case 'auth/app-deleted':
      return 'Firebase app has been deleted.'
    case 'auth/app-not-authorized':
      return 'App is not authorized to use Firebase Authentication.'
    case 'auth/argument-error':
      return 'Invalid arguments provided.'
    case 'auth/invalid-phone-number':
      return 'The phone number is not valid.'
    case 'auth/missing-phone-number':
      return 'Please provide a phone number.'
    default:
      console.error('Unhandled auth error:', error.code, error.message)
      return 'An unexpected error occurred. Please try again.'
  }
}

// Export type for use in components
export type UseAuthReturn = ReturnType<typeof useAuth>
