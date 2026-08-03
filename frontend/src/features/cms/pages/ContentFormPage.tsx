import React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { PageHeader, FormSection, FormField } from '../components/ContentLayout'
import { cn } from '@/lib/utils'
import { Save, X } from 'lucide-react'

interface FieldDefinition {
  name: string
  label: string
  type: 'text' | 'textarea' | 'select' | 'number' | 'boolean' | 'json'
  required?: boolean
  options?: { value: string; label: string }[]
}

interface ContentFormPageProps {
  entityType: string
  title: string
  initialData: Record<string, unknown> | null
  fields: FieldDefinition[]
  onSave: (data: Record<string, unknown>) => Promise<void>
  onCancel: () => void
  loading: boolean
}

export const ContentFormPage: React.FC<ContentFormPageProps> = ({
  entityType, title, initialData, fields, onSave, onCancel, loading,
}) => {
  const fieldEntries = fields.map((f) => [f.name, f.required ? z.string().min(1, `${f.label} is required`) : z.string().optional()] as const)
  const schema = z.object(Object.fromEntries(fieldEntries))

  type FormValues = z.infer<typeof schema>

  const defaultValues = Object.fromEntries(
    fields.map((f) => [f.name, initialData?.[f.name] ?? '']),
  ) as FormValues

  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  })

  const onSubmit = async (data: FormValues) => {
    await onSave(data as unknown as Record<string, unknown>)
  }

  return (
    <div className="p-6">
      <PageHeader
        title={title}
        subtitle={initialData ? `Editing existing ${entityType.replace(/_/g, ' ')}` : `Creating new ${entityType.replace(/_/g, ' ')}`}
        onBack={onCancel}
        actions={
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onCancel}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition"
            >
              <X className="w-4 h-4" />
              Cancel
            </button>
            <button
              type="submit"
              form="cms-form"
              disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition disabled:opacity-50"
            >
              {loading && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              <Save className="w-4 h-4" />
              Save
            </button>
          </div>
        }
      />

      <form id="cms-form" onSubmit={handleSubmit(onSubmit)}>
        <FormSection title="Details" description={`Fill in the details for this ${entityType.replace(/_/g, ' ')}`}>
          {fields.map((field) => (
            <FormField key={field.name} label={field.label} required={field.required} error={errors[field.name as keyof typeof errors]?.message as string | undefined}>
              {field.type === 'textarea' || field.type === 'json' ? (
                <textarea
                  {...register(field.name)}
                  rows={field.type === 'json' ? 8 : 4}
                  className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none font-mono"
                  placeholder={field.type === 'json' ? '{\n  "key": "value"\n}' : ''}
                />
              ) : field.type === 'select' ? (
                <select
                  {...register(field.name)}
                  className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                >
                  <option value="">Select {field.label}...</option>
                  {field.options?.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              ) : field.type === 'boolean' ? (
                <input
                  type="checkbox"
                  {...register(field.name)}
                  className="w-5 h-5 rounded border-slate-300 dark:border-slate-700 text-blue-600 focus:ring-blue-500"
                />
              ) : field.type === 'number' ? (
                <input
                  type="number"
                  {...register(field.name, { valueAsNumber: true })}
                  className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              ) : (
                <input
                  type="text"
                  {...register(field.name)}
                  className="w-full px-3 py-2 border rounded-lg border-slate-300 dark:border-slate-700 dark:bg-slate-800 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              )}
            </FormField>
          ))}
        </FormSection>
      </form>
    </div>
  )
}
