import React, { useState, useEffect, useRef } from 'react'
import { Network, Plus, Search, CheckCircle2, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { ContentLayout, Modal, StatusBadge, EmptyState, TableSkeleton, FormField } from '../components/ContentLayout'
import { useKnowledgeGraphs, useValidateGraph } from '../hooks/useCmsQueries'
import { cmsApi } from '../api/cmsApi'
import type { KnowledgeGraph, KnowledgeGraphNode, KnowledgeGraphEdge, GraphValidationResult, EntitySearchResult } from '../types'

interface GraphDetail extends KnowledgeGraph {
  nodes?: KnowledgeGraphNode[]
  edges?: KnowledgeGraphEdge[]
}

export const KnowledgeGraphEditorPage: React.FC = () => {
  const [selectedGraphId, setSelectedGraphId] = useState<string | null>(null)
  const [showAddNode, setShowAddNode] = useState(false)
  const [showAddEdge, setShowAddEdge] = useState(false)
  const [showValidation, setShowValidation] = useState(false)
  const [validationResult, setValidationResult] = useState<GraphValidationResult | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<EntitySearchResult[]>([])
  const [graphDetails, setGraphDetails] = useState<{ nodes: KnowledgeGraphNode[]; edges: KnowledgeGraphEdge[] } | null>(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  const { data: graphs, isLoading: graphsLoading } = useKnowledgeGraphs()
  const validateMutation = useValidateGraph(selectedGraphId ?? '')

  const selectedGraph = graphs?.find((g) => g.id === selectedGraphId)

  useEffect(() => {
    if (selectedGraphId) {
      setDetailsLoading(true)
      Promise.all([
        cmsApi.knowledgeGraph.getGraph(selectedGraphId) as Promise<GraphDetail>,
      ]).then(([detail]) => {
        setGraphDetails({ nodes: detail.nodes ?? [], edges: detail.edges ?? [] })
      }).catch(() => toast.error('Failed to load graph details')).finally(() => setDetailsLoading(false))
    } else {
      setGraphDetails(null)
    }
  }, [selectedGraphId])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!searchQuery) { setSearchResults([]); return }
    debounceRef.current = setTimeout(() => {
      cmsApi.knowledgeGraph.searchEntities(searchQuery).then(setSearchResults).catch(() => {})
    }, 300)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [searchQuery])

  const handleValidate = async () => {
    if (!selectedGraphId) { toast.error('Select a graph first'); return }
    try {
      const result = await validateMutation.mutateAsync()
      setValidationResult(result)
      setShowValidation(true)
    } catch {
      toast.error('Validation failed')
    }
  }

  const [nodeForm, setNodeForm] = useState({ entity_type: '', entity_id: '', label: '' })
  const [edgeForm, setEdgeForm] = useState({ source_node_id: '', target_node_id: '', relationship_type: '' })

  const handleAddNode = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!nodeForm.entity_type || !nodeForm.label) { toast.error('Entity type and label are required'); return }
    try {
      await cmsApi.knowledgeGraph.addNode(selectedGraphId!, { entity_type: nodeForm.entity_type, entity_id: nodeForm.entity_id, label: nodeForm.label })
      toast.success('Node added')
      setShowAddNode(false)
      setNodeForm({ entity_type: '', entity_id: '', label: '' })
    } catch { toast.error('Failed to add node') }
  }

  const handleAddEdge = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!edgeForm.source_node_id || !edgeForm.target_node_id || !edgeForm.relationship_type) { toast.error('All fields are required'); return }
    try {
      await cmsApi.knowledgeGraph.addEdge(selectedGraphId!, { source_node_id: edgeForm.source_node_id, target_node_id: edgeForm.target_node_id, relationship_type: edgeForm.relationship_type })
      toast.success('Edge added')
      setShowAddEdge(false)
      setEdgeForm({ source_node_id: '', target_node_id: '', relationship_type: '' })
    } catch { toast.error('Failed to add edge') }
  }

  return (
    <ContentLayout
      title="Knowledge Graph Editor"
      description="Manage entity relationships and graph topology"
      actions={
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search entities..."
              className="pl-8 pr-3 py-1.5 text-sm border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 outline-none w-48"
            />
          </div>
          <select
            value={selectedGraphId ?? ''}
            onChange={(e) => setSelectedGraphId(e.target.value || null)}
            className="px-3 py-1.5 text-sm border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-slate-900 dark:text-white outline-none"
          >
            <option value="">Select graph...</option>
            {graphs?.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
          </select>
          <button onClick={() => setShowAddNode(true)} disabled={!selectedGraphId} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium rounded-lg flex items-center gap-1.5 transition">
            <Plus className="w-3.5 h-3.5" /> Add Node
          </button>
          <button onClick={() => setShowAddEdge(true)} disabled={!selectedGraphId} className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-medium rounded-lg flex items-center gap-1.5 transition">
            <Plus className="w-3.5 h-3.5" /> Add Edge
          </button>
          <button onClick={handleValidate} disabled={!selectedGraphId || validateMutation.isPending} className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-medium rounded-lg flex items-center gap-1.5 transition">
            <CheckCircle2 className="w-3.5 h-3.5" /> Validate
          </button>
        </div>
      }
    >
      {searchQuery && searchResults.length > 0 && (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
          <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-2">Search Results</h4>
          <div className="space-y-1">
            {searchResults.map((sr) => (
              <div key={sr.id} className="text-sm text-slate-700 dark:text-slate-300">
                <span className="font-mono text-xs text-slate-500">{sr.entity_type}</span> {sr.label} ({sr.id})
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-4">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
            <Network className="w-4 h-4 text-purple-600" /> Graphs
          </h3>
          {graphsLoading ? (
            <TableSkeleton />
          ) : !graphs?.length ? (
            <EmptyState title="No graphs" />
          ) : (
            <div className="space-y-2">
              {graphs.map((g) => (
                <div
                  key={g.id}
                  onClick={() => setSelectedGraphId(g.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition ${
                    selectedGraphId === g.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-slate-200 dark:border-slate-800 hover:border-slate-300'
                  }`}
                >
                  <p className="text-sm font-medium text-slate-900 dark:text-white">{g.name}</p>
                  <StatusBadge status={g.status} />
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-3 space-y-6">
          {selectedGraph && graphDetails ? (
            <>
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">{selectedGraph.name}</h3>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                  <div><span className="text-slate-500">Description:</span><p className="text-slate-900 dark:text-white">{selectedGraph.description || '-'}</p></div>
                  <div><span className="text-slate-500">Status:</span><StatusBadge status={selectedGraph.status} /></div>
                  <div><span className="text-slate-500">Nodes:</span><p className="text-slate-900 dark:text-white">{graphDetails.nodes.length}</p></div>
                  <div><span className="text-slate-500">Edges:</span><p className="text-slate-900 dark:text-white">{graphDetails.edges.length}</p></div>
                </div>
              </div>

              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
                <h4 className="font-semibold text-slate-900 dark:text-white mb-3">Nodes</h4>
                {detailsLoading ? <TableSkeleton /> : !graphDetails.nodes.length ? <EmptyState title="No nodes" /> : (
                  <div className="space-y-2">
                    {graphDetails.nodes.map((node) => (
                      <div key={node.id} className="flex items-center gap-3 p-3 border border-slate-200 dark:border-slate-800 rounded-lg">
                        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: node.color || '#3b82f6' }} />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-900 dark:text-white">{node.label}</p>
                          <p className="text-xs text-slate-500">{node.entity_type} — {node.entity_id}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
                <h4 className="font-semibold text-slate-900 dark:text-white mb-3">Edges</h4>
                {detailsLoading ? <TableSkeleton /> : !graphDetails.edges.length ? <EmptyState title="No edges" /> : (
                  <div className="space-y-2">
                    {graphDetails.edges.map((edge) => (
                      <div key={edge.id} className="flex items-center gap-3 p-3 border border-slate-200 dark:border-slate-800 rounded-lg">
                        <div className="flex-1">
                          <p className="text-sm text-slate-900 dark:text-white">
                            <span className="font-mono text-xs">{edge.source_node_id}</span> → <span className="font-mono text-xs">{edge.target_node_id}</span>
                          </p>
                          <p className="text-xs text-slate-500">{edge.relationship_type} | weight: {edge.weight}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5">
              <EmptyState title="Select a Graph" description="Choose a knowledge graph from the left panel" icon={<Network className="w-8 h-8" />} />
            </div>
          )}
        </div>
      </div>

      <Modal open={showAddNode} onClose={() => setShowAddNode(false)} title="Add Node">
        <form onSubmit={handleAddNode} className="space-y-4">
          <FormField label="Entity Type" required>
            <input type="text" value={nodeForm.entity_type} onChange={(e) => setNodeForm({ ...nodeForm, entity_type: e.target.value })} placeholder="e.g. question" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
          </FormField>
          <FormField label="Entity ID">
            <input type="text" value={nodeForm.entity_id} onChange={(e) => setNodeForm({ ...nodeForm, entity_id: e.target.value })} placeholder="Entity ID" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
          </FormField>
          <FormField label="Label" required>
            <input type="text" value={nodeForm.label} onChange={(e) => setNodeForm({ ...nodeForm, label: e.target.value })} placeholder="Display label" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
          </FormField>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowAddNode(false)} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition">Cancel</button>
            <button type="submit" className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition">Add</button>
          </div>
        </form>
      </Modal>

      <Modal open={showAddEdge} onClose={() => setShowAddEdge(false)} title="Add Edge">
        <form onSubmit={handleAddEdge} className="space-y-4">
          <FormField label="Source Node ID" required>
            <input type="text" value={edgeForm.source_node_id} onChange={(e) => setEdgeForm({ ...edgeForm, source_node_id: e.target.value })} placeholder="Source node ID" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
          </FormField>
          <FormField label="Target Node ID" required>
            <input type="text" value={edgeForm.target_node_id} onChange={(e) => setEdgeForm({ ...edgeForm, target_node_id: e.target.value })} placeholder="Target node ID" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
          </FormField>
          <FormField label="Relationship Type" required>
            <input type="text" value={edgeForm.relationship_type} onChange={(e) => setEdgeForm({ ...edgeForm, relationship_type: e.target.value })} placeholder="e.g. associated_with" className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white" />
          </FormField>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowAddEdge(false)} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition">Cancel</button>
            <button type="submit" className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition">Add</button>
          </div>
        </form>
      </Modal>

      <Modal open={showValidation} onClose={() => setShowValidation(false)} title="Validation Results" size="lg">
        {validationResult && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              {validationResult.is_valid ? (
                <span className="flex items-center gap-1 text-emerald-600 font-medium"><CheckCircle2 className="w-5 h-5" /> Valid</span>
              ) : (
                <span className="flex items-center gap-1 text-red-600 font-medium"><AlertCircle className="w-5 h-5" /> Issues Found</span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg"><span className="text-slate-500">Total Nodes</span><p className="font-semibold">{validationResult.total_nodes}</p></div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg"><span className="text-slate-500">Total Edges</span><p className="font-semibold">{validationResult.total_edges}</p></div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg"><span className="text-slate-500">Orphan Nodes</span><p className="font-semibold">{validationResult.orphan_count}</p></div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg"><span className="text-slate-500">Cycles</span><p className="font-semibold">{validationResult.cycle_count}</p></div>
            </div>
            {validationResult.issues.length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-slate-900 dark:text-white mb-2">Issues</h5>
                <ul className="space-y-1">
                  {validationResult.issues.map((issue, i) => <li key={i} className="text-sm text-red-600 flex items-start gap-1"><AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />{issue}</li>)}
                </ul>
              </div>
            )}
            {validationResult.orphan_nodes.length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-slate-900 dark:text-white mb-2">Orphan Nodes</h5>
                <div className="flex flex-wrap gap-1">{validationResult.orphan_nodes.map((n) => <span key={n} className="px-2 py-0.5 text-xs bg-yellow-100 dark:bg-yellow-900/30 rounded">{n}</span>)}</div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </ContentLayout>
  )
}
