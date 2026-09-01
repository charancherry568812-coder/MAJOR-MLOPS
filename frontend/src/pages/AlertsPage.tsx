import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import {
  AlertTriangle, CheckCircle, ShieldAlert, Filter,
  Bell, CheckCircle2, Clock
} from 'lucide-react'
import { useToastStore } from '../store/toastStore'

export default function AlertsPage() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()
  const [severityFilter, setSeverityFilter] = useState('')

  const { data: summary } = useQuery({
    queryKey: ['alert-summary'],
    queryFn: () => api.get('/alerts/summary').then(r => r.data.data),
  })

  const { data: alertsData, refetch } = useQuery({
    queryKey: ['alerts', severityFilter],
    queryFn: () => {
      let url = '/alerts?page_size=50'
      if (severityFilter) url += `&severity=${severityFilter}`
      return api.get(url).then(r => r.data.data)
    },
  })

  const resolveMutation = useMutation({
    mutationFn: (id: string) => api.put(`/alerts/${id}/resolve`),
    onSuccess: () => {
      addToast('success', 'Alert resolved')
      refetch()
      queryClient.invalidateQueries({ queryKey: ['alert-summary'] })
    },
    onError: () => addToast('error', 'Failed to resolve alert'),
  })

  const alerts = alertsData?.items || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Operational Alerts & Notification Queue</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time threshold alerts for federated client heartbeats, model performance decay, and data drift.
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs text-slate-500 font-medium">Total Alerts</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{summary?.total || 0}</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs text-slate-500 font-medium">Unresolved Alerts</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{summary?.unresolved || 0}</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs text-slate-500 font-medium">Critical Severity</p>
          <p className="text-2xl font-bold text-rose-600 mt-1">{summary?.critical || 0}</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs text-slate-500 font-medium">Warnings</p>
          <p className="text-2xl font-bold text-yellow-600 mt-1">{summary?.warning || 0}</p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-semibold text-slate-800 text-sm">System Alerts List</h2>
          <select
            value={severityFilter}
            onChange={e => setSeverityFilter(e.target.value)}
            className="text-xs border rounded-lg px-2 py-1 bg-white"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="WARNING">WARNING</option>
            <option value="INFO">INFO</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold text-slate-500 border-b border-slate-100">
              <tr>
                <th className="p-4">Type</th>
                <th className="p-4">Severity</th>
                <th className="p-4">Title & Message</th>
                <th className="p-4">Status</th>
                <th className="p-4">Logged Time</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {alerts.map((a: any) => (
                <tr key={a.id} className="hover:bg-slate-50/50">
                  <td className="p-4 font-mono text-xs font-semibold text-slate-700">{a.alert_type}</td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      a.severity === 'CRITICAL' ? 'bg-rose-100 text-rose-800' :
                      a.severity === 'WARNING' ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'
                    }`}>
                      {a.severity}
                    </span>
                  </td>
                  <td className="p-4">
                    <p className="font-semibold text-slate-800">{a.title}</p>
                    <p className="text-xs text-slate-500">{a.message}</p>
                  </td>
                  <td className="p-4">
                    {a.is_resolved ? (
                      <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
                        <CheckCircle size={14} /> Resolved
                      </span>
                    ) : (
                      <span className="text-xs text-amber-600 font-semibold flex items-center gap-1">
                        <Clock size={14} /> Open
                      </span>
                    )}
                  </td>
                  <td className="p-4 text-xs text-slate-500">
                    {a.created_at ? new Date(a.created_at).toLocaleString() : '-'}
                  </td>
                  <td className="p-4 text-right">
                    {!a.is_resolved && (
                      <button
                        onClick={() => resolveMutation.mutate(a.id)}
                        className="px-3 py-1 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-medium"
                      >
                        Resolve
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {alerts.length === 0 && (
                <tr><td colSpan={6} className="p-8 text-center text-slate-400">No active alerts reported.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
