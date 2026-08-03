import { useMutation } from '@tanstack/react-query'
import { getAuth, signInWithEmailAndPassword, GoogleAuthProvider, signInWithPopup } from 'firebase/auth'
import type { LoginFormValues } from '../types/auth'
import { toFriendlyAuthError } from '../utils/authErrors'

export function getAuthErrorMessage(error: unknown): string {
  return toFriendlyAuthError(error).message
}

export function useLogin() {
  return useMutation({
    mutationFn: async ({ email, password }: LoginFormValues) => {
      const auth = getAuth()
      await signInWithEmailAndPassword(auth, email, password)
      return auth.currentUser
    },
  })
}

export function useGoogleLogin() {
  return useMutation({
    mutationFn: async () => {
      const auth = getAuth()
      const provider = new GoogleAuthProvider()
      const result = await signInWithPopup(auth, provider)
      return result.user
    },
  })
}