import type { LucideIcon } from 'lucide-react'
import {
  Activity,
  BarChart3,
  Beaker,
  BookOpen,
  CheckCircle2,
  Dumbbell,
  FileJson,
  FileText,
  GitBranch,
  GitMerge,
  Globe2,
  Heart,
  History,
  Layers,
  LayoutDashboard,
  Network,
  Apple,
  Pill,
  ScanLine,
  Search,
  Settings,
  Shield,
  Stethoscope,
  Users,
  Building2,
  ClipboardList,
  Scale,
  Sparkles,
} from 'lucide-react'

export interface DoctorNavItem {
  label: string
  path: string
  icon: LucideIcon
}

export interface DoctorNavGroup {
  label: string
  items: DoctorNavItem[]
}

// CMS navigation consumed by DoctorSidebar (rendered by RootLayout for
// clinical/CMS roles). Patient navigation lives in the dashboard feature's
// navConfig. This ensures complete separation of patient and doctor portals.
export const doctorNavGroups: DoctorNavGroup[] = [
  {
    label: 'Overview',
    items: [
      { label: 'Dashboard', path: '/cms/dashboard', icon: LayoutDashboard },
      { label: 'Population Analytics', path: '/cms/analytics', icon: BarChart3 },
    ],
  },
  {
    label: 'Content',
    items: [
      { label: 'Questions', path: '/cms/questions', icon: FileText },
      { label: 'Question Groups', path: '/cms/question-groups', icon: Layers },
      { label: 'Diseases', path: '/cms/diseases', icon: Activity },
      { label: 'Body Systems', path: '/cms/body-systems', icon: Stethoscope },
      { label: 'Symptoms', path: '/cms/symptoms', icon: Heart },
      { label: 'Indicators', path: '/cms/indicators', icon: Activity },
      { label: 'Lab Tests', path: '/cms/lab-tests', icon: Beaker },
      { label: 'Imaging', path: '/cms/imaging', icon: ScanLine },
      { label: 'Recommendations', path: '/cms/recommendations', icon: Heart },
      { label: 'Lifestyle Advice', path: '/cms/lifestyle', icon: Apple },
      { label: 'Exercise Programs', path: '/cms/exercise', icon: Dumbbell },
      { label: 'Nutrition Advice', path: '/cms/nutrition', icon: Apple },
      { label: 'Evidence', path: '/cms/evidence', icon: BookOpen },
      { label: 'Templates', path: '/cms/templates', icon: FileText },
      { label: 'Medications', path: '/cms/medications', icon: Pill },
      { label: 'Guidelines', path: '/cms/guidelines', icon: BookOpen },
      { label: 'Decision Rules', path: '/cms/rules', icon: GitBranch },
      { label: 'Thresholds', path: '/cms/thresholds', icon: Activity },
    ],
  },
  {
    label: 'Builders',
    items: [
      { label: 'Question Builder', path: '/cms/builder', icon: Layers },
      { label: 'Rule Builder', path: '/cms/rules-builder', icon: GitBranch },
      { label: 'Knowledge Graph', path: '/cms/graph', icon: Network },
    ],
  },
  {
    label: 'Workflow',
    items: [
      { label: 'Publishing', path: '/cms/publishing', icon: GitMerge },
      { label: 'Approvals', path: '/cms/approvals', icon: CheckCircle2 },
      { label: 'Version History', path: '/cms/history', icon: History },
    ],
  },
  {
    label: 'Operations',
    items: [
      { label: 'Audit Logs', path: '/cms/audit', icon: Shield },
      { label: 'Users & Roles', path: '/cms/users', icon: Users },
      { label: 'Search', path: '/cms/search', icon: Search },
      { label: 'Settings', path: '/cms/settings', icon: Settings },
    ],
  },
  {
    label: 'Interoperability',
    items: [
      { label: 'FHIR Export', path: '/cms/interop', icon: FileJson },
      { label: 'SDG Analytics', path: '/cms/interop/sdg', icon: Globe2 },
      { label: 'Care Continuity', path: '/cms/interop/care-continuity', icon: Network },
      { label: 'Facilities & Referrals', path: '/cms/interop/facilities', icon: Building2 },
      { label: 'CHW Queue', path: '/cms/interop/chw-queue', icon: ClipboardList },
    ],
  },
  {
    label: 'AI Governance',
    items: [
      { label: 'CHW Suggestions', path: '/cms/ai-governance/chw-suggestions', icon: Sparkles },
      { label: 'Equity Intelligence', path: '/cms/ai-governance/equity', icon: Scale },
      { label: 'SDG Narratives', path: '/cms/ai-governance/sdg-narratives', icon: Globe2 },
    ],
  },
]
