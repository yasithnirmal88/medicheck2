import React from 'react'
import { useAuth } from '../../../hooks/useAuth'
import LoadingPage from '../../../shared/loading/LoadingPage'
import { Navigate } from 'react-router-dom'

const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth()
  if (loading) return <LoadingPage />
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default AuthGuard
