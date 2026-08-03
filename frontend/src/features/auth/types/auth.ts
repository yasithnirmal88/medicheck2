export type LoginFormValues = {
  email: string
  password: string
}

export type AuthErrorType = 'invalid-credentials' | 'user-not-found' | 'network' | 'too-many-attempts' | 'unknown'

export type FriendlyAuthError = {
  type: AuthErrorType
  message: string
}