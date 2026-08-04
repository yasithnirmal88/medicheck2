export type LoginFormValues = {
  email: string
  password: string
}

export type RegisterFormValues = {
  email: string
  password: string
  confirmPassword?: string
  displayName?: string
  acceptTerms?: boolean
}

export type AuthErrorType = 'invalid-credentials' | 'user-not-found' | 'network' | 'too-many-attempts' | 'unknown'

export type FriendlyAuthError = {
  type: AuthErrorType
  message: string
}