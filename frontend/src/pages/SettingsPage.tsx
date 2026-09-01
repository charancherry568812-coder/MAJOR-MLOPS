import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import {
  Settings, Save, Sliders, Shield, Activity, Target,
  RefreshCw, CheckCircle
} from 'lucide-react'
import { useToastStore } from '../store/toastStore'

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()

  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')

  const { data: settingsData, isLoading, refetch } = useQuery({
    queryKey: ['settings'],
    queryFn: () => api.get('/settings').then(r => r.data.data),
  })

  const updateMutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) =>
      api.put(`/settings/${key}?value=${encodeURIComponent(value)}`),
    onSuccess: () => {
      addToast('success', 'Setting updated successfully')
      setEditingKey(null)
      refetch()
    },
    onError: (err: any) => addToast('error', err.response?.data?.detail || 'Failed to update setting'),
  })

  const settings: any[] = settingsData || []

  // Group settings by category
  const categories = Array.from(new Set(settings.map(s => s.category || 'general')))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">System Governance & Platform Parameters</h1>
          <p className="text-sm text-slate-500 mt-1">
            Fine-tune federated learning convergence criteria, MLOps drift alert thresholds, risk bounds, and security lockout policies.
          </p>
        </div>
      </div>

      {/* Settings Categories */}
      <div className="space-y-6">
        {categories.map(cat => {
          const catSettings = settings.filter(s => (s.category || 'general') === cat)
          return (
            <div key={cat} className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
              <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
                <Sliders size={16} className="text-blue-600" />
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
                  {cat.toUpperCase()} GOVERNANCE POLICIES
                </h2>
              </div>

              <div className="divide-y divide-slate-100">
                {catSettings.map(s => (
                  <div key={s.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50/50">
                    <div className="max-w-xl">
                      <p className="font-mono font-semibold text-sm text-slate-800">{s.key}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{s.description}</p>
                    </div>

                    <div className="flex items-center gap-3">
                      {editingKey === s.key ? (
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            value={editValue}
                            onChange={e => setEditValue(e.target.value)}
                            className="px-3 py-1.5 text-sm border rounded-xl w-32 font-mono"
                          />
                          <button
                            onClick={() => updateMutation.mutate({ key: s.key, value: editValue })}
                            disabled={updateMutation.isPending}
                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingKey(null)}
                            className="px-3 py-1.5 border rounded-xl text-xs text-slate-600 hover:bg-slate-100"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-3">
                          <span className="px-3 py-1 bg-slate-100 text-slate-800 font-mono text-sm rounded-lg font-semibold border border-slate-200">
                            {s.value}
                          </span>
                          <button
                            onClick={() => { setEditingKey(s.key); setEditValue(s.value) }}
                            className="px-3 py-1 text-xs font-medium text-blue-600 hover:text-blue-800 border border-blue-200 hover:bg-blue-50 rounded-lg"
                          >
                            Edit
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
