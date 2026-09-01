import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import {
  FileText, Search, Filter, Download, ShieldCheck,
  CheckCircle, AlertCircle, Clock, ArrowUpDown
} from 'lucide-react'

export default function AuditLogsPage() {
  const [page, setPage] = useState(1)
  const [actionFilter, setActionFilter] = useState('')
  const [searchUser, setSearchUser] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', page, actionFilter, searchUser],
    queryFn: () => {
      let url = `/audit-logs?page=${page}&page_size=25`
      if (actionFilter) url += `&action=${actionFilter}`
      if (searchUser) url += `&user_email=${searchUser}`
      return api.get(url).then(r => r.data.data)
    },
  })

  const logs = data?.items || []
  const total = data?.total || 0
  const totalPages = data?.total_pages || 1

  const handleExportCSV = () => {
    window.open(`${api.defaults.baseURL}/reports/generate?report_type=AUDIT&format=CSV`, '_blank')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Enterprise Compliance & Audit Trail</h1>
          <p className="text-sm text-slate-500 mt-1">
            Immutable system logs tracking authentication, dataset access, federated training runs, model deployments, and fraud actions.
          </p>
        </div>
        <button
          onClick={handleExportCSV}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-sm font-semibold transition-all shadow-sm"
        >
          <Download size={16} />
          Export Audit Trail (CSV)
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap gap-3 items-center flex-1">
          <div className="relative min-w-[240px]">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Filter by user email..."
              value={searchUser}
              onChange={e => { setSearchUser(e.target.value); setPage(1) }}
              className="w-full pl-9 pr-3 py-1.5 text-sm border rounded-xl"
            />
          </div>

          <select
            value={actionFilter}
            onChange={e => { setActionFilter(e.target.value); setPage(1) }}
            className="px-3 py-1.5 text-sm border rounded-xl text-slate-700 bg-white"
          >
            <option value="">All Operations</option>
            <option value="LOGIN">LOGIN</option>
            <option value="LOGOUT">LOGOUT</option>
            <option value="USER_CREATED">USER_CREATED</option>
            <option value="BANK_CREATED">BANK_CREATED</option>
            <option value="DATA_UPLOADED">DATA_UPLOADED</option>
            <option value="TRAINING_STARTED">TRAINING_STARTED</option>
            <option value="TRAINING_COMPLETED">TRAINING_COMPLETED</option>
            <option value="MODEL_REGISTERED">MODEL_REGISTERED</option>
            <option value="MODEL_DEPLOYED">MODEL_DEPLOYED</option>
            <option value="MODEL_ROLLBACK">MODEL_ROLLBACK</option>
            <option value="PREDICTION_CREATED">PREDICTION_CREATED</option>
            <option value="FRAUD_ALERT_CREATED">FRAUD_ALERT_CREATED</option>
            <option value="FRAUD_ALERT_RESOLVED">FRAUD_ALERT_RESOLVED</option>
          </select>
        </div>

        <span className="text-xs text-slate-400 font-medium">Total logged events: {total}</span>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold text-slate-500 border-b border-slate-100">
              <tr>
                <th className="p-4">Timestamp (UTC)</th>
                <th className="p-4">User</th>
                <th className="p-4">Role</th>
                <th className="p-4">Action</th>
                <th className="p-4">Resource</th>
                <th className="p-4">Status</th>
                <th className="p-4">Audit Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-xs">
              {logs.map((log: any) => (
                <tr key={log.id} className="hover:bg-slate-50/50">
                  <td className="p-4 text-slate-500 whitespace-nowrap">
                    {log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}
                  </td>
                  <td className="p-4 font-sans font-medium text-slate-800">{log.user_email || 'SYSTEM'}</td>
                  <td className="p-4 font-sans">
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">
                      {log.user_role || 'DAEMON'}
                    </span>
                  </td>
                  <td className="p-4 font-semibold text-blue-600">{log.action}</td>
                  <td className="p-4 text-slate-600">{log.resource_type || '-'}</td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                      log.status === 'SUCCESS' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      {log.status}
                    </span>
                  </td>
                  <td className="p-4 text-slate-500 max-w-sm truncate">
                    {typeof log.details === 'object' ? JSON.stringify(log.details) : log.details || '-'}
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400 font-sans">
                    No matching audit records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 border rounded-lg hover:bg-slate-50 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1.5 border rounded-lg hover:bg-slate-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
