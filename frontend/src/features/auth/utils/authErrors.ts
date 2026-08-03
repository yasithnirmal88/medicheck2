import type { FriendlyAuthError } from '../types/auth'

const MESSAGES: Record<FriendlyAuthError['type'], string> = {
  'invalid-credentials':
    'The email or password you entered is incorrect. Please try again.',
  'user-not-found': 'No account was found for this email. Please check and try again.',
  network: 'Network error. Please check your connection and try again.',
  'too-many-attempts': 'Too many sign-in attempts. Please wait a moment and try again.',
  unknown: 'Something went wrong while signing you in. Please try again.',
}

const FIREBASE_CODE_MAP: Record<string, FriendlyAuthError['type']> = {
  'auth/wrong-password': 'invalid-credentials',
  'auth/invalid-credential': 'invalid-credentials',
  'auth/invalid-login-credentials': 'invalid-credentials',
  'auth/invalid-email': 'invalid-credentials',
  'auth/user-not-found': 'user-not-found',
  'auth/too-many-requests': 'too-many-attempts',
  'auth/network-request-failed': 'network',
  'auth/internal-error': 'network',
  'auth/invalid-api-key': 'network',
  'auth/invalid-app-credential': 'network',
}

function getCode(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'code' in error) {
    return String((error as { code?: string }).code ?? '')
  }
  return ''
}

function getMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return String((error as { message?: string }).message ?? '')
  }
  return ''
}

export function toFriendlyAuthError(error: unknown): FriendlyAuthError {
  const code = getCode(error)
  const message = getMessage(error)

  let type: FriendlyAuthError['type'] = FIREBASE_CODE_MAP[code]

  if (!type) {
    type =
      code.startsWith('auth/network-') ||
      /network|fetch failed|timeout|could not|offline|unreachable/i.test(message)
        ? 'network'
        : 'unknown'
  }

  return { type, message: MESSAGES[type] }
}