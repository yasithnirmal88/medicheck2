import React, { useState, useEffect } from 'react'
import { SearchInput, TableSkeleton, EmptyState } from '../components/ContentLayout'
import { cmsApi } from '../api/cmsApi'
import { Search, FileText } from 'lucide-react'
import type { EntitySearchResult } from '../types'

export const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<EntitySearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setSearched(false)
      return
    }
    const timer = setTimeout(async () => {
      setLoading(true)
      setSearched(true)
      try {
        const data = await cmsApi.search(query)
        setResults(Array.isArray(data) ? data : [])
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  const grouped = results.reduce<Record<string, EntitySearchResult[]>>((acc, r) => {
    const group = r.entity_type || 'other'
    if (!acc[group]) acc[group] = []
    acc[group].push(r)
    return acc
  }, {})

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Global CMS Search</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Search across all content entities in the CMS</p>
      </div>

      <div className="max-w-2xl">
        <SearchInput value={query} onChange={setQuery} placeholder="Search by code, name, or keyword..." />
      </div>

      {loading && <TableSkeleton rows={4} />}

      {!loading && searched && results.length === 0 && (
        <EmptyState
          title="No results found"
          description={`No content matches "${query}". Try a different search term.`}
          icon={<Search className="w-12 h-12 text-slate-300 dark:text-slate-600" />}
        />
      )}

      {!loading && Object.keys(grouped).length > 0 && (
        <div className="space-y-6">
          {Object.entries(grouped).map(([entityType, items]) => (
            <div key={entityType}>
              <div className="flex items-center gap-2 mb-3">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white capitalize">
                  {entityType.replace(/_/g, ' ')}
                </h2>
                <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                  {items.length}
                </span>
              </div>
              <div className="grid gap-2">
                {items.map((item) => (
                  <div
                    key={`${item.entity_type}-${item.id}`}
                    onClick={() => {
                      const path = `/cms/content/${item.entity_type}/${item.id}`
                      window.location.href = path
                    }}
                    className="flex items-center gap-3 p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition cursor-pointer"
                  >
                    <FileText className="w-5 h-5 text-slate-400 dark:text-slate-500 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{item.label}</p>
                      <p className="text-xs text-slate-400 dark:text-slate-500 font-mono truncate">{item.id}</p>
                    </div>
                    <span className="text-xs font-medium text-slate-400 dark:text-slate-500 capitalize shrink-0">
                      {item.entity_type?.replace(/_/g, ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && !searched && (
        <EmptyState
          title="Search across all entities"
          description="Type a query above to search across questions, diseases, symptoms, and more."
          icon={<Search className="w-12 h-12 text-slate-300 dark:text-slate-600" />}
        />
      )}
    </div>
  )
}
