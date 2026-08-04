import React, { createContext, useContext, useEffect, useState } from 'react'
import { initializeApp } from 'firebase/app'
import { getAuth, onAuthStateChanged, User } from 'firebase/auth'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyAUjtplfYBgFUOo6C5Q5R0NmXzVPIiH9TQ",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "medicheck-19865.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "medicheck-19865",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "medicheck-19865.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "873643749135",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:873643749135:web:763c4346a3aa00964f987a",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-RXCH3ECT4X"
}

const app = initializeApp(firebaseConfig)
const auth = getAuth(app)

type AuthContextType = {
  user: User | null
  loading: boolean
}

const AuthContext = createContext<AuthContextType>({ user: null, loading: true })

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u)
      setLoading(false)
    })
    return () => unsub()
  }, [])

  return <AuthContext.Provider value={{ user, loading }}>{children}</AuthContext.Provider>
}

export const useAuthContext = () => useContext(AuthContext)
