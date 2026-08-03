import React, { useState } from 'react'
import { GitBranch, Plus, Play, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import { ContentLayout, Modal, StatusBadge, EmptyState, TableSkeleton, FormField } from '../components/ContentLayout'
import { useRuleSets, useEvaluateRule } from '../hooks/useCmsQueries'
import { cmsApi } from '../api/cmsApi'
import type { RuleSet, RuleEvaluationResult } from '../types'

export const RuleBuilderPage: React.FC = () => {
  const [selectedRuleSetId, setSelectedRuleSetId] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [formName, setFormName] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [formBodySystemId, setFormBodySystemId] = useState('')
  const [evalContext, setEvalContext] = useState('{}')
  const [evalResults, setEvalResults] = useState<RuleEvaluationResult[] | null>(null)

  const { data: ruleSets, isLoading } = useRuleSets()
  const evaluateMutation = useEvaluateRule()

  const selectedSet = ruleSets?.find((r) => r.id === selectedRuleSetId)

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formName) { toast.error('Name is required'); return }
    try {
      await cmsApi.rules.createSet({ name: formName, description: formDescription || null, body_system_id: formBodySystemId || null })
      toast.success('Rule set created')
      setShowCreate(false)
      setFormName('')
      setFormDescription('')
      setFormBodySystemId('')
    } catch {
      toast.error('Failed to create rule set')
    }
  }

  const handleEvaluate = async () => {
    if (!selectedRuleSetId) { toast.error('Select a rule set first'); return }
    let context: Record<string, unknown>
    try { context = JSON.parse(evalContext) } catch { toast.error('Invalid JSON context'); return }
    try {
      const results = await evaluateMutation.mutateAsync({ ruleSetId: selectedRuleSetId, context })
      setEvalResults(results)
      toast.success('Evaluation complete')
    } catch {
      toast.error('Evaluation failed')
    }
  }

  return (
    <ContentLayout title="Rule Builder" description="Create and evaluate clinical decision rules">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-amber-600" /> Rule Sets
            </h3>
            <button
              onClick={() => setShowCreate(true)}
              className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 transition"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          {isLoading ? (
            <TableSkeleton />
          ) : !ruleSets?.length ? (
            <EmptyState title="No rule sets" description="Create your first rule set" />
          ) : (
            <div className="space-y-2">
              {ruleSets.map((rs) => (
                <div
                  key={rs.id}
                  onClick={() => setSelectedRuleSetId(rs.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition ${
                    selectedRuleSetId === rs.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-slate-200 dark:border-slate-800 hover:border-slate-300'
                  }`}
                >
                  <p className="text-sm font-medium text-slate-900 dark:text-white">{rs.name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <StatusBadge status={rs.status} />
                    <span className="text-xs text-slate-500">v{rs.version}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-2 space-y-6">
          {selectedSet ? (
            <>
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">{selectedSet.name}</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">Description:</span>
                    <p className="text-slate-900 dark:text-white">{selectedSet.description || '-'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Body System:</span>
                    <p className="text-slate-900 dark:text-white">{selectedSet.body_system_id || '-'}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Status:</span>
                    <StatusBadge status={selectedSet.status} />
                  </div>
                  <div>
                    <span className="text-slate-500">Version:</span>
                    <p className="text-slate-900 dark:text-white">{selectedSet.version}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
                <h4 className="font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                  <Play className="w-4 h-4 text-emerald-600" /> Evaluate
                </h4>
                <textarea
                  rows={4}
                  value={evalContext}
                  onChange={(e) => setEvalContext(e.target.value)}
                  placeholder='{"key": "value"}'
                  className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm font-mono text-slate-900 dark:text-white mb-3"
                />
                <button
                  onClick={handleEvaluate}
                  disabled={evaluateMutation.isPending}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition flex items-center gap-2"
                >
                  {evaluateMutation.isPending ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Play className="w-4 h-4" />}
                  Evaluate
                </button>
                {evalResults && (
                  <div className="mt-4 space-y-2">
                    <h5 className="text-sm font-medium text-slate-900 dark:text-white">Results</h5>
                    {evalResults.map((r, i) => (
                      <div key={i} className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg text-sm">
                        <span className="font-medium text-slate-900 dark:text-white">{r.name}</span>: {String(r.result)}
                        {r.confidence !== null && <span className="text-slate-500 ml-2">(confidence: {r.confidence})</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
              <EmptyState
                title="Select a Rule Set"
                description="Choose a rule set from the left panel to view details and evaluate"
                icon={<AlertTriangle className="w-8 h-8" />}
              />
            </div>
          )}
        </div>
      </div>

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Rule Set">
        <form onSubmit={handleCreate} className="space-y-4">
          <FormField label="Name" required>
            <input
              type="text"
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              placeholder="Rule set name"
              className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white"
            />
          </FormField>
          <FormField label="Description">
            <textarea
              rows={3}
              value={formDescription}
              onChange={(e) => setFormDescription(e.target.value)}
              placeholder="Optional description"
              className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white"
            />
          </FormField>
          <FormField label="Body System ID">
            <input
              type="text"
              value={formBodySystemId}
              onChange={(e) => setFormBodySystemId(e.target.value)}
              placeholder="e.g. cardiovascular"
              className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white"
            />
          </FormField>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition">
              Create
            </button>
          </div>
        </form>
      </Modal>
    </ContentLayout>
  )
}
