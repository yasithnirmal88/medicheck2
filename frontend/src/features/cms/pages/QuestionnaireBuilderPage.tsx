import React, { useState } from 'react'
import { Layers, Plus, ArrowUp, ArrowDown, GitFork, Link as LinkIcon } from 'lucide-react'
import toast from 'react-hot-toast'
import { ContentLayout, Tabs, Modal, StatusBadge, EmptyState, TableSkeleton, FormField } from '../components/ContentLayout'
import { useBuilderGroups, useQuestions, useReorderGroups } from '../hooks/useCmsQueries'
import { cmsApi } from '../api/cmsApi'
import type { QuestionGroupWithQuestions, Question, DependencyRule, BranchRule } from '../types'

const builderTabs = [
  { id: 'groups', label: 'Groups' },
  { id: 'dependencies', label: 'Dependencies' },
  { id: 'branch-rules', label: 'Branch Rules' },
]

export const QuestionnaireBuilderPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('groups')
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null)
  const [showCreateQuestion, setShowCreateQuestion] = useState(false)
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null)

  const { data: groups, isLoading: groupsLoading } = useBuilderGroups()
  const { data: questionsData, isLoading: questionsLoading } = useQuestions({ question_group_id: selectedGroupId ?? undefined })
  const reorderGroups = useReorderGroups()

  const selectedGroup = groups?.find((g) => g.id === selectedGroupId)
  const questions = questionsData?.items ?? []

  const [formCode, setFormCode] = useState('')
  const [formText, setFormText] = useState('')
  const [formQuestionType, setFormQuestionType] = useState('single_choice')
  const [formIsRequired, setFormIsRequired] = useState(true)

  const [dependencies, setDependencies] = useState<DependencyRule[]>([])
  const [branchRules, setBranchRules] = useState<BranchRule[]>([])
  const [depsLoading, setDepsLoading] = useState(false)
  const [branchLoading, setBranchLoading] = useState(false)

  React.useEffect(() => {
    if (activeTab === 'dependencies' && selectedQuestionId) {
      setDepsLoading(true)
      cmsApi.builder.getDependencies(selectedQuestionId).then(setDependencies).catch(() => toast.error('Failed to load dependencies')).finally(() => setDepsLoading(false))
    }
  }, [activeTab, selectedQuestionId])

  React.useEffect(() => {
    if (activeTab === 'branch-rules' && selectedQuestionId) {
      setBranchLoading(true)
      cmsApi.builder.getBranchRules(selectedQuestionId).then(setBranchRules).catch(() => toast.error('Failed to load branch rules')).finally(() => setBranchLoading(false))
    }
  }, [activeTab, selectedQuestionId])

  const handleMoveGroup = async (groupId: string, direction: 'up' | 'down') => {
    try {
      await cmsApi.builder.moveGroup(groupId, direction)
      reorderGroups.mutate(groups?.map((g) => g.id) ?? [])
      toast.success(`Group moved ${direction}`)
    } catch {
      toast.error('Failed to move group')
    }
  }

  const handleCreateQuestion = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formCode || !formText) {
      toast.error('Code and text are required')
      return
    }
    try {
      await cmsApi.questions.create({ code: formCode, text: formText, question_type: formQuestionType, is_required: formIsRequired, question_group_id: selectedGroupId })
      toast.success('Question created')
      setShowCreateQuestion(false)
      setFormCode('')
      setFormText('')
      setFormQuestionType('single_choice')
      setFormIsRequired(true)
    } catch {
      toast.error('Failed to create question')
    }
  }

  return (
    <ContentLayout title="Question Builder" description="Build and manage questionnaire groups and questions">
      <Tabs tabs={builderTabs} active={activeTab} onChange={setActiveTab} />

      {activeTab === 'groups' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-600" /> Groups
              </h3>
            </div>
            {groupsLoading ? (
              <TableSkeleton />
            ) : !groups?.length ? (
              <EmptyState title="No groups" description="No question groups found" />
            ) : (
              <div className="space-y-2">
                {groups.map((group, idx) => (
                  <div
                    key={group.id}
                    onClick={() => setSelectedGroupId(group.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition flex items-center justify-between ${
                      selectedGroupId === group.id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-slate-200 dark:border-slate-800 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <div className="flex flex-col gap-0.5 text-slate-400">
                        <button onClick={(e) => { e.stopPropagation(); handleMoveGroup(group.id, 'up') }} className="hover:text-slate-600"><ArrowUp className="w-3 h-3" /></button>
                        <button onClick={(e) => { e.stopPropagation(); handleMoveGroup(group.id, 'down') }} className="hover:text-slate-600"><ArrowDown className="w-3 h-3" /></button>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-white">{group.name}</p>
                        <p className="text-xs text-slate-500">{group.questions?.length ?? 0} questions</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-900 dark:text-white">
                {selectedGroup ? selectedGroup.name : 'Select a group'} — Questions
              </h3>
              {selectedGroupId && (
                <button
                  onClick={() => setShowCreateQuestion(true)}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg flex items-center gap-1.5 transition"
                >
                  <Plus className="w-3.5 h-3.5" /> Create Question
                </button>
              )}
            </div>
            {questionsLoading ? (
              <TableSkeleton />
            ) : !questions.length ? (
              <EmptyState title="No questions" description={selectedGroupId ? 'Create a question in this group' : 'Select a group to view questions'} />
            ) : (
              <div className="space-y-2">
                {questions.map((q) => (
                  <div
                    key={q.id}
                    onClick={() => setSelectedQuestionId(q.id)}
                    className={`p-3 rounded-lg border transition cursor-pointer ${
                      selectedQuestionId === q.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-slate-200 dark:border-slate-800 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-slate-600 dark:text-slate-400">{q.code}</span>
                      <StatusBadge status={q.question_type} />
                      <span className="text-xs text-slate-500">Priority: {q.priority}</span>
                    </div>
                    <p className="text-sm text-slate-900 dark:text-white">{q.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'dependencies' && (
        <div className="mt-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
          <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
            <LinkIcon className="w-4 h-4 text-blue-600" /> Dependencies
            {selectedQuestionId && <span className="text-sm font-normal text-slate-500">— Selected question: {selectedQuestionId}</span>}
          </h3>
          {!selectedQuestionId ? (
            <EmptyState title="Select a question" description="Click a question in the Groups tab to view its dependencies" />
          ) : depsLoading ? (
            <TableSkeleton />
          ) : !dependencies.length ? (
            <EmptyState title="No dependencies" description="This question has no dependency rules" />
          ) : (
            <div className="space-y-2">
              {dependencies.map((dep) => (
                <div key={dep.id} className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg">
                  <p className="text-sm text-slate-900 dark:text-white">
                    Depends on <span className="font-mono text-xs">{dep.depends_on_question_id}</span>
                  </p>
                  <p className="text-xs text-slate-500">Condition: {dep.condition} {dep.value && `→ ${dep.value}`} | Logic: {dep.logic_type}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'branch-rules' && (
        <div className="mt-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
          <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
            <GitFork className="w-4 h-4 text-blue-600" /> Branch Rules
            {selectedQuestionId && <span className="text-sm font-normal text-slate-500">— Selected question: {selectedQuestionId}</span>}
          </h3>
          {!selectedQuestionId ? (
            <EmptyState title="Select a question" description="Click a question in the Groups tab to view its branch rules" />
          ) : branchLoading ? (
            <TableSkeleton />
          ) : !branchRules.length ? (
            <EmptyState title="No branch rules" description="This question has no branch rules" />
          ) : (
            <div className="space-y-2">
              {branchRules.map((br) => (
                <div key={br.id} className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg">
                  <p className="text-sm text-slate-900 dark:text-white">
                    Condition: {br.condition} → Target: <span className="font-mono text-xs">{br.target_question_id}</span>
                  </p>
                  <p className="text-xs text-slate-500">Priority: {br.priority}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <Modal open={showCreateQuestion} onClose={() => setShowCreateQuestion(false)} title="Create Question">
        <form onSubmit={handleCreateQuestion} className="space-y-4">
          <FormField label="Code" required>
            <input
              type="text"
              value={formCode}
              onChange={(e) => setFormCode(e.target.value)}
              placeholder="e.g. BP_HIGH"
              className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white"
            />
          </FormField>
          <FormField label="Text" required>
            <textarea
              rows={3}
              value={formText}
              onChange={(e) => setFormText(e.target.value)}
              placeholder="Question prompt text"
              className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white"
            />
          </FormField>
          <FormField label="Question Type" required>
            <select
              value={formQuestionType}
              onChange={(e) => setFormQuestionType(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white"
            >
              <option value="single_choice">Single Choice</option>
              <option value="multiple_choice">Multiple Choice</option>
              <option value="numeric">Numeric</option>
              <option value="scale">Scale</option>
              <option value="boolean">Boolean</option>
            </select>
          </FormField>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={formIsRequired} onChange={(e) => setFormIsRequired(e.target.checked)} className="rounded border-slate-300 dark:border-slate-700" />
            Is Required
          </label>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowCreateQuestion(false)} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition">
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
