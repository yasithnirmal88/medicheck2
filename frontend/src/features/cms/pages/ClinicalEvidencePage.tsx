import React, { useState } from 'react'
import { BookOpen, Search, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'
import { ContentLayout, StatusBadge, EmptyState, TableSkeleton, FormField } from '../components/ContentLayout'
import { useEvidenceReferences } from '../hooks/useCmsQueries'
import { cmsApi } from '../api/cmsApi'
import type { EvidenceReference } from '../types'

const evidenceLevels = ['', 'Level I', 'Level II', 'Level III', 'Level IV', 'Level V']

export const ClinicalEvidencePage: React.FC = () => {
  const [searchTitle, setSearchTitle] = useState('')
  const [searchPmid, setSearchPmid] = useState('')
  const [searchDoi, setSearchDoi] = useState('')
  const [searchLevel, setSearchLevel] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const { data: evidenceData, isLoading } = useEvidenceReferences({
    ...(searchTitle ? { title: searchTitle } : {}),
    ...(searchPmid ? { pmid: searchPmid } : {}),
    ...(searchDoi ? { doi: searchDoi } : {}),
    ...(searchLevel ? { evidence_level: searchLevel } : {}),
  })

  const evidenceList = evidenceData?.items ?? []

  const [formTitle, setFormTitle] = useState('')
  const [formCitation, setFormCitation] = useState('')
  const [formPmid, setFormPmid] = useState('')
  const [formDoi, setFormDoi] = useState('')
  const [formLevel, setFormLevel] = useState('Level I')
  const [formConfidence, setFormConfidence] = useState(0)
  const [formSummary, setFormSummary] = useState('')

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formTitle) { toast.error('Title is required'); return }
    try {
      await cmsApi.evidenceReferences.create({
        title: formTitle,
        citation: formCitation || null,
        pmid: formPmid || null,
        doi: formDoi || null,
        evidence_level: formLevel || null,
        confidence_score: formConfidence || null,
        summary: formSummary || null,
      } as Partial<EvidenceReference>)
      toast.success('Evidence reference created')
      setShowCreate(false)
      setFormTitle('')
      setFormCitation('')
      setFormPmid('')
      setFormDoi('')
      setFormLevel('Level I')
      setFormConfidence(0)
      setFormSummary('')
    } catch { toast.error('Failed to create evidence reference') }
  }

  return (
    <ContentLayout
      title="Clinical Evidence"
      description="Manage PubMed literature references and evidence grades"
      actions={
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition flex items-center gap-2">
          <BookOpen className="w-4 h-4" /> Create Evidence
        </button>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <Search className="w-4 h-4 text-blue-600" /> Search
          </h3>
          <div className="space-y-3">
            <FormField label="Title">
              <input type="text" value={searchTitle} onChange={(e) => setSearchTitle(e.target.value)} placeholder="Search title..." className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
            </FormField>
            <FormField label="PMID">
              <input type="text" value={searchPmid} onChange={(e) => setSearchPmid(e.target.value)} placeholder="PubMed ID" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
            </FormField>
            <FormField label="DOI">
              <input type="text" value={searchDoi} onChange={(e) => setSearchDoi(e.target.value)} placeholder="Digital Object Identifier" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
            </FormField>
            <FormField label="Evidence Level">
              <select value={searchLevel} onChange={(e) => setSearchLevel(e.target.value)} className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white">
                {evidenceLevels.map((l) => <option key={l} value={l}>{l || 'All Levels'}</option>)}
              </select>
            </FormField>
          </div>
        </div>

        <div className="lg:col-span-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Evidence Library</h3>
          {isLoading ? (
            <TableSkeleton />
          ) : !evidenceList.length ? (
            <EmptyState title="No evidence references" description="Try adjusting your search or create a new reference" />
          ) : (
            <div className="space-y-3">
              {evidenceList.map((e) => (
                <div key={e.id} className="p-4 border border-slate-200 dark:border-slate-800 rounded-lg">
                  <div className="flex items-start justify-between mb-1">
                    <h4 className="text-sm font-medium text-slate-900 dark:text-white">{e.title}</h4>
                    <StatusBadge status={e.evidence_level ?? 'unknown'} />
                  </div>
                  {e.citation && <p className="text-xs text-slate-500 mb-1">{e.citation}</p>}
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    {e.pmid && (
                      <a href={`https://pubmed.ncbi.nlm.nih.gov/${e.pmid}`} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline flex items-center gap-1">
                        PMID: {e.pmid} <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                    {e.confidence_score !== null && <span>Confidence: {e.confidence_score}</span>}
                  </div>
                  {e.summary && <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">{e.summary}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showCreate && (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Create Evidence Reference</h3>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Title" required>
              <input type="text" value={formTitle} onChange={(e) => setFormTitle(e.target.value)} placeholder="Paper title" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
            </FormField>
            <FormField label="Citation">
              <input type="text" value={formCitation} onChange={(e) => setFormCitation(e.target.value)} placeholder="Full citation" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
            </FormField>
            <FormField label="PMID">
              <input type="text" value={formPmid} onChange={(e) => setFormPmid(e.target.value)} placeholder="PubMed ID" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
            </FormField>
            <FormField label="DOI">
              <input type="text" value={formDoi} onChange={(e) => setFormDoi(e.target.value)} placeholder="DOI" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
            </FormField>
            <FormField label="Evidence Level">
              <select value={formLevel} onChange={(e) => setFormLevel(e.target.value)} className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white">
                {evidenceLevels.filter(Boolean).map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </FormField>
            <FormField label="Confidence Score">
              <input type="number" min={0} max={100} value={formConfidence} onChange={(e) => setFormConfidence(Number(e.target.value))} className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
            </FormField>
            <div className="md:col-span-2">
              <FormField label="Summary">
                <textarea rows={3} value={formSummary} onChange={(e) => setFormSummary(e.target.value)} placeholder="Brief summary" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
              </FormField>
            </div>
            <div className="md:col-span-2 flex justify-end gap-3">
              <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition">Cancel</button>
              <button type="submit" className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition">Save</button>
            </div>
          </form>
        </div>
      )}
    </ContentLayout>
  )
}
