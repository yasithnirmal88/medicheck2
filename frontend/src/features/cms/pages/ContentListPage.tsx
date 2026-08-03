import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ContentLayout, DataTable, StatusBadge, SearchInput, Pagination, ConfirmAction } from '../components/ContentLayout'
import { useContentList, useDeleteContent } from '../hooks/useCmsQueries'
import { Plus, Edit2, Trash2 } from 'lucide-react'
import type { Column } from '../components/ContentLayout'
import type { EntityType } from '../types'

interface ContentListPageProps<T extends { id: string }> {
  entityType: string
  columns: Column<T>[]
  title: string
  description: string
  basePath?: string
}

export function ContentListPage<T extends { id: string }>({
  entityType, columns, title, description, basePath,
}: ContentListPageProps<T>) {
  const navigate = useNavigate()
  const [skip, setSkip] = useState(0)
  const [query, setQuery] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const limit = 20
  const path = basePath || `/cms/${entityType.replace(/_/g, '-')}`

  const { data, isLoading } = useContentList<T>(entityType as EntityType, { skip, limit, query: query || undefined })
  const deleteMutation = useDeleteContent(entityType as EntityType)

  const items = data?.items ?? []
  const total = data?.total ?? 0

  const handleDelete = () => {
    if (!deleteTarget) return
    deleteMutation.mutate(deleteTarget, { onSuccess: () => setDeleteTarget(null) })
  }

  const allColumns: Column<T>[] = [
    ...columns,
    {
      key: '_actions',
      header: 'Actions',
      render: (item: T) => (
        <div className="flex items-center gap-2">
          <button
            onClick={(e: React.MouseEvent) => { e.stopPropagation(); navigate(`${path}/${item.id}`) }}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            title="Edit"
          >
            <Edit2 className="w-4 h-4 text-slate-500 dark:text-slate-400" />
          </button>
          <button
            onClick={(e: React.MouseEvent) => { e.stopPropagation(); setDeleteTarget(item.id) }}
            className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition"
            title="Delete"
          >
            <Trash2 className="w-4 h-4 text-red-500" />
          </button>
        </div>
      ),
    },
  ]

  return (
    <ContentLayout
      title={title}
      description={description}
      actions={
        <button
          onClick={() => navigate(`${path}/new`)}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create
        </button>
      }
    >
      <SearchInput value={query} onChange={setQuery} placeholder={`Search ${title.toLowerCase()}...`} />
      <DataTable
        columns={allColumns}
        data={items}
        keyExtractor={(item: T) => item.id}
        onRowClick={(item: T) => navigate(`${path}/${item.id}`)}
        loading={isLoading}
      />
      <Pagination skip={skip} limit={limit} total={total} onChange={setSkip} />
      <ConfirmAction
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Item"
        message="Are you sure you want to delete this item? This action cannot be undone."
        confirmLabel="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </ContentLayout>
  )
}
