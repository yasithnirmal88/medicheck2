import React, { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Info, Loader2, Sparkles, FileText, ExternalLink, Languages, Gauge, ShieldCheck } from 'lucide-react'
import Card from '@/shared/ui/Card'
import {
  fetchReportExplanation,
  type AIExplanation,
  type AIRetrievedEvidence,
  type AISourceBreakdownItem,
  type LiteracyLevel,
} from '../api/patientService'

interface ReportExplanationProps {
  sessionId: string | undefined
}

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'si', label: 'සිංහල' },
  { value: 'ta', label: 'தமிழ்' },
] as const

const LITERACY_LEVELS: { value: LiteracyLevel; label: string }[] = [
  { value: 'simple', label: 'Simple' },
  { value: 'standard', label: 'Standard' },
  { value: 'detailed', label: 'Detailed' },
]

const QUALITY_STATUS_LABELS: Record<string, { label: string; tone: string }> = {
  valid: { label: 'AI explanation verified', tone: 'text-emerald-600' },
  evidence_unavailable: { label: 'No supporting evidence available', tone: 'text-amber-600' },
  fallback: { label: 'Fallback explanation used', tone: 'text-amber-600' },
  validation_failed: { label: 'AI output validation failed', tone: 'text-red-600' },
  provider_unavailable: { label: 'AI provider unavailable', tone: 'text-amber-600' },
}

/**
 * AI-assisted explanation of an already-generated deterministic report.
 *
 * Boundaries: this component only EXPLAINS the deterministic report. It never
 * replaces it, never hides deterministic findings, and never diagnoses. If the
 * AI explanation is unavailable, the parent report remains fully visible.
 *
 * Phase 7: supports language (EN/SI/TA) and literacy level (Simple/Standard/
 * Detailed) selection. The deterministic result is identical at every level;
 * only communication changes. Also renders the AI transparency notice, the
 * "Show the source" source breakdown, and the AI quality status.
 */
const ReportExplanation: React.FC<ReportExplanationProps> = ({ sessionId }) => {
  const [language, setLanguage] = useState<string>('en')
  const [literacy, setLiteracy] = useState<LiteracyLevel>('standard')

  const { data, isLoading, isError, error } = useQuery<AIExplanation>({
    queryKey: ['report-explanation', sessionId, language, literacy],
    queryFn: () =>
      fetchReportExplanation(sessionId || '', {
        language,
        literacy_level: literacy,
      }),
    enabled: !!sessionId,
    retry: false,
    staleTime: 1000 * 60 * 30,
  })

  // Map retrieved evidence id → record, for citation lookups by finding.
  const evidenceById = useMemo(() => {
    const m = new Map<string, AIRetrievedEvidence>()
    for (const e of data?.retrieved_evidence ?? []) {
      m.set(e.id, e)
    }
    return m
  }, [data])

  if (!sessionId) {
    return null
  }

  if (isLoading) {
    return (
      <Card className="mt-6 border-indigo-100">
        <SectionHeader />
        <PersonalizationControls
          language={language}
          literacy={literacy}
          setLanguage={setLanguage}
          setLiteracy={setLiteracy}
        />
        <div className="flex items-center gap-2 text-sm text-gray-500 mt-3">
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
          <span>Preparing your explanation...</span>
        </div>
      </Card>
    )
  }

  if (isError || !data) {
    return (
      <Card className="mt-6 border-amber-100">
        <SectionHeader />
        <PersonalizationControls
          language={language}
          literacy={literacy}
          setLanguage={setLanguage}
          setLiteracy={setLiteracy}
        />
        <div className="flex items-start gap-2 text-sm text-gray-600 mt-3">
          <AlertTriangle
            className="w-4 h-4 text-amber-500 mt-0.5 shrink-0"
            aria-hidden
          />
          <span>
            We couldn't generate the explanation right now. Your clinical
            assessment is still available below.
          </span>
        </div>
        {error ? (
          <span className="sr-only">
            Explanation request failed. The clinical report is unaffected.
          </span>
        ) : null}
      </Card>
    )
  }

  if (!data.available) {
    return (
      <Card className="mt-6 border-amber-100">
        <SectionHeader />
        <PersonalizationControls
          language={language}
          literacy={literacy}
          setLanguage={setLanguage}
          setLiteracy={setLiteracy}
        />
        <div className="flex items-start gap-2 text-sm text-gray-600 mt-3">
          <AlertTriangle
            className="w-4 h-4 text-amber-500 mt-0.5 shrink-0"
            aria-hidden
          />
          <span>
            We couldn't generate the explanation right now. Your clinical
            assessment is still available below.
          </span>
        </div>
      </Card>
    )
  }

  const retrievedEvidence = data.retrieved_evidence ?? []
  const evidenceAvailable = data.evidence_available ?? retrievedEvidence.length > 0
  const qualityInfo = data.quality_status
    ? QUALITY_STATUS_LABELS[data.quality_status] ?? {
        label: data.quality_status,
        tone: 'text-gray-600',
      }
    : null
  const sourceBreakdown = data.source_breakdown ?? []

  return (
    <Card className="mt-6 border-indigo-100">
      <SectionHeader />
      <PersonalizationControls
        language={language}
        literacy={literacy}
        setLanguage={setLanguage}
        setLiteracy={setLiteracy}
      />

      {qualityInfo ? (
        <div className={`flex items-center gap-1.5 text-xs ${qualityInfo.tone} mt-3`} role="status">
          <ShieldCheck className="w-3.5 h-3.5" aria-hidden />
          <span>{qualityInfo.label}</span>
        </div>
      ) : null}

      <div className="space-y-5 mt-4">
        <section>
          <h3 className="text-sm font-semibold text-gray-900">What this means</h3>
          <p className="text-sm text-gray-700 mt-1">{data.summary}</p>
        </section>

        {data.severity_explanation ? (
          <section>
            <h3 className="text-sm font-semibold text-gray-900">
              Understanding the severity
            </h3>
            <p className="text-sm text-gray-700 mt-1">
              {data.severity_explanation}
            </p>
          </section>
        ) : null}

        {data.key_findings.length > 0 ? (
          <section>
            <h3 className="text-sm font-semibold text-gray-900">
              Why these findings matter
            </h3>
            <ul className="mt-2 space-y-3">
              {data.key_findings.map((f, i) => {
                const cited = (f.evidence_ids ?? [])
                  .map((id) => evidenceById.get(id))
                  .filter((e): e is AIRetrievedEvidence => Boolean(e))
                return (
                  <li key={i} className="p-3 border rounded-lg bg-gray-50">
                    <div className="text-sm font-medium text-gray-900">
                      {f.title}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {f.explanation}
                    </div>
                    {cited.length > 0 ? (
                      <div className="mt-2 text-xs text-gray-500 flex flex-wrap items-center gap-1">
                        <FileText className="w-3.5 h-3.5 shrink-0" aria-hidden />
                        <span>Based on evidence associated with this finding:</span>
                        {cited.map((e, idx) => (
                          <span key={e.id} className="inline-flex items-center gap-0.5">
                            {idx > 0 ? <span>,</span> : null}
                            {e.url ? (
                              <a
                                href={e.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-indigo-600 underline hover:text-indigo-700 inline-flex items-center gap-0.5"
                              >
                                [{idx + 1}]
                                <ExternalLink className="w-3 h-3" aria-hidden />
                              </a>
                            ) : (
                              <span className="text-gray-500">[{idx + 1}]</span>
                            )}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </li>
                )
              })}
            </ul>
          </section>
        ) : null}

        {data.recommendation_explanations.length > 0 ? (
          <section>
            <h3 className="text-sm font-semibold text-gray-900">
              Understanding your recommendations
            </h3>
            <ul className="mt-2 space-y-2">
              {data.recommendation_explanations.map((r, i) => (
                <li key={i} className="text-sm text-gray-700">
                  <span className="font-medium">•</span> {r.explanation}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {/* Source breakdown — "Show the source" transparency chain. */}
        {sourceBreakdown.length > 0 ? (
          <section className="p-3 border border-indigo-100 rounded-lg bg-indigo-50/30">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-indigo-600" aria-hidden />
              <h3 className="text-sm font-semibold text-gray-900">
                Show the source
              </h3>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Each finding is traceable to the deterministic engine, your
              answers, and supporting evidence. Nothing here is invented.
            </p>
            <ul className="mt-2 space-y-2">
              {sourceBreakdown.map((s, i) => (
                <SourceBreakdownRow
                  key={i}
                  item={s}
                  evidenceById={evidenceById}
                />
              ))}
            </ul>
          </section>
        ) : null}

        {/* Evidence section — visually distinct from AI prose so the patient
            can tell approved supporting evidence apart from AI-generated text. */}
        {evidenceAvailable && retrievedEvidence.length > 0 ? (
          <section className="p-3 border border-gray-200 rounded-lg bg-white">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-gray-600" aria-hidden />
              <h3 className="text-sm font-semibold text-gray-900">
                Evidence
              </h3>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Retrieved from the MediCheck approved clinical evidence repository.
              These references are not generated by the AI.
            </p>
            <ul className="mt-2 space-y-2">
              {retrievedEvidence.map((e, idx) => (
                <li key={e.id} className="text-sm">
                  <div className="flex items-start gap-1.5">
                    <span className="text-xs font-medium text-gray-400 mt-0.5">
                      [{idx + 1}]
                    </span>
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-gray-800 break-words">
                        {e.title}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5 flex flex-wrap gap-x-2 gap-y-0.5">
                        {e.evidence_level ? (
                          <span>Evidence level: {e.evidence_level}</span>
                        ) : null}
                        {e.source ? <span>Source: {e.source}</span> : null}
                        {e.relevance != null ? (
                          <span>Relevance: {(e.relevance * 100).toFixed(0)}%</span>
                        ) : null}
                      </div>
                      {e.excerpt ? (
                        <p className="text-xs text-gray-500 mt-1">{e.excerpt}</p>
                      ) : null}
                      {e.url ? (
                        <a
                          href={e.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-indigo-600 underline hover:text-indigo-700 inline-flex items-center gap-0.5 mt-1"
                        >
                          View source
                          <ExternalLink className="w-3 h-3" aria-hidden />
                        </a>
                      ) : null}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ) : (
          <section className="p-3 border border-gray-200 rounded-lg bg-white">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-gray-400" aria-hidden />
              <h3 className="text-sm font-semibold text-gray-700">Evidence</h3>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              No supporting evidence was available from the MediCheck evidence
              repository for this explanation.
            </p>
          </section>
        )}

        {data.evidence_notes.length > 0 ? (
          <section>
            <h3 className="text-sm font-semibold text-gray-900">
              Supporting evidence notes
            </h3>
            <ul className="mt-2 space-y-1">
              {data.evidence_notes.map((n, i) => (
                <li key={i} className="text-xs text-gray-500 flex gap-1">
                  <Info className="w-3.5 h-3.5 mt-0.5 shrink-0" aria-hidden />
                  <span>{n}</span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {data.limitations ? (
          <section>
            <h3 className="text-sm font-semibold text-gray-900">Limitations</h3>
            <p className="text-sm text-gray-600 mt-1">{data.limitations}</p>
          </section>
        ) : null}

        {data.transparency_notice ? (
          <section className="p-3 border border-gray-200 rounded-lg bg-gray-50">
            <div className="flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-gray-600 mt-0.5 shrink-0" aria-hidden />
              <p className="text-xs text-gray-600">{data.transparency_notice}</p>
            </div>
          </section>
        ) : null}

        <div className="pt-3 border-t border-gray-100">
          <div className="flex items-start gap-2">
            <Sparkles
              className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0"
              aria-hidden
            />
            <p className="text-xs text-gray-500">
              <span className="font-medium">AI-generated explanation.</span>{' '}
              {data.disclaimer} This is not a diagnosis. If you are experiencing
              urgent symptoms, follow the guidance provided with your assessment
              and contact a healthcare professional.
            </p>
          </div>
        </div>
      </div>
    </Card>
  )
}

const SectionHeader: React.FC = () => (
  <div className="flex items-center gap-2">
    <Sparkles className="w-5 h-5 text-indigo-500" aria-hidden />
    <h2 className="text-lg font-semibold text-gray-900">AI Explanation</h2>
  </div>
)

const PersonalizationControls: React.FC<{
  language: string
  literacy: LiteracyLevel
  setLanguage: (v: string) => void
  setLiteracy: (v: LiteracyLevel) => void
}> = ({ language, literacy, setLanguage, setLiteracy }) => (
  <div className="flex flex-wrap items-center gap-3 mt-3">
    <label className="flex items-center gap-1.5 text-xs text-gray-600">
      <Languages className="w-3.5 h-3.5" aria-hidden />
      <span className="font-medium">Language</span>
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        className="border border-gray-300 rounded px-1.5 py-0.5 text-xs bg-white"
        aria-label="Explanation language"
      >
        {LANGUAGES.map((l) => (
          <option key={l.value} value={l.value}>
            {l.label}
          </option>
        ))}
      </select>
    </label>
    <label className="flex items-center gap-1.5 text-xs text-gray-600">
      <Gauge className="w-3.5 h-3.5" aria-hidden />
      <span className="font-medium">Detail level</span>
      <select
        value={literacy}
        onChange={(e) => setLiteracy(e.target.value as LiteracyLevel)}
        className="border border-gray-300 rounded px-1.5 py-0.5 text-xs bg-white"
        aria-label="Detail level"
      >
        {LITERACY_LEVELS.map((l) => (
          <option key={l.value} value={l.value}>
            {l.label}
          </option>
        ))}
      </select>
    </label>
  </div>
)

const SourceBreakdownRow: React.FC<{
  item: AISourceBreakdownItem
  evidenceById: Map<string, AIRetrievedEvidence>
}> = ({ item, evidenceById }) => {
  const cited = item.evidence_ids
    .map((id) => evidenceById.get(id))
    .filter((e): e is AIRetrievedEvidence => Boolean(e))
  return (
    <li className="text-xs text-gray-600 p-2 border border-gray-100 rounded bg-white">
      <div className="font-medium text-gray-800">{item.clinical_finding}</div>
      <div className="mt-0.5 text-gray-500">
        <span className="font-medium text-gray-600">Source chain:</span>{' '}
        {item.knowledge_graph_relationship}
        {item.deterministic_score != null
          ? ` · score ${item.deterministic_score.toFixed(2)}`
          : ''}
        {item.trace_id ? ` · trace ${item.trace_id.slice(0, 8)}` : ''}
      </div>
      {cited.length > 0 ? (
        <div className="mt-1 flex flex-wrap items-center gap-1 text-gray-500">
          <span>Evidence:</span>
          {cited.map((e, idx) => (
            <span key={e.id} className="inline-flex items-center gap-0.5">
              {idx > 0 ? <span>,</span> : null}
              {e.url ? (
                <a
                  href={e.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-600 underline hover:text-indigo-700 inline-flex items-center gap-0.5"
                >
                  [{idx + 1}]
                  <ExternalLink className="w-3 h-3" aria-hidden />
                </a>
              ) : (
                <span className="text-gray-500">[{idx + 1}]</span>
              )}
            </span>
          ))}
        </div>
      ) : null}
    </li>
  )
}

export default ReportExplanation
