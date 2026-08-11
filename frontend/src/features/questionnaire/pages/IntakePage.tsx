import React, { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  HelpCircle,
  Loader2,
  MessageSquareText,
  Mic,
  Repeat,
  Sparkles,
  Square,
  X,
} from 'lucide-react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import {
  extractIntake,
  transcribeAudio,
  type IntakeLanguage,
  type IntakeResponse,
  type IntakeObservation,
} from '../api/intakeService'
import { useStartSession, useTemplates } from '../hooks/useQuestionnaire'
import { useVoiceRecorder } from '../hooks/useVoiceRecorder'

/**
 * Phase 3/5 — AI Clinical Intake (multilingual + voice).
 *
 * An OPTIONAL assisted entry point. The patient describes what they are
 * experiencing in natural language (typed or spoken, in English/Sinhala/Tamil);
 * the AI extracts structured observations and maps them to EXISTING clinical
 * indicators. The knowledge graph then recommends relevant existing question
 * groups. The patient can edit, reject interpretations, skip AI entirely, or
 * continue to the standard questionnaire. The deterministic CDSE remains the
 * clinical decision layer.
 *
 * Phase 5: the language layer is an INTERFACE layer only — localized input
 * always resolves to the SAME canonical indicator IDs. Voice input is
 * transcribed to text, reviewed/edited by the patient, THEN fed into the same
 * Phase 3 intake pipeline. Audio is never stored or logged.
 *
 * Safety language: no diagnoses, no "AI detected your disease". Only
 * informational phrasing such as "we identified some information that may be
 * relevant".
 */

const LANGUAGES: { code: IntakeLanguage; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'si', label: 'සිංහල' },
  { code: 'ta', label: 'தமிழ்' },
]
const IntakePage: React.FC = () => {
  const navigate = useNavigate()
  const [text, setText] = useState('')
  const [language, setLanguage] = useState<IntakeLanguage>('en')
  const [transcribing, setTranscribing] = useState(false)
  const [voiceError, setVoiceError] = useState<string | null>(null)
  const [inputType, setInputType] = useState<'text' | 'voice'>('text')
  const [result, setResult] = useState<IntakeResponse | null>(null)
  const [rejectedObservations, setRejectedObservations] = useState<Set<string>>(new Set())
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const { data: templates } = useTemplates()
  const startSession = useStartSession()
  const recorder = useVoiceRecorder()

  const mutation = useMutation({
    mutationFn: () => extractIntake({ text, language, input_type: inputType }),
    onSuccess: (data) => {
      setResult(data)
      setRejectedObservations(new Set())
      setErrorMsg(null)
    },
    onError: () => {
      setErrorMsg('Something went wrong. You can continue with the standard questionnaire.')
    },
  })

  const handleStartRecording = async () => {
    setVoiceError(null)
    await recorder.start()
  }

  const handleStopRecording = async () => {
    const blob = await recorder.stop()
    if (!blob) return
    setTranscribing(true)
    try {
      const result = await transcribeAudio(blob, language)
      setText(result.transcript)
      setInputType('voice')
    } catch {
      setVoiceError('Voice input isn\'t available right now. You can type instead.')
    } finally {
      setTranscribing(false)
    }
  }

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value)
    setInputType('text')
  }

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLanguage(e.target.value as IntakeLanguage)
  }

  const activeObservations = useMemo(
    () => (result?.observations ?? []).filter((o) => !rejectedObservations.has(o.id)),
    [result, rejectedObservations],
  )

  const acceptedCandidateIndicators = useMemo(() => {
    if (!result) return []
    const obsIds = new Set(activeObservations.map((o) => o.id))
    return result.candidate_indicators.filter(
      (c) => c.observation_ids.length === 0 || c.observation_ids.some((id) => obsIds.has(id)),
    )
  }, [result, activeObservations])

  const recommendedGroups = useMemo(
    () => result?.candidate_question_groups ?? [],
    [result],
  )

  const handleRejectObservation = (id: string) => {
    setRejectedObservations((prev) => new Set(prev).add(id))
  }

  const handleStartAssessment = (code: string) => {
    let templateId: string | undefined
    if (templates?.length) {
      const match = templates.find((t) => t.code === code)
      templateId = match?.id
    }
    if (templateId) {
      startSession.mutate(templateId, {
        onSuccess: (session) => navigate(`/questionnaires/${session.id}`),
      })
    } else {
      // Fall back to the standard selection page if no backend template matches.
      navigate('/assessments')
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    mutation.mutate()
  }

  const handleSkip = () => navigate('/assessments')

  const handleEdit = () => {
    setResult(null)
  }

  const isLoading = mutation.isPending
  const isUnavailable = result && !result.available

  return (
    <AppLayout>
      <div className="mx-auto max-w-3xl space-y-6 py-2">
        <header className="space-y-2">
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-300">
            <Sparkles className="w-5 h-5" aria-hidden />
            <h1 className="text-xl font-semibold">Tell us what you&apos;re experiencing</h1>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Describe anything you&apos;ve noticed recently in your own words. We&apos;ll help identify
            information that may be relevant and suggest a few questions to clarify it. This is an
            optional assisted step — you can always use the standard questionnaire.
          </p>
        </header>

        <Card className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <label htmlFor="intake-text" className="block text-sm font-medium text-gray-700 dark:text-gray-200">
                How are you feeling?
              </label>
              <label className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                Language:
                <select
                  value={language}
                  onChange={handleLanguageChange}
                  disabled={isLoading || !!result || transcribing}
                  aria-label="Select your language"
                  className="rounded border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  {LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code}>{l.label}</option>
                  ))}
                </select>
              </label>
            </div>
            <textarea
              id="intake-text"
              className="w-full min-h-[120px] rounded border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-900 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              placeholder="I have been getting tired when climbing stairs..."
              value={text}
              onChange={handleTextChange}
              disabled={isLoading || !!result || transcribing}
              aria-describedby="intake-help"
            />
            <p id="intake-help" className="text-xs text-gray-500">
              You can type, speak, edit your description, reject an interpretation, or skip this step at any time.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              {!result && (
                <button
                  type="submit"
                  className="inline-flex items-center gap-2 rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                  disabled={isLoading || transcribing || !text.trim()}
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden /> : <ArrowRight className="w-4 h-4" aria-hidden />}
                  {isLoading ? 'Analyzing...' : 'Continue'}
                </button>
              )}
              {!result && recorder.isSupported && recorder.state !== 'recording' && (
                <button
                  type="button"
                  onClick={handleStartRecording}
                  disabled={isLoading || transcribing}
                  className="inline-flex items-center gap-2 rounded border border-indigo-300 dark:border-indigo-700 px-4 py-2 text-sm font-medium text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 disabled:opacity-50"
                >
                  {transcribing ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden /> : <Mic className="w-4 h-4" aria-hidden />}
                  {transcribing ? 'Transcribing...' : 'Speak'}
                </button>
              )}
              {recorder.state === 'recording' && (
                <button
                  type="button"
                  onClick={handleStopRecording}
                  className="inline-flex items-center gap-2 rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                >
                  <Square className="w-4 h-4" aria-hidden /> Stop
                </button>
              )}
              <button
                type="button"
                onClick={handleSkip}
                className="inline-flex items-center gap-2 rounded border border-gray-300 dark:border-slate-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-slate-700"
              >
                Skip AI intake
              </button>
            </div>
            {inputType === 'voice' && text && !result && (
              <div className="rounded border border-amber-200 bg-amber-50 dark:bg-amber-900/20 p-3 text-sm text-amber-800 dark:text-amber-200">
                <p className="font-medium">Please review your transcript</p>
                <p className="mt-1">This was transcribed from your voice. Edit it above if anything is incorrect, then continue. We won&apos;t interpret it until you confirm.</p>
              </div>
            )}
          </form>

          {errorMsg && (
            <div className="flex items-start gap-2 rounded border border-amber-200 bg-amber-50 dark:bg-amber-900/20 p-3 text-sm text-amber-800 dark:text-amber-200">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" aria-hidden />
              <span>{errorMsg}</span>
            </div>
          )}

          {voiceError && (
            <div className="flex items-start gap-2 rounded border border-amber-200 bg-amber-50 dark:bg-amber-900/20 p-3 text-sm text-amber-800 dark:text-amber-200">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" aria-hidden />
              <span>{voiceError}</span>
            </div>
          )}

          {isUnavailable && (
            <div className="flex items-start gap-2 rounded border border-amber-200 bg-amber-50 dark:bg-amber-900/20 p-3 text-sm text-amber-800 dark:text-amber-200">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" aria-hidden />
              <div>
                <p className="font-medium">AI-assisted intake is currently unavailable.</p>
                <p className="mt-1">{result?.message ?? 'You can continue with the standard questionnaire.'}</p>
                <button
                  type="button"
                  onClick={handleSkip}
                  className="mt-2 inline-flex items-center gap-1 text-indigo-600 hover:underline"
                >
                  Continue with standard questionnaire <ArrowRight className="w-3 h-3" aria-hidden />
                </button>
              </div>
            </div>
          )}
        </Card>

        {result && result.available && (
          <ResultsSection
            observations={activeObservations}
            candidateCount={acceptedCandidateIndicators.length}
            recommendedGroups={recommendedGroups}
            clarifications={result.clarifications}
            onRejectObservation={handleRejectObservation}
            onEdit={handleEdit}
            onStartAssessment={handleStartAssessment}
            starting={startSession.isPending}
          />
        )}
      </div>
    </AppLayout>
  )
}

interface ResultsSectionProps {
  observations: IntakeObservation[]
  candidateCount: number
  clarifications: IntakeResponse['clarifications']
  recommendedGroups: IntakeResponse['candidate_question_groups']
  onRejectObservation: (id: string) => void
  onEdit: () => void
  onStartAssessment: (code: string) => void
  starting: boolean
}

const ResultsSection: React.FC<ResultsSectionProps> = ({
  observations,
  candidateCount,
  clarifications,
  recommendedGroups,
  onRejectObservation,
  onEdit,
  onStartAssessment,
  starting,
}) => {
  return (
    <Card className="space-y-5 border-indigo-100">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-300">
          <CheckCircle2 className="w-5 h-5" aria-hidden />
          <h2 className="text-base font-semibold">We noticed a few things that may be relevant</h2>
        </div>
        <button
          type="button"
          onClick={onEdit}
          className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
        >
          <MessageSquareText className="w-3.5 h-3.5" aria-hidden /> Edit description
        </button>
      </div>

      <ul className="space-y-2">
        {observations.map((o) => (
          <li
            key={o.id}
            className="flex items-start justify-between gap-3 rounded border border-gray-200 dark:border-slate-700 p-3"
          >
            <div className="space-y-1 text-sm">
              <p className="font-medium text-gray-800 dark:text-gray-100">{o.normalized_concept}</p>
              <p className="text-xs text-gray-500">&ldquo;{o.source_text}&rdquo;</p>
              <div className="flex flex-wrap gap-2 text-[11px] text-gray-500">
                {o.polarity === 'negative' && <Badge color="gray">negated</Badge>}
                {o.polarity === 'uncertain' && <Badge color="amber">uncertain</Badge>}
                <Badge color="blue">{o.certainty}</Badge>
                <Badge color="violet">{o.temporality}</Badge>
                {o.duration && (
                  <Badge color="teal">
                    <Clock className="w-3 h-3 mr-1" aria-hidden /> {o.duration}
                  </Badge>
                )}
                {o.frequency && (
                  <Badge color="teal">
                    <Repeat className="w-3 h-3 mr-1" aria-hidden /> {o.frequency}
                  </Badge>
                )}
              </div>
            </div>
            <button
              type="button"
              onClick={() => onRejectObservation(o.id)}
              aria-label="Reject this interpretation"
              className="shrink-0 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-slate-700"
            >
              <X className="w-4 h-4" aria-hidden />
            </button>
          </li>
        ))}
      </ul>

      <p className="text-sm text-gray-600 dark:text-gray-400">
        We identified {candidateCount} possible relevant indicator{candidateCount === 1 ? '' : 's'}. Your answers
        will be evaluated using MediCheck&apos;s clinical assessment system.
      </p>

      {clarifications.length > 0 && (
        <div className="rounded border border-sky-100 bg-sky-50 dark:bg-sky-900/20 p-3">
          <div className="flex items-center gap-2 text-sky-700 dark:text-sky-300">
            <HelpCircle className="w-4 h-4" aria-hidden />
            <h3 className="text-sm font-medium">A few clarifying questions</h3>
          </div>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700 dark:text-gray-300">
            {clarifications.map((c, i) => (
              <li key={i}>{c.text}</li>
            ))}
          </ul>
        </div>
      )}

      {recommendedGroups.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-200">Recommended assessments</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {recommendedGroups.map((g) => (
              <button
                key={g.question_group_id}
                type="button"
                onClick={() => onStartAssessment(g.code)}
                disabled={starting}
                className="flex items-center justify-between gap-2 rounded border border-gray-200 dark:border-slate-700 p-3 text-left text-sm hover:border-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 disabled:opacity-50"
              >
                <span className="font-medium text-gray-800 dark:text-gray-100">{g.name}</span>
                <ArrowRight className="w-4 h-4 text-indigo-500" aria-hidden />
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between gap-2 border-t border-gray-100 dark:border-slate-700 pt-3">
        <p className="text-xs text-gray-500">
          This is not a diagnosis. MediCheck&apos;s clinical assessment system evaluates your answers.
        </p>
        <button
          type="button"
          onClick={() => onStartAssessment('standard-assessment')}
          disabled={starting}
          className="inline-flex items-center gap-2 rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {starting ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden /> : <ArrowRight className="w-4 h-4" aria-hidden />}
          Continue to questions
        </button>
      </div>
    </Card>
  )
}

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span
    className={`inline-flex items-center rounded-full bg-${color}-100 dark:bg-${color}-900/30 px-2 py-0.5 text-${color}-700 dark:text-${color}-300`}
  >
    {children}
  </span>
)

export default IntakePage
