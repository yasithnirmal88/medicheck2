import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronDown,
  ChevronUp,
  Edit3,
  CheckCircle,
  AlertTriangle,
  Info,
  User,
  Activity,
  Heart,
  Apple,
  Dumbbell,
  Moon,
  Brain,
  AlertCircle,
  Scissors,
  Users,
  Pill,
  Shield,
  Syringe,
  Venus,
  Mars,
  AlertTriangle as RiskIcon,
  Globe,
  Briefcase,
  Plane,
  Phone,
  CheckCircle as SubmitIcon,
  Loader,
} from 'lucide-react'
import type { WizardState, SectionKey } from '@/features/profile/types/wizard'
import { fieldSpecs } from '@/features/profile/wizard/fieldSpecs'
import { Switch } from './Switch'
import { cn } from '@/lib/utils'

const STEP_LABELS: { key: SectionKey; label: string; icon: React.ReactNode }[] = [
  { key: 'personal', label: 'Personal', icon: <User className="h-4 w-4" /> },
  { key: 'body', label: 'Body', icon: <Activity className="h-4 w-4" /> },
  { key: 'lifestyle', label: 'Lifestyle', icon: <Heart className="h-4 w-4" /> },
  { key: 'nutrition', label: 'Nutrition', icon: <Apple className="h-4 w-4" /> },
  { key: 'physical_activity', label: 'Activity', icon: <Dumbbell className="h-4 w-4" /> },
  { key: 'sleep', label: 'Sleep', icon: <Moon className="h-4 w-4" /> },
  { key: 'mental_health', label: 'Mental', icon: <Brain className="h-4 w-4" /> },
  { key: 'conditions', label: 'Conditions', icon: <AlertCircle className="h-4 w-4" /> },
  { key: 'surgeries', label: 'Surgeries', icon: <Scissors className="h-4 w-4" /> },
  { key: 'family_history', label: 'Family', icon: <Users className="h-4 w-4" /> },
  { key: 'medications', label: 'Meds', icon: <Pill className="h-4 w-4" /> },
  { key: 'allergies', label: 'Allergies', icon: <Shield className="h-4 w-4" /> },
  { key: 'vaccinations', label: 'Vaccines', icon: <Syringe className="h-4 w-4" /> },
  { key: 'women_health', label: "Women's", icon: <Venus className="h-4 w-4" /> },
  { key: 'men_health', label: "Men's", icon: <Mars className="h-4 w-4" /> },
  { key: 'lifestyle_risks', label: 'Risks', icon: <RiskIcon className="h-4 w-4" /> },
  { key: 'environment', label: 'Environment', icon: <Globe className="h-4 w-4" /> },
  { key: 'occupation', label: 'Work', icon: <Briefcase className="h-4 w-4" /> },
  { key: 'travel', label: 'Travel', icon: <Plane className="h-4 w-4" /> },
  { key: 'emergency', label: 'Emergency', icon: <Phone className="h-4 w-4" /> },
]

function getSectionCompletion(key: SectionKey, state: WizardState): { filled: number; total: number; missing: string[] } {
  const specs = fieldSpecs[key]
  if (specs.length === 0) return { filled: 0, total: 0, missing: [] }
  const value = state[key]
  if (Array.isArray(value)) {
    const count = value.length
    return count > 0 ? { filled: count, total: count, missing: [] } : { filled: 0, total: 0, missing: [] }
  }
  const record = (value as unknown as Record<string, unknown>) ?? {}
  let filled = 0
  let total = 0
  const missing: string[] = []
  for (const spec of specs) {
    if (spec.kind === 'checkbox') {
      total++
      if (record[spec.name]) filled++
      continue
    }
    if (spec.optional) continue
    total++
    const val = record[spec.name]
    const hasValue = val !== undefined && val !== null && val !== '' && (typeof val !== 'string' || (val as string).trim() !== '') && !(Array.isArray(val) && (val as unknown[]).length === 0)
    if (hasValue) {
      filled++
    } else {
      missing.push(spec.label)
    }
  }
  return { filled, total, missing }
}

interface ReviewSubmitPageProps {
  state: WizardState
  setSection: (key: SectionKey, value: unknown) => void
  onSubmit: () => void
}

export function ReviewSubmitPage({ state, setSection, onSubmit }: ReviewSubmitPageProps) {
  const [expandedSections, setExpandedSections] = useState<Set<SectionKey>>(new Set(STEP_LABELS.map((s) => s.key)))
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    setSubmitting(true)
    await new Promise((resolve) => setTimeout(resolve, 1500))
    setSubmitting(false)
    setSubmitted(true)
    onSubmit()
  }

  const toggleSection = (key: SectionKey) => {
    setExpandedSections((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  if (submitted) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, type: 'spring', bounce: 0.4 }}
        className="flex flex-col items-center justify-center py-12 text-center"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', bounce: 0.5 }}
          className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400"
        >
          <SubmitIcon className="h-12 w-12" />
        </motion.div>
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-2 text-2xl font-bold text-slate-800 dark:text-slate-100"
        >
          Profile Submitted!
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-sm text-slate-500 dark:text-slate-400"
        >
          Your health profile has been submitted successfully. We&apos;ll review your data and provide personalized insights.
        </motion.p>
      </motion.div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="mb-4 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-2">
          <Info className="h-4 w-4 text-blue-500" />
          Review Your Profile
        </h3>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Click Edit on any section to make changes. Sections with missing required fields are highlighted.
        </p>
      </div>

      <AnimatePresence>
        {STEP_LABELS.map((step) => {
          const { filled, total, missing } = getSectionCompletion(step.key, state)
          const isExpanded = expandedSections.has(step.key)
          const completionPct = total > 0 ? Math.round((filled / total) * 100) : 0
          const hasMissing = missing.length > 0
          const isComplete = total > 0 && missing.length === 0

          return (
            <motion.div
              key={step.key}
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800"
            >
              <button
                type="button"
                onClick={() => toggleSection(step.key)}
                className="flex w-full items-center justify-between px-4 py-3 text-left"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                    {step.icon}
                  </span>
                  <div>
                    <span className="text-sm font-medium text-slate-800 dark:text-slate-100">{step.label}</span>
                    <div className="mt-0.5 flex items-center gap-2">
                      {total > 0 && (
                        <div className="flex h-1.5 w-20 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                          <div
                            className={cn(
                              'h-full rounded-full transition-all duration-300',
                              completionPct === 100 ? 'bg-emerald-500' : completionPct >= 50 ? 'bg-amber-400' : 'bg-red-400',
                            )}
                            style={{ width: `${completionPct}%` }}
                          />
                        </div>
                      )}
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {total > 0 ? `${filled}/${total}` : '—'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isComplete ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
                      <CheckCircle className="h-3 w-3" /> Complete
                    </span>
                  ) : total > 0 ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
                      <AlertTriangle className="h-3 w-3" /> Incomplete
                    </span>
                  ) : null}
                  {isExpanded ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
                </div>
              </button>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="border-t border-slate-200 px-4 py-3 dark:border-slate-700">
                      {hasMissing && (
                        <div className="mb-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-800/50 dark:bg-amber-900/20 dark:text-amber-200">
                          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                          <div>
                            <p className="font-medium">Missing required fields:</p>
                            <ul className="mt-1 list-inside list-disc space-y-0.5">
                              {missing.map((m) => (
                                <li key={m}>{m}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between">
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                          {total > 0
                            ? `${filled} of ${total} required fields completed`
                            : 'No required fields'}
                        </p>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSection(step.key, state[step.key])
                          }}
                          className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
                        >
                          <Edit3 className="h-3 w-3" /> Edit
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )
        })}
      </AnimatePresence>

      <div className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
        <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Consent &amp; Terms</h3>
        <div className="mt-4 space-y-4">
          <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
            <div>
              <p className="text-sm font-medium text-slate-800 dark:text-slate-100">Accept Terms &amp; Conditions</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">You must accept to submit your profile</p>
            </div>
            <Switch
              checked={state.consents.terms_accepted}
              onChange={(v) => setSection('consents', { ...state.consents, terms_accepted: v })}
              label="Accept Terms"
            />
          </div>
          <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
            <div>
              <p className="text-sm font-medium text-slate-800 dark:text-slate-100">AI-Assisted Health Analysis</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Allow AI to analyze your profile data</p>
            </div>
            <Switch
              checked={state.consents.ai_consent}
              onChange={(v) => setSection('consents', { ...state.consents, ai_consent: v })}
              label="AI Analysis"
            />
          </div>
          <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
            <div>
              <p className="text-sm font-medium text-slate-800 dark:text-slate-100">Anonymized Research Consent</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Allow your data to be used for research</p>
            </div>
            <Switch
              checked={state.consents.research_consent}
              onChange={(v) => setSection('consents', { ...state.consents, research_consent: v })}
              label="Research Consent"
            />
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-4">
        <button
          type="button"
          onClick={() => setSection('consents', state.consents)}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
        >
          Save Draft
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting || !state.consents.terms_accepted}
          className={cn(
            'rounded-lg px-6 py-2 text-sm font-medium text-white transition-colors',
            submitting || !state.consents.terms_accepted
              ? 'cursor-not-allowed bg-blue-400'
              : 'bg-blue-600 hover:bg-blue-700',
          )}
        >
          {submitting ? (
            <span className="flex items-center gap-2">
              <Loader className="h-4 w-4 animate-spin" /> Submitting...
            </span>
          ) : (
            'Submit Profile'
          )}
        </button>
      </div>
    </div>
  )
}