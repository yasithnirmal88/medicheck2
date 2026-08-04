/**
 * Route Guards for Role-Based Access Control
 * 
 * Provides authentication and authorization guards for React Router.
 * These guards enforce RBAC at the route level, preventing unauthorized access.
 */

import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthContext } from '@/contexts/AuthContext'
import type { UserRole } from '@/types/role'
import LoadingPage from '@/shared/loading/LoadingPage'

// ============================================================================
// RequireAuth - Basic authentication check
// ============================================================================

interface RequireAuthProps {
  children: React.ReactElement
  redirectTo?: string
}

/**
 * RequireAuth - Ensures user is authenticated
 * 
 * Redirects to login if user is not authenticated.
 * Shows loading state while checking auth status.
 */
export const RequireAuth: React.FC<RequireAuthProps> = ({ 
  children, 
  redirectTo = '/login' 
}) => {
  const { user, loading, isAuthenticated } = useAuthContext()
  const location = useLocation()

  if (loading) {
    return <LoadingPage />
  }

  if (!isAuthenticated) {
    // Redirect to login, but save the location they tried to access
    return <Navigate to={redirectTo} state={{ from: location }} replace />
  }

  return children
}

// ============================================================================
// RequireRole - Role-based access control
// ============================================================================

interface RequireRoleProps {
  children: React.ReactElement
  roles: UserRole | UserRole[]
  fallbackPath?: string
  showLoading?: boolean
}

/**
 * RequireRole - Ensures user has one of the specified roles
 * 
 * Redirects to fallbackPath if user doesn't have required role.
 * Requires user to be authenticated first.
 */
export const RequireRole: React.FC<RequireRoleProps> = ({
  children,
  roles,
  fallbackPath = '/unauthorized',
  showLoading = true,
}) => {
  const { user, loading, role, isAuthenticated } = useAuthContext()
  const location = useLocation()

  // Normalize roles to array
  const allowedRoles = Array.isArray(roles) ? roles : [roles]

  if (loading && showLoading) {
    return <LoadingPage />
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Check if user has required role
  if (!role || !allowedRoles.includes(role)) {
    console.warn(
      `Access denied: User role "${role}" is not in allowed roles [${allowedRoles.join(', ')}]`
    )
    return <Navigate to={fallbackPath} replace />
  }

  return children
}

// ============================================================================
// RequirePatient - Patient-only routes
// ============================================================================

interface RequirePatientProps {
  children: React.ReactElement
  fallbackPath?: string
}

/**
 * RequirePatient - Ensures user is a patient
 * 
 * Redirects to patient dashboard or fallback if user is not a patient.
 */
export const RequirePatient: React.FC<RequirePatientProps> = ({
  children,
  fallbackPath = '/cms/dashboard',
}) => {
  const { isAuthenticated, isPatient, loading, role } = useAuthContext()
  const location = useLocation()

  if (loading) {
    return <LoadingPage />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Redirect doctors/clinicians away from patient routes
  if (!isPatient) {
    console.warn(
      `Access denied: Non-patient role "${role}" tried to access patient route`
    )
    return <Navigate to={fallbackPath} replace />
  }

  return children
}

// ============================================================================
// RequireDoctor - Doctor/Clinical routes (CMS access)
// ============================================================================

interface RequireDoctorProps {
  children: React.ReactElement
  fallbackPath?: string
}

/**
 * RequireDoctor - Ensures user is a doctor or clinical staff
 * 
 * Redirects to patient dashboard or fallback if user is a patient.
 * Required for accessing CMS features.
 */
export const RequireDoctor: React.FC<RequireDoctorProps> = ({
  children,
  fallbackPath = '/app',
}) => {
  const { isAuthenticated, isPatient, loading, role, canAccessCMS } = useAuthContext()
  const location = useLocation()

  if (loading) {
    return <LoadingPage />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Redirect patients away from doctor routes
  if (isPatient || !canAccessCMS) {
    console.warn(
      `Access denied: Patient or insufficient role "${role}" tried to access CMS`
    )
    return <Navigate to={fallbackPath} replace />
  }

  return children
}

// ============================================================================
// RequireAdmin - Admin-only routes
// ============================================================================

interface RequireAdminProps {
  children: React.ReactElement
  fallbackPath?: string
}

/**
 * RequireAdmin - Ensures user is an admin
 * 
 * Redirects to fallback if user is not an admin.
 */
export const RequireAdmin: React.FC<RequireAdminProps> = ({
  children,
  fallbackPath = '/app',
}) => {
  const { isAuthenticated, loading, role } = useAuthContext()
  const location = useLocation()

  if (loading) {
    return <LoadingPage />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  const adminRoles: UserRole[] = ['super_admin', 'medical_director']
  
  if (!role || !adminRoles.includes(role)) {
    console.warn(
      `Access denied: Non-admin role "${role}" tried to access admin route`
    )
    return <Navigate to={fallbackPath} replace />
  }

  return children
}

// ============================================================================
// RedirectBasedOnRole - Dynamic redirect based on user role
// ============================================================================

interface RedirectBasedOnRoleProps {
  children: React.ReactElement
}

/**
 * RedirectBasedOnRole - Redirects user based on their role
 * 
 * Patients go to /app
 * Doctors/Clinicians go to /cms/dashboard
 * 
 * Use this for the root route after login.
 */
export const RedirectBasedOnRole: React.FC<RedirectBasedOnRoleProps> = ({
  children,
}) => {
  const { isAuthenticated, isPatient, loading, role, roleLoading } = useAuthContext()
  const location = useLocation()

  // Wait for both auth and role to be loaded
  if (loading || roleLoading) {
    return <LoadingPage />
  }

  if (!isAuthenticated || !role) {
    // Not logged in, go to login
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Already at correct destination based on role, render children
  // This is useful for "/" route that should show role-appropriate content
  return children
}

// ============================================================================
// GuestRoute - Routes only for non-authenticated users
// ============================================================================

interface GuestRouteProps {
  children: React.ReactElement
}

/**
 * GuestRoute - Ensures user is NOT authenticated
 * 
 * Redirects to appropriate dashboard if user is already logged in.
 */
export const GuestRoute: React.FC<GuestRouteProps> = ({ children }) => {
  const { isAuthenticated, loading, role, roleLoading } = useAuthContext()
  const location = useLocation()

  // Check where user came from
  const from = (location.state as { from?: Location })?.from?.pathname || '/'

  if (loading || roleLoading) {
    return <LoadingPage />
  }

  if (isAuthenticated && role) {
    // User is already logged in, redirect based on role
    const redirectPath = role === 'patient' ? '/app' : '/cms/dashboard'
    return <Navigate to={redirectPath} replace />
  }

  return children
}
