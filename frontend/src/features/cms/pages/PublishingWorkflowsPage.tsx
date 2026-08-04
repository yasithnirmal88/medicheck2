import React, { useState } from 'react'
import { GitMerge, Plus } from 'lucide-react'
import toast from 'react-hot-toast'
import { ContentLayout, StatusBadge, EmptyState, TableSkeleton, Modal, FormField } from '../components/ContentLayout'
import { useWorkflows } from '../hooks/useCmsQueries'
import { cmsApi } from '../api/cmsApi'

export const PublishingWorkflowsPage: React.FC = () => {
  const [showCreate, setShowCreate] = useState(false)
  const [formName, setFormName] = useState('')
  const [formEntityType, setFormEntityType] = useState('')
  const [formDescription, setFormDescription] = useState('')

  const { data: workflows, isLoading } = useWorkflows()

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formName || !formEntityType) { toast.error('Name and entity type are required'); return }
    try {
      await cmsApi.publishing.createWorkflow({ name: formName, entity_type: formEntityType, description: formDescription || null })
      toast.success('Workflow created')
      setShowCreate(false)
      setFormName('')
      setFormEntityType('')
      setFormDescription('')
    } catch { toast.error('Failed to create workflow') }
  }

  return (
    <ContentLayout
      title="Publishing Workflows"
      description="Manage publishing workflows and approval pipelines"
      actions={
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition">
          <Plus className="w-4 h-4" /> Create Workflow
        </button>
      }
    >
      {isLoading ? (
        <TableSkeleton rows={4} />
      ) : !workflows?.length ? (
        <EmptyState title="No workflows" description="Create your first publishing workflow" icon={<GitMerge className="w-8 h-8" />} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workflows.map((w) => (
            <div key={w.id} className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-slate-900 dark:text-white">{w.name}</h3>
                <StatusBadge status={w.status} />
              </div>
              <div className="space-y-2 text-sm">
                <p className="text-slate-500">Entity Type: <span className="text-slate-900 dark:text-white">{w.entity_type}</span></p>
                <p className="text-slate-500">Steps: <span className="text-slate-900 dark:text-white">{w.steps?.length ?? 0}</span></p>
                <p className="text-slate-500">Current Step: <span className="text-slate-900 dark:text-white">{w.current_step}</span></p>
                {w.description && <p className="text-xs text-slate-500 mt-2">{w.description}</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Workflow">
        <form onSubmit={handleCreate} className="space-y-4">
          <FormField label="Name" required>
            <input type="text" value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="Workflow name" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
          </FormField>
          <FormField label="Entity Type" required>
            <input type="text" value={formEntityType} onChange={(e) => setFormEntityType(e.target.value)} placeholder="e.g. question" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
          </FormField>
          <FormField label="Description">
            <textarea rows={3} value={formDescription} onChange={(e) => setFormDescription(e.target.value)} placeholder="Optional description" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
          </FormField>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition">Cancel</button>
            <button type="submit" className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition">Create</button>
          </div>
        </form>
      </Modal>
    </ContentLayout>
  )
}
