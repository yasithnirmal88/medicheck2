/**
 * Role Types for Medicheck Healthcare Platform
 * 
 * Defines user roles and their permissions for RBAC.
 * These types mirror the backend roles defined in app/core/security/rbac.py
 */

// User account types - determined at registration
export type AccountType = 'patient' | 'doctor'

// Full role enumeration (includes all healthcare roles)
export type UserRole =
  | 'patient'
  | 'doctor'
  | 'super_admin'
  | 'medical_director'
  | 'specialist_doctor'
  | 'general_physician'
  | 'research_reviewer'
  | 'content_editor'
  | 'read_only_reviewer'
  | 'community_health_worker'

// Role display names for UI
export const ROLE_DISPLAY_NAMES: Record<UserRole, string> = {
  patient: 'Patient',
  doctor: 'Doctor',
  super_admin: 'Super Admin',
  medical_director: 'Medical Director',
  specialist_doctor: 'Specialist Doctor',
  general_physician: 'General Physician',
  research_reviewer: 'Research Reviewer',
  content_editor: 'Content Editor',
  read_only_reviewer: 'Read-Only Reviewer',
  community_health_worker: 'Community Health Worker',
}

// Role hierarchy (higher number = more permissions)
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  patient: 0,
  community_health_worker: 3,
  read_only_reviewer: 5,
  content_editor: 10,
  research_reviewer: 15,
  general_physician: 20,
  doctor: 30,
  specialist_doctor: 40,
  medical_director: 50,
  super_admin: 100,
}

// Role categories for UI grouping
export type RoleCategory = 'patient' | 'clinical' | 'admin' | 'chw'

export const ROLE_CATEGORIES: Record<UserRole, RoleCategory> = {
  patient: 'patient',
  doctor: 'clinical',
  super_admin: 'admin',
  medical_director: 'admin',
  specialist_doctor: 'clinical',
  general_physician: 'clinical',
  research_reviewer: 'clinical',
  content_editor: 'clinical',
  read_only_reviewer: 'clinical',
  community_health_worker: 'chw',
}

// Check if a role is a clinical/doctor role
export function isClinicalRole(role: UserRole): boolean {
  return ROLE_CATEGORIES[role] === 'clinical'
}

// Check if a role is admin
export function isAdminRole(role: UserRole): boolean {
  return ROLE_CATEGORIES[role] === 'admin'
}

// Check if a role can access CMS
export function canAccessCMS(role: UserRole): boolean {
  return isClinicalRole(role) || isAdminRole(role)
}

// Check if a role can access patient dashboard
export function canAccessPatientApp(role: UserRole): boolean {
  return role === 'patient' || isAdminRole(role)
}

// Check if a role is a Community Health Worker (Phase 8)
export function isCHWRole(role: UserRole): boolean {
  return ROLE_CATEGORIES[role] === 'chw'
}

// Role permissions (for fine-grained access control)
export type Permission =
  | 'questionnaire:read'
  | 'questionnaire:write'
  | 'assessment:read'
  | 'assessment:write'
  | 'profile:read'
  | 'profile:write'
  | 'cms:read'
  | 'cms:write'
  | 'cms:publish'
  | 'users:read'
  | 'users:write'
  | 'audit:read'
  | 'settings:read'
  | 'settings:write'

// Default permissions per role
export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  patient: [
    'questionnaire:read',
    'questionnaire:write',
    'assessment:read',
    'profile:read',
    'profile:write',
  ],
  doctor: [
    'questionnaire:read',
    'questionnaire:write',
    'assessment:read',
    'assessment:write',
    'profile:read',
    'cms:read',
    'cms:write',
    'cms:publish',
    'audit:read',
    'settings:read',
  ],
  super_admin: [
    'questionnaire:read',
    'questionnaire:write',
    'assessment:read',
    'assessment:write',
    'profile:read',
    'profile:write',
    'cms:read',
    'cms:write',
    'cms:publish',
    'users:read',
    'users:write',
    'audit:read',
    'settings:read',
    'settings:write',
  ],
  medical_director: [
    'questionnaire:read',
    'questionnaire:write',
    'assessment:read',
    'assessment:write',
    'profile:read',
    'cms:read',
    'cms:write',
    'cms:publish',
    'users:read',
    'audit:read',
    'settings:read',
  ],
  specialist_doctor: [
    'questionnaire:read',
    'questionnaire:write',
    'assessment:read',
    'assessment:write',
    'profile:read',
    'cms:read',
    'cms:write',
    'cms:publish',
    'audit:read',
    'settings:read',
  ],
  general_physician: [
    'questionnaire:read',
    'questionnaire:write',
    'assessment:read',
    'profile:read',
    'cms:read',
    'cms:write',
    'settings:read',
  ],
  research_reviewer: [
    'questionnaire:read',
    'assessment:read',
    'profile:read',
    'cms:read',
    'audit:read',
  ],
  content_editor: [
    'questionnaire:read',
    'questionnaire:write',
    'assessment:read',
    'profile:read',
    'cms:read',
    'cms:write',
    'settings:read',
  ],
  read_only_reviewer: [
    'questionnaire:read',
    'assessment:read',
    'profile:read',
    'cms:read',
  ],
  community_health_worker: [
    'questionnaire:read',
    'questionnaire:write',
    'assessment:read',
    'assessment:write',
    'profile:read',
    'profile:write',
  ],
}

// Check if a role has a specific permission
export function hasPermission(role: UserRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false
}

// Check if role A has equal or higher permissions than role B
export function hasEqualOrHigherRole(roleA: UserRole, roleB: UserRole): boolean {
  return ROLE_HIERARCHY[roleA] >= ROLE_HIERARCHY[roleB]
}
