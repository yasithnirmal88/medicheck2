import React, { useState } from 'react'
import {
  Activity,
  BarChart3,
  Bot,
  CheckCircle2,
  HeartPulse,
  Lightbulb,
  Send,
  ShieldCheck,
  User,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Question } from '../types'
import AutoSaveIndicator from './AutoSaveIndicator'

type Confidence = 'low' | 'medium' | 'high'

const CONFIDENCE_LABELS: Record<Confidence, string> = {
  low: 'Some uncertainty',
  medium: 'Moderate confidence',
  high: 'High confidence',
}

function confidenceColor(c: Confidence): string {
  if (c === 'low') return 'bg-amber-500'
  if (c === 'medium') return 'bg-emerald-500'
  return 'bg-indigo-600'
}

// Static context for the current question (placeholder until domain logic is wired).
const STATIC_CONTEXT = {
  whyMatters: 'This question helps assess risk factors that influence your personalized health profile and follow-up recommendations.',
  medicalExplanation:
    'The information you provide contributes to a clinical knowledge graph that links symptoms, conditions, and evidence-based guidance. Your answers are stored securely and reviewed in line with clinical best practices.',
  helpfulTip: 'Answer honestly and to the best of your knowledge. You can skip any non-required question and return later.',
  bodySystem: 'General',
  confidence: 'medium' as Confidence,
  progress: { answered: 3, total: 10, pct: 30 },
}

const SidebarSection: React.FC<{ icon: React.ReactNode; title: string; children: React.ReactNode }> = ({
  icon,
  title,
  children,
}) => (
  <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-slate-800">
    <div className="flex items-center gap-2 mb-2.5">
      <span className="flex h-5 w-5 items-center justify-center text-indigo-600 dark:text-indigo-400">{icon}</span>
      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
    </div>
    <div className="text-sm text-gray-600 dark:text-gray-300 space-y-2 leading-relaxed">{children}</div>
  </div>
)

type QuestionnaireSidebarProps = {
  question: Question | null | undefined
  answered: number
  totalQuestions: number
  completionPercentage: number
  saveStatus: 'idle' | 'saving' | 'saved' | 'error'
  isSaving: boolean
}

const QuestionnaireSidebar: React.FC<QuestionnaireSidebarProps> = ({
  question,
  answered,
  totalQuestions,
  completionPercentage,
  saveStatus,
  isSaving,
}) => {
  const [chatOpen, setChatOpen] = useState(false)
  const [chatInput, setChatInput] = useState('')

  const confidence: Confidence = STATIC_CONTEXT.confidence

  return (
    <aside className="w-full max-w-xs space-y-4 xl:w-80">
      {/* Why this question matters */}
      <SidebarSection icon={<HeartPulse className="h-4 w-4" />} title="Why this question matters">
        <p>{STATIC_CONTEXT.whyMatters}</p>
      </SidebarSection>

      {/* Medical explanation */}
      <SidebarSection icon={<ShieldCheck className="h-4 w-4" />} title="Medical explanation">
        <p>{STATIC_CONTEXT.medicalExplanation}</p>
      </SidebarSection>

      {/* Helpful tips */}
      <SidebarSection icon={<Lightbulb className="h-4 w-4" />} title="Helpful tips">
        <p>{STATIC_CONTEXT.helpfulTip}</p>
      </SidebarSection>

      {/* Current body system */}
      <SidebarSection icon={<Activity className="h-4 w-4" />} title="Current body system">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center justify-center h-6 w-6 rounded-lg bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40">
            <Activity className="h-4 w-4" />
          </span>
          <span className="font-medium text-gray-800 dark:text-gray-200">{STATIC_CONTEXT.bodySystem}</span>
        </div>
      </SidebarSection>

      {/* Progress */}
      <SidebarSection icon={<BarChart3 className="h-4 w-4" />} title="Progress">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>{answered}/{totalQuestions} answered</span>
            <span>{Math.round(completionPercentage)}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
            <div
              className="h-full rounded-full bg-indigo-600 transition-all"
              style={{ width: `${Math.min(100, Math.max(0, completionPercentage))}%` }}
              aria-hidden="true"
            />
          </div>
        </div>
      </SidebarSection>

      {/* Confidence meter */}
      <SidebarSection icon={<CheckCircle2 className="h-4 w-4" />} title="Confidence meter">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span
                className={cn(
                  'text-sm font-medium',
                  confidence === 'low'
                    ? 'text-amber-600'
                    : confidence === 'medium'
                      ? 'text-emerald-600'
                      : 'text-indigo-600',
                )}
              >
                {CONFIDENCE_LABELS[confidence]}
              </span>
            </div>
          <div className="flex items-center gap-1.5">
            {(['low', 'medium', 'high'] as Confidence[]).map((c, i) => {
              const active = i <= { low: 0, medium: 1, high: 2 }[confidence]
              return (
                <span
                  key={c}
                  className={cn(
                    'h-2.5 w-6 rounded-full transition-all',
                    active ? confidenceColor(confidence) : 'bg-gray-200 dark:bg-gray-700',
                  )}
                  aria-hidden="true"
                />
              )
            })}
          </div>
          <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
            <AutoSaveIndicator status={saveStatus === 'saving' ? 'saving' : saveStatus === 'error' ? 'error' : 'saved'} />
            <span>{isSaving ? 'Saving answer…' : 'Answer saved'}</span>
          </div>
        </div>
      </SidebarSection>

      {/* AI Assistant chat (collapsible) */}
      <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-slate-800">
        <button
          type="button"
          onClick={() => setChatOpen((o) => !o)}
          aria-expanded={chatOpen}
          className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left"
        >
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40">
              <Bot className="h-4 w-4" />
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">Assessment AI</span>
          </div>
          <span className="text-gray-500 dark:text-gray-400">{chatOpen ? <X className="h-4 w-4" /> : <Send className="h-4 w-4" />}</span>
        </button>

        {chatOpen && (
          <div
            className="border-t border-gray-200 px-4 py-3 dark:border-gray-700"
            aria-label="Assessment AI assistant"
          >
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Ask me why a question matters, what your answers mean, or how to review them.
            </p>
            <div className="mt-2 flex items-center gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    setChatInput('')
                  }
                }}
                placeholder="Ask the assistant..."
                className="flex-1 rounded-lg border border-gray-300 bg-gray-50 px-3 py-1.5 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60 dark:border-gray-600 dark:bg-slate-900 dark:text-gray-100"
              />
              <button
                type="button"
                onClick={() => setChatInput('')}
                aria-label="Send"
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}

export default React.memo(QuestionnaireSidebar)
