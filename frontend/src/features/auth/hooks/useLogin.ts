/**
 * Authentication Hooks
 * 
 * Provides React Query mutations for authentication operations.
 * Uses centralized Firebase configuration from @/lib/firebase
 */

import { useMutation } from '@tanstack/react-query'
import { 
  getFirebaseAuth,
  initializeFirebase,
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword,
  GoogleAuthProvider, 
  signInWithPopup,
  signOut as firebaseSignOut,
  updateProfile,
  type User 
} from '@/lib/firebase'
import api from '@/lib/api'
import type { LoginFormValues, RegisterFormValues } from '../types/auth'
import { toFriendlyAuthError } from '../utils/authErrors'

// Re-export error handler for convenience
export function getAuthErrorMessage(error: unknown): string {
  return toFriendlyAuthError(error).message
}

// Email/Password Login
export function useLogin() {
  return useMutation({
    mutationFn: async ({ email, password }: LoginFormValues) => {
      // Ensure Firebase is initialized
      initializeFirebase()
      
      const auth = getFirebaseAuth()
      const result = await signInWithEmailAndPassword(auth, email, password)
      return result.user
    },
  })
}

// Google Sign-In
export function useGoogleLogin() {
  return useMutation({
    mutationFn: async () => {
      // Ensure Firebase is initialized
      initializeFirebase()
      
      const auth = getFirebaseAuth()
      const provider = new GoogleAuthProvider()
      
      // Add scopes if needed
      // provider.addScope('profile')
      // provider.addScope('email')
      
      const result = await signInWithPopup(auth, provider)
      return result.user
    },
  })
}

// Registration with role
export function useRegister() {
  return useMutation({
    mutationFn: async ({ email, password, displayName, role = 'patient' }: RegisterFormValues) => {
      // Ensure Firebase is initialized
      initializeFirebase()
      
      const auth = getFirebaseAuth()
      
      // Create Firebase user
      const result = await createUserWithEmailAndPassword(auth, email, password)
      
      // Update display name if provided
      if (displayName && result.user) {
        await updateProfile(result.user, { displayName })
      }
      
      // Register with backend to store role
      try {
        const token = await result.user.getIdToken()
        await api.post('/auth/register', {
          email,
          display_name: displayName,
          role, // 'patient' or 'doctor'
          firebase_uid: result.user.uid,
        }, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
      } catch (apiError) {
        // Log but don't fail - Firebase user was created successfully
        console.warn('Failed to register with backend API:', apiError)
        // Store role in localStorage as fallback
        localStorage.setItem('medicheck_role', role)
        localStorage.setItem('medicheck_account_type', role)
      }
      
      return result.user
    },
  })
}

// Sign Out
export function useSignOut() {
  return useMutation({
    mutationFn: async () => {
      const auth = getFirebaseAuth()
      await firebaseSignOut(auth)
      // Clear local role storage
      localStorage.removeItem('medicheck_role')
      localStorage.removeItem('medicheck_account_type')
    },
  })
}

// Get current user
export function getCurrentUser(): User | null {
  try {
    const auth = getFirebaseAuth()
    return auth?.currentUser ?? null
  } catch {
    return null
  }
}

// Get ID token for API calls
export async function getIdToken(forceRefresh = false): Promise<string | null> {
  try {
    const auth = getFirebaseAuth()
    const user = auth?.currentUser
    
    if (!user) {
      return null
    }
    
    return await user.getIdToken(forceRefresh)
  } catch (error) {
    console.error('Error getting ID token:', error)
    return null
  }
}