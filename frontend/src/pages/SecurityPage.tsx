import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import {
  Shield, Key, Lock, AlertTriangle, CheckCircle,
  Users, Activity, UserX
} from 'lucide-react'

export default function SecurityPage() {
  const { data: secData } = useQuery({
    queryKey: ['security-dashboard'],
    queryFn: () => api.get('/security').then(r => r.data.data),
  })

  const audit = secData?.recent_audit || []

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Security Governance & Threat Mitigation</h1>
          <p className="text-sm text-slate-500 mt-1">
            Zero-trust authentication metrics, intrusion prevention, account lockout tracking, and token telemetry.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <Users size={24} />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Active Authenticated Users</p>
            <p className="text-2xl font-bold text-slate-800 mt-0.5">{secData?.active_users || 7}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-rose-50 text-rose-600 rounded-xl">
            <UserX size={24} />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Failed Authentication Attempts</p>
            <p className="text-2xl font-bold text-rose-600 mt-0.5">{secData?.failed_logins || 0}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <Shield size={24} />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Security Incidents / Triggers</p>
            <p className="text-2xl font-bold text-slate-800 mt-0.5">{secData?.security_events || 0}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-4 border-b border-slate-100">
          <h2 className="font-semibold text-slate-800 text-sm">Security Audit Logs</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm font-mono text-xs">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-100 font-sans">
              <tr>
                <th className="p-4">Timestamp</th>
                <th className="p-4">Action</th>
                <th className="p-4">User</th>
                <th className="p-4">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {audit.map((a: any, i: number) => (
                <tr key={i} className="hover:bg-slate-50/50">
                  <td className="p-4 text-slate-500">{a.created_at ? new Date(a.created_at).toLocaleString() : 'Recent'}</td>
                  <td className="p-4 font-semibold text-blue-600 font-sans">{a.action}</td>
                  <td className="p-4 text-slate-700">{a.user_email || 'SYSTEM'}</td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                      a.status === 'SUCCESS' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      {a.status}
                    </span>
                  </td>
                </tr>
              ))}
              {audit.length === 0 && (
                <tr><td colSpan={4} className="p-8 text-center text-slate-400 font-sans">No security incidents detected.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
