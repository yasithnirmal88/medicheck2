import {
  Activity,
  Brain,
  Droplet,
  Footprints,
  Heart,
  Scale,
  ShieldCheck,
  Stethoscope,
  Syringe,
} from 'lucide-react'
import type { ComponentType } from 'react'

type ImageIcon = ComponentType<{ className?: string }>

const bodySystemIcons: Record<string, ImageIcon> = {
  Cardiovascular: Heart,
  Neurological: Brain,
  Respiratory: Stethoscope,
  Endocrine: Droplet,
  Renal: Syringe,
  General: Activity,
  Musculoskeletal: Footprints,
  Preventive: ShieldCheck,
  Lifestyle: Scale,
  Metabolic: Activity,
  Immune: ShieldCheck,
  Digestive: Activity,
}

export type AssessmentCatalogEntry = {
  code: string
  title: string
  description: string
  estimatedTime: number
  questions: number
  difficulty: 'Easy' | 'Medium' | 'Hard'
  aiScore: number
  bodySystems: { name: string; icon: ImageIcon }[]
  color: 'indigo' | 'blue' | 'rose' | 'amber' | 'emerald' | 'violet' | 'teal' | 'cyan' | 'fuchsia'
}

export const assessments: AssessmentCatalogEntry[] = [
  {
    code: 'quick-health-check',
    title: 'Quick Health Check',
    description: 'A 5-minute snapshot of your overall well-being across key health indicators.',
    estimatedTime: 5,
    questions: 12,
    difficulty: 'Easy',
    aiScore: 96,
    bodySystems: [{ name: 'General', icon: bodySystemIcons.General }],
    color: 'indigo',
  },
  {
    code: 'standard-assessment',
    title: 'Standard Assessment',
    description: 'A comprehensive general health questionnaire covering the most common risk factors.',
    estimatedTime: 12,
    questions: 36,
    difficulty: 'Medium',
    aiScore: 89,
    bodySystems: [
      { name: 'General', icon: bodySystemIcons.General },
      { name: 'Cardiovascular', icon: bodySystemIcons.Cardiovascular },
      { name: 'Endocrine', icon: bodySystemIcons.Endocrine },
    ],
    color: 'blue',
  },
  {
    code: 'comprehensive-assessment',
    title: 'Comprehensive Assessment',
    description: 'Deep, multi-system evaluation for a detailed long-term health risk profile.',
    estimatedTime: 25,
    questions: 84,
    difficulty: 'Hard',
    aiScore: 92,
    bodySystems: [
      { name: 'General', icon: bodySystemIcons.General },
      { name: 'Cardiovascular', icon: bodySystemIcons.Cardiovascular },
      { name: 'Respiratory', icon: bodySystemIcons.Respiratory },
      { name: 'Endocrine', icon: bodySystemIcons.Endocrine },
      { name: 'Renal', icon: bodySystemIcons.Renal },
      { name: 'Neurological', icon: bodySystemIcons.Neurological },
    ],
    color: 'violet',
  },
  {
    code: 'heart-health',
    title: 'Heart Health',
    description: 'Focused cardiovascular risk assessment and lifestyle recommendations.',
    estimatedTime: 8,
    questions: 22,
    difficulty: 'Medium',
    aiScore: 88,
    bodySystems: [{ name: 'Cardiovascular', icon: bodySystemIcons.Cardiovascular }],
    color: 'rose',
  },
  {
    code: 'diabetes-risk',
    title: 'Diabetes Risk',
    description: 'Evaluate your risk factors for Type 2 diabetes and track metabolic health.',
    estimatedTime: 7,
    questions: 18,
    difficulty: 'Medium',
    aiScore: 84,
    bodySystems: [
      { name: 'Endocrine', icon: bodySystemIcons.Endocrine },
      { name: 'Metabolic', icon: bodySystemIcons.Metabolic },
    ],
    color: 'amber',
  },
  {
    code: 'kidney-health',
    title: 'Kidney Health',
    description: 'Screen for chronic kidney disease risk factors and early indicators.',
    estimatedTime: 9,
    questions: 20,
    difficulty: 'Medium',
    aiScore: 80,
    bodySystems: [{ name: 'Renal', icon: bodySystemIcons.Renal }],
    color: 'cyan',
  },
  {
    code: 'mental-health',
    title: 'Mental Health',
    description: 'A sensitive screening tool for stress, anxiety, and general wellbeing.',
    estimatedTime: 10,
    questions: 24,
    difficulty: 'Medium',
    aiScore: 91,
    bodySystems: [{ name: 'Neurological', icon: bodySystemIcons.Neurological }],
    color: 'fuchsia',
  },
  {
    code: 'respiratory-health',
    title: 'Respiratory Health',
    description: 'Assess asthma, COPD, and other respiratory risk and triggers.',
    estimatedTime: 6,
    questions: 16,
    difficulty: 'Easy',
    aiScore: 85,
    bodySystems: [{ name: 'Respiratory', icon: bodySystemIcons.Respiratory }],
    color: 'teal',
  },
  {
    code: 'lifestyle-assessment',
    title: 'Lifestyle Assessment',
    description: 'Evaluate nutrition, activity, sleep, and habits that shape long-term health.',
    estimatedTime: 11,
    questions: 30,
    difficulty: 'Medium',
    aiScore: 87,
    bodySystems: [
      { name: 'Lifestyle', icon: bodySystemIcons.Lifestyle },
      { name: 'Musculoskeletal', icon: bodySystemIcons.Musculoskeletal },
    ],
    color: 'emerald',
  },
]

export const difficultyVariant = {
  Easy: { label: 'Easy', color: 'text-emerald-600', bg: 'bg-emerald-100 dark:bg-emerald-900/30' },
  Medium: { label: 'Medium', color: 'text-amber-600', bg: 'bg-amber-100 dark:bg-amber-900/30' },
  Hard: { label: 'Hard', color: 'text-rose-600', bg: 'bg-rose-100 dark:bg-rose-900/30' },
} as const

export const colorTheme: Record<AssessmentCatalogEntry['color'], string> = {
  indigo: 'indigo',
  blue: 'blue',
  rose: 'rose',
  amber: 'amber',
  emerald: 'emerald',
  violet: 'violet',
  teal: 'teal',
  cyan: 'cyan',
  fuchsia: 'fuchsia',
}
