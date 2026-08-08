import type { LucideIcon } from 'lucide-react'
import {
  Activity,
  BookOpen,
  Calendar,
  ClipboardList,
  FileText,
  FlaskConical,
  HeartPulse,
  Layers,
  LayoutDashboard,
  LogOut,
  Settings,
  Stethoscope,
  User,
} from 'lucide-react'

export interface NavItem {
  label: string
  to?: string
  icon: LucideIcon
  badge?: number
  disabled?: boolean
  section?: string
}

// Patient navigation consumed by Sidebar (rendered by DashboardLayout, the
// sole patient chrome). Doctor/CMS navigation is defined in DoctorLayout.tsx.
// This ensures complete separation of patient and doctor portals.

export const primaryNav: NavItem[] = [
  { label: 'Dashboard', to: '/app', icon: LayoutDashboard },
  { label: 'Health Profile', to: '/profile', icon: User },
  { label: 'Questionnaires', to: '/questionnaires', icon: ClipboardList },
  { label: 'Assessments', to: '/assessments', icon: Stethoscope },
  { label: 'Health Reports', to: '/assessments', icon: FileText },
  { label: 'Medical Timeline', to: '/timeline', icon: Activity },
]

export const secondaryNav: NavItem[] = [
  { label: 'Recommendations', to: '/recommendations', icon: HeartPulse },
  { label: 'Laboratory Results', to: '/body-systems', icon: FlaskConical },
  // REMOVED: CMS link - Patients should NOT access CMS
  // { label: 'Knowledge Center', to: '/cms', icon: BookOpen },
  { label: 'Body Systems', to: '/body-systems', icon: Layers },
]

export const tertiaryNav: NavItem[] = [
  { label: 'Appointments', icon: Calendar, disabled: true },
  { label: 'Settings', to: '/settings', icon: Settings },
]

export const utilityItems: NavItem[] = [
  { label: 'Settings', to: '/settings', icon: Settings },
  { label: 'Help & Support', icon: BookOpen },
  { label: 'Logout', icon: LogOut },
]

export function defaultActiveHref(): string {
  return '/app'
}