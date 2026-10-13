import { useMemo, useState } from 'react'
import { Navigate, useLocation, useNavigate, useParams } from 'react-router-dom'
import { ContentFormPage } from './ContentFormPage'
import { ContentLayout, TableSkeleton } from '../components/ContentLayout'
import {
  useContentItem,
  useCreateContent,
  useUpdateContent,
} from '../hooks/useCmsQueries'
import { ENTITY_TYPES, type EntityType } from '../types'
import { getContentListPath } from './contentRoutes'

const AUDIT_FIELDS = new Set([
  'id',
  'created_at',
  'updated_at',
  'deleted_at',
  'created_by',
  'updated_by',
  'version',
])

export default function ContentEditorRoute() {
  const { entityType: routeEntityType, entityId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [formError, setFormError] = useState<string | null>(null)
  const isEntityType = ENTITY_TYPES.some((entityType) => entityType === routeEntityType)
  const entityType = isEntityType ? routeEntityType as EntityType : undefined
  const returnTo = (location.state as { returnTo?: unknown } | null)?.returnTo
  const listPath = entityType
    ? typeof returnTo === 'string' && returnTo.startsWith('/cms/')
      ? returnTo
      : getContentListPath(entityType)
    : '/cms'
  const itemQuery = useContentItem<Record<string, unknown>>(entityType ?? 'question', entityId)
  const createMutation = useCreateContent<Record<string, unknown>>(entityType ?? 'question')
  const updateMutation = useUpdateContent<Record<string, unknown>>(entityType ?? 'question')

  const initialData = useMemo(() => {
    if (!entityType || !entityId || !itemQuery.data) return { data: '{}' }
    const editable = Object.fromEntries(
      Object.entries(itemQuery.data).filter(([key]) => !AUDIT_FIELDS.has(key)),
    )
    if (entityType === 'question') delete editable.options
    return { data: JSON.stringify(editable, null, 2) }
  }, [entityId, entityType, itemQuery.data])

  if (!entityType) return <Navigate to="/not-found" replace />

  if (entityId && itemQuery.isLoading) {
    return (
      <ContentLayout title="Loading content">
        <TableSkeleton />
      </ContentLayout>
    )
  }

  if (entityId && (!itemQuery.data || itemQuery.isError)) {
    return (
      <ContentLayout title="Content unavailable" description="This item could not be loaded.">
        <button
          type="button"
          onClick={() => navigate(listPath)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white"
        >
          Back to list
        </button>
      </ContentLayout>
    )
  }

  const save = async (values: Record<string, unknown>) => {
    setFormError(null)
    let data: unknown
    try {
      data = JSON.parse(String(values.data ?? ''))
    } catch {
      setFormError('Enter valid JSON before saving.')
      return
    }
    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      setFormError('Content must be a JSON object.')
      return
    }

    const editable = Object.fromEntries(
      Object.entries(data).filter(([key]) => !AUDIT_FIELDS.has(key)),
    ) as Record<string, unknown>
    try {
      if (entityId) {
        await updateMutation.mutateAsync({ id: entityId, data: editable })
      } else {
        await createMutation.mutateAsync(editable)
      }
      navigate(listPath)
    } catch {
      setFormError('The content could not be saved. Review the fields and try again.')
    }
  }

  return (
    <>
      {formError && (
        <p role="alert" className="mx-6 mt-4 text-sm text-red-600 dark:text-red-400">
          {formError}
        </p>
      )}
      <ContentFormPage
        entityType={entityType}
        title={`${entityId ? 'Edit' : 'Create'} ${entityType.replace(/_/g, ' ')}`}
        initialData={initialData}
        fields={[{ name: 'data', label: 'Content JSON', type: 'json', required: true }]}
        onSave={save}
        onCancel={() => navigate(listPath)}
        loading={createMutation.isPending || updateMutation.isPending}
      />
    </>
  )
}
