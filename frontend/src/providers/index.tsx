import React, { useMemo } from 'react'
import { AuthProvider } from '../contexts/AuthContext'
import ThemeProvider from './ThemeProvider'

const Providers: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const content = useMemo(() => <ThemeProvider>{children}</ThemeProvider>, [children])
  return <AuthProvider>{content}</AuthProvider>
}

export default Providers
