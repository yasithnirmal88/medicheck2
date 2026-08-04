import React from 'react'
import { ContentLayout, FormSection, TableSkeleton } from '../components/ContentLayout'
import { useContentList } from '../hooks/useCmsQueries'
import { cn } from '@/lib/utils'
import { Tag, Stethoscope, AlertTriangle } from 'lucide-react'
import type { MedicalSpecialty, MedicalTag, RiskCategory } from '../types'

export const SettingsPage: React.FC = () => {
  const { data: specialtiesData, isLoading: loadingSpecialties } = useContentList<MedicalSpecialty>('specialty', { limit: 100 })
  const { data: tagsData, isLoading: loadingTags } = useContentList<MedicalTag>('tag', { limit: 100 })
  const { data: riskCategoriesData, isLoading: loadingRisk } = useContentList<RiskCategory>('risk_category', { limit: 100 })

  return (
    <ContentLayout
      title="CMS Settings"
      description="Configure medical specialties, tags, and risk categories"
    >
      <FormSection title="General Settings" description="Platform-level CMS configuration options">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Default Page Size</p>
            <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">20</p>
          </div>
          <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Content Versioning</p>
            <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">Enabled</p>
          </div>
          <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Audit Logging</p>
            <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">Active</p>
          </div>
        </div>
      </FormSection>

      <FormSection
        title="Medical Specialties"
        description={`${specialtiesData?.total ?? 0} specialties configured`}
      >
        {loadingSpecialties ? (
          <TableSkeleton rows={3} />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {specialtiesData?.items.map((s) => (
              <div key={s.id} className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                  <Stethoscope className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{s.name}</p>
                  <p className="text-xs text-slate-400 dark:text-slate-500 font-mono">{s.code}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </FormSection>

      <FormSection
        title="Medical Tags"
        description={`${tagsData?.total ?? 0} tags configured`}
      >
        {loadingTags ? (
          <TableSkeleton rows={3} />
        ) : (
          <div className="flex flex-wrap gap-2">
            {tagsData?.items.map((t) => (
              <div
                key={t.id}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50"
              >
                <Tag className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t.name}</span>
                {t.color_hex && (
                  <span
                    className="w-3 h-3 rounded-full inline-block"
                    style={{ backgroundColor: t.color_hex }}
                  />
                )}
              </div>
            ))}
            {tagsData?.items.length === 0 && (
              <p className="text-sm text-slate-500 dark:text-slate-400">No tags configured yet.</p>
            )}
          </div>
        )}
      </FormSection>

      <FormSection
        title="Risk Categories"
        description={`${riskCategoriesData?.total ?? 0} categories configured`}
      >
        {loadingRisk ? (
          <TableSkeleton rows={3} />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {riskCategoriesData?.items.map((rc) => (
              <div key={rc.id} className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className={cn(
                  'p-2 rounded-lg',
                  rc.color_hex ? '' : 'bg-amber-50 dark:bg-amber-900/20',
                )}
                  style={rc.color_hex ? { backgroundColor: `${rc.color_hex}20` } : undefined}
                >
                  <AlertTriangle className="w-4 h-4" style={{ color: rc.color_hex || '#d97706' }} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{rc.name}</p>
                  <p className="text-xs text-slate-400 dark:text-slate-500">
                    {rc.min_score ?? '—'} – {rc.max_score ?? '—'}
                  </p>
                </div>
                {rc.color_hex && (
                  <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: rc.color_hex }} />
                )}
              </div>
            ))}
          </div>
        )}
      </FormSection>
    </ContentLayout>
  )
}
