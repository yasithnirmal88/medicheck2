import React, { useState } from 'react'
import { Users, Shield, CheckCircle, XCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { ContentLayout, Tabs, StatusBadge, EmptyState, TableSkeleton, Modal, DataTable } from '../components/ContentLayout'
import { useUsers, useRoles, useUpdateUserRoles } from '../hooks/useCmsQueries'
import { cmsApi } from '../api/cmsApi'
import type { UserProfile, UserRole } from '../types'

const userTabs = [
  { id: 'users', label: 'Users' },
  { id: 'roles', label: 'Roles' },
]

export const UsersRolesPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('users')
  const [editingUser, setEditingUser] = useState<UserProfile | null>(null)
  const [selectedRoles, setSelectedRoles] = useState<string[]>([])

  const { data: usersData, isLoading: usersLoading } = useUsers()
  const { data: roles, isLoading: rolesLoading } = useRoles()
  const updateRoles = useUpdateUserRoles()

  const users = usersData?.items ?? []

  const userColumns = [
    { key: 'full_name', header: 'Name', render: (u: UserProfile) => <span className="font-medium text-slate-900 dark:text-white">{u.full_name}</span> },
    { key: 'email', header: 'Email', render: (u: UserProfile) => <span className="text-sm">{u.email}</span> },
    { key: 'roles', header: 'Roles', render: (u: UserProfile) => (
      <div className="flex flex-wrap gap-1">
        {u.roles?.map((r) => <StatusBadge key={r} status={r} />)}
        {!u.roles?.length && <span className="text-xs text-slate-400">None</span>}
      </div>
    )},
    { key: 'is_active', header: 'Status', render: (u: UserProfile) => u.is_active ? <span className="flex items-center gap-1 text-emerald-600 text-xs"><CheckCircle className="w-3.5 h-3.5" /> Active</span> : <span className="flex items-center gap-1 text-slate-400 text-xs"><XCircle className="w-3.5 h-3.5" /> Inactive</span> },
    { key: 'actions', header: 'Actions', render: (u: UserProfile) => (
      <div className="flex gap-2">
        <button onClick={() => { setEditingUser(u); setSelectedRoles(u.roles ?? []) }} className="px-2 py-1 text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white rounded transition">Edit Roles</button>
        <button onClick={() => handleToggleActive(u)} className="px-2 py-1 text-xs font-medium bg-slate-600 hover:bg-slate-700 text-white rounded transition">{u.is_active ? 'Deactivate' : 'Activate'}</button>
      </div>
    )},
  ]

  const roleColumns = [
    { key: 'name', header: 'Name', render: (r: UserRole) => <span className="font-medium text-slate-900 dark:text-white">{r.name}</span> },
    { key: 'code', header: 'Code', render: (r: UserRole) => <span className="font-mono text-xs">{r.code}</span> },
    { key: 'description', header: 'Description', render: (r: UserRole) => <span className="text-sm text-slate-500">{r.description || '-'}</span> },
    { key: 'hierarchy_level', header: 'Level', render: (r: UserRole) => <span className="text-sm">{r.hierarchy_level}</span> },
    { key: 'is_active', header: 'Status', render: (r: UserRole) => r.is_active ? <span className="flex items-center gap-1 text-emerald-600 text-xs"><CheckCircle className="w-3.5 h-3.5" /> Active</span> : <span className="flex items-center gap-1 text-slate-400 text-xs"><XCircle className="w-3.5 h-3.5" /> Inactive</span> },
  ]

  const handleToggleActive = async (u: UserProfile) => {
    try {
      await cmsApi.users.toggleActive(u.id)
      toast.success(`User ${u.is_active ? 'deactivated' : 'activated'}`)
    } catch { toast.error('Failed to toggle user status') }
  }

  const handleSaveRoles = async () => {
    if (!editingUser) return
    try {
      await updateRoles.mutateAsync({ userId: editingUser.id, roles: selectedRoles })
      setEditingUser(null)
    } catch { toast.error('Failed to update roles') }
  }

  return (
    <ContentLayout title="Users & Roles" description="Manage user profiles and role assignments">
      <Tabs tabs={userTabs} active={activeTab} onChange={setActiveTab} />

      {activeTab === 'users' && (
        <div className="mt-6">
          <DataTable
            columns={userColumns}
            data={users}
            keyExtractor={(u: UserProfile) => u.id}
            loading={usersLoading}
            emptyMessage="No users found"
          />
        </div>
      )}

      {activeTab === 'roles' && (
        <div className="mt-6">
          <DataTable
            columns={roleColumns}
            data={roles ?? []}
            keyExtractor={(r: UserRole) => r.id}
            loading={rolesLoading}
            emptyMessage="No roles defined"
          />
        </div>
      )}

      <Modal open={!!editingUser} onClose={() => setEditingUser(null)} title={`Edit Roles — ${editingUser?.full_name ?? ''}`}>
        <div className="space-y-3">
          {roles?.map((role) => (
            <label key={role.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedRoles.includes(role.code)}
                onChange={(e) => {
                  if (e.target.checked) setSelectedRoles([...selectedRoles, role.code])
                  else setSelectedRoles(selectedRoles.filter((r) => r !== role.code))
                }}
                className="rounded border-slate-300 dark:border-slate-700"
              />
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-white">{role.name}</p>
                <p className="text-xs text-slate-500">{role.description || role.code}</p>
              </div>
            </label>
          ))}
          <div className="flex justify-end gap-3 pt-2">
            <button onClick={() => setEditingUser(null)} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition">Cancel</button>
            <button onClick={handleSaveRoles} disabled={updateRoles.isPending} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition">Save</button>
          </div>
        </div>
      </Modal>
    </ContentLayout>
  )
}
