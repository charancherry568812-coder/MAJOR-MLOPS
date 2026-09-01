import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import {
  Users, UserPlus, Shield, Search, Key, CheckCircle,
  XCircle, MoreVertical, Edit2, Lock, Info
} from 'lucide-react'
import { useToastStore } from '../store/toastStore'

export default function UsersPage() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()

  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createForm, setCreateForm] = useState({
    email: '',
    password: '',
    full_name: '',
    role_id: '',
  })

  // Fetch Users
  const { data: usersData, refetch } = useQuery({
    queryKey: ['users', search, roleFilter],
    queryFn: () => {
      let url = '/users?page_size=50'
      if (search) url += `&search=${search}`
      if (roleFilter) url += `&role=${roleFilter}`
      return api.get(url).then(r => r.data.data)
    },
  })

  // Fetch Roles
  const { data: rolesData } = useQuery({
    queryKey: ['roles'],
    queryFn: () => api.get('/users/roles').then(r => r.data.data),
  })

  // Create User Mutation
  const createMutation = useMutation({
    mutationFn: (payload: any) =>
      api.post(`/users?email=${encodeURIComponent(payload.email)}&password=${encodeURIComponent(payload.password)}&full_name=${encodeURIComponent(payload.full_name)}&role_id=${payload.role_id}`),
    onSuccess: () => {
      addToast('success', 'User account created successfully')
      setShowCreateModal(false)
      setCreateForm({ email: '', password: '', full_name: '', role_id: '' })
      refetch()
    },
    onError: (err: any) => addToast('error', err.response?.data?.detail || 'Failed to create user'),
  })

  // Toggle User Active Status Mutation
  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      api.put(`/users/${id}?is_active=${is_active}`),
    onSuccess: () => {
      addToast('success', 'User status updated')
      refetch()
    },
    onError: () => addToast('error', 'Status update failed'),
  })

  const users = usersData?.items || []
  const roles = rolesData || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">User Management & Access Control</h1>
          <p className="text-sm text-slate-500 mt-1">
            Configure role-based access permissions, provision bank officer logins, and inspect user activity.
          </p>
        </div>
        <button
          onClick={() => {
            if (roles.length > 0) setCreateForm(f => ({ ...f, role_id: roles[0].id }))
            setShowCreateModal(true)
          }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold transition-all shadow-sm"
        >
          <UserPlus size={16} />
          Create User
        </button>
      </div>

      {/* Demo Credentials Reference Callout */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/60 p-4 rounded-2xl">
        <div className="flex items-start gap-3">
          <Info className="text-blue-600 mt-0.5 flex-shrink-0" size={18} />
          <div className="text-xs text-blue-900 space-y-1">
            <p className="font-bold">Default Consortium Demo Accounts (All seeded and active):</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 pt-1 font-mono text-[11px]">
              <div>• <strong>SUPER_ADMIN:</strong> admin@fedbank.com / Admin@123</div>
              <div>• <strong>BANK_ADMIN:</strong> banka.admin@fedbank.com / BankA@123</div>
              <div>• <strong>DATA_SCIENTIST:</strong> data.scientist@fedbank.com / DataSci@123</div>
              <div>• <strong>ML_ENGINEER:</strong> ml.engineer@fedbank.com / MLEng@123</div>
              <div>• <strong>AUDITOR:</strong> auditor@fedbank.com / Auditor@123</div>
              <div>• <strong>VIEWER:</strong> viewer@fedbank.com / Viewer@123</div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap gap-3 items-center flex-1">
          <div className="relative min-w-[240px]">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-sm border rounded-xl"
            />
          </div>

          <select
            value={roleFilter}
            onChange={e => setRoleFilter(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded-xl text-slate-700 bg-white"
          >
            <option value="">All Roles</option>
            {roles.map((r: any) => (
              <option key={r.id} value={r.name}>{r.name}</option>
            ))}
          </select>
        </div>

        <span className="text-xs text-slate-400 font-medium">Total active users: {users.length}</span>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold text-slate-500 border-b border-slate-100">
              <tr>
                <th className="p-4">User</th>
                <th className="p-4">Role</th>
                <th className="p-4">Status</th>
                <th className="p-4">Created Date</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u: any) => (
                <tr key={u.id} className="hover:bg-slate-50/50">
                  <td className="p-4">
                    <p className="font-semibold text-slate-800">{u.full_name}</p>
                    <p className="text-xs text-slate-500 font-mono">{u.email}</p>
                  </td>
                  <td className="p-4">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                      {u.role?.name}
                    </span>
                  </td>
                  <td className="p-4">
                    {u.is_active ? (
                      <span className="flex items-center gap-1.5 text-xs text-emerald-700 font-medium">
                        <CheckCircle size={14} className="text-emerald-500" /> Active
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
                        <XCircle size={14} /> Inactive
                      </span>
                    )}
                  </td>
                  <td className="p-4 text-xs text-slate-500">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="p-4 text-right">
                    <button
                      onClick={() => toggleActiveMutation.mutate({ id: u.id, is_active: !u.is_active })}
                      className={`px-3 py-1 text-xs font-medium rounded-lg border transition-all ${
                        u.is_active ? 'text-rose-600 border-rose-200 hover:bg-rose-50' : 'text-emerald-600 border-emerald-200 hover:bg-emerald-50'
                      }`}
                    >
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* CREATE USER MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <h3 className="font-bold text-lg text-slate-800">Create Bank Officer User</h3>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-600">Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. Sarah Connor"
                  value={createForm.full_name}
                  onChange={e => setCreateForm({ ...createForm, full_name: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border rounded-xl text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-600">Email Address</label>
                <input
                  type="email"
                  placeholder="e.g. sarah@fedbank.com"
                  value={createForm.email}
                  onChange={e => setCreateForm({ ...createForm, email: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border rounded-xl text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-600">Initial Password</label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={createForm.password}
                  onChange={e => setCreateForm({ ...createForm, password: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border rounded-xl text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-600">Role</label>
                <select
                  value={createForm.role_id}
                  onChange={e => setCreateForm({ ...createForm, role_id: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border rounded-xl text-sm bg-white"
                >
                  {roles.map((r: any) => (
                    <option key={r.id} value={r.id}>{r.name} – {r.description}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 border rounded-xl text-sm font-medium hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={() => createMutation.mutate(createForm)}
                disabled={createMutation.isPending || !createForm.email || !createForm.password}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold disabled:opacity-50"
              >
                Create Account
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
