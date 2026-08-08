/**
 * Firebase Configuration and Initialization
 * 
 * This module provides centralized Firebase initialization and authentication services.
 * All Firebase-related functionality should be imported from this module.
 * 
 * Environment Variables (prefix with VITE_ for Vite):
 * - VITE_FIREBASE_API_KEY
 * - VITE_FIREBASE_AUTH_DOMAIN
 * - VITE_FIREBASE_PROJECT_ID
 * - VITE_FIREBASE_STORAGE_BUCKET
 * - VITE_FIREBASE_MESSAGING_SENDER_ID
 * - VITE_FIREBASE_APP_ID
 * - VITE_FIREBASE_MEASUREMENT_ID (optional)
 */

import { initializeApp, getApps, FirebaseApp } from 'firebase/app'
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User,
  GoogleAuthProvider,
  signInWithPopup,
  sendPasswordResetEmail,
  updateProfile,
  Auth,
} from 'firebase/auth'

// Firebase configuration interface
interface FirebaseConfig {
  apiKey: string
  authDomain: string
  projectId: string
  storageBucket: string
  messagingSenderId: string
  appId: string
  measurementId?: string
}

// Get Firebase configuration from environment variables
const getFirebaseConfig = (): FirebaseConfig => {
  const config: FirebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY || '',
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || '',
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '',
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
    appId: import.meta.env.VITE_FIREBASE_APP_ID || '',
  }

  // Add measurementId if available (optional)
  const measurementId = import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
  if (measurementId) {
    config.measurementId = measurementId
  }

  return config
}

// Initialize Firebase App (singleton pattern)
let app: FirebaseApp | null = null
let auth: Auth | null = null

export const initializeFirebase = (): { app: FirebaseApp; auth: Auth } => {
  // Return existing instance if already initialized
  if (app && auth) {
    return { app, auth }
  }

  const config = getFirebaseConfig()

  // Validate configuration
  if (!config.apiKey) {
    console.warn(
      'Firebase: No API key found. Authentication will be disabled.\n' +
        'Set VITE_FIREBASE_API_KEY in your .env file.'
    )
  }

  // Initialize Firebase app (avoid re-initialization)
  if (getApps().length === 0) {
    app = initializeApp(config)
  } else {
    app = getApps()[0]
  }

  // Initialize Auth
  auth = getAuth(app)

  return { app: app!, auth: auth! }
}

// Export initialized instances
export const getFirebaseApp = (): FirebaseApp => {
  if (!app) {
    const { app: firebaseApp } = initializeFirebase()
    return firebaseApp
  }
  return app
}

export const getFirebaseAuth = (): Auth => {
  if (!auth) {
    const { auth: firebaseAuth } = initializeFirebase()
    return firebaseAuth
  }
  return auth
}

// Export Firebase services for convenience
export { auth as firebaseAuth }

// Re-export Firebase types and functions
export {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  firebaseSignOut as signOut,
  onAuthStateChanged,
  updateProfile,
  GoogleAuthProvider,
  signInWithPopup,
  sendPasswordResetEmail,
  type User,
}

// Type for auth state callback
export type AuthStateCallback = (user: User | null) => void

// Initialize on module load (for early auth detection)
if (typeof window !== 'undefined') {
  initializeFirebase()
}
