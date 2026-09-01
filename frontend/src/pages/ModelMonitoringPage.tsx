import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'
export default function ModelMonitoringPage() {
  const qc = useQueryClient(); const { addToast } = useToastStore()
  const { data } = useQuery({ queryKey: ['monitoring'], queryFn: () => api.get('/monitoring').then(r => r.data.data) })
  const { data: perf } = useQuery({ queryKey: ['monitoring-perf'], queryFn: () => api.get('/monitoring/performance').then(r => r.data.data) })
  const check = useMutation({ mutationFn: () => api.post('/monitoring/check'), onSuccess: () => { qc.invalidateQueries({ queryKey: ['monitoring'] }); addToast('success', 'Monitoring check completed') } })
  const d = data || {}
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><h1 className="text-2xl font-bold">Model Monitoring</h1>
      <button onClick={() => check.mutate()} disabled={check.isPending} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">{check.isPending ? 'Checking...' : 'Run Check'}</button></div>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[['Total Checks', d.model_metrics?.length || 0, 'blue'], ['Drift Alerts', d.drift_summary?.critical || 0, 'red'], ['Warnings', d.drift_summary?.warning || 0, 'yellow'], ['Normal', d.drift_summary?.normal || 0, 'green']].map(([l, v, c]) =>
        <div key={l as string} className="bg-white rounded-xl p-4 shadow-sm border text-center"><p className={`text-2xl font-bold text-${c}-600`}>{v}</p><p className="text-xs text-gray-500">{l}</p></div>)}
    </div>
    <div className="bg-white rounded-xl shadow-sm border overflow-hidden"><h3 className="px-4 py-3 font-semibold bg-gray-50">Model Performance Tracking</h3>
      <table className="w-full text-sm"><thead className="bg-gray-50"><tr><th className="px-4 py-3 text-left">Version</th><th className="px-4 py-3 text-right">Accuracy</th><th className="px-4 py-3 text-right">F1</th><th className="px-4 py-3 text-right">AUC</th><th className="px-4 py-3 text-left">Status</th></tr></thead>
        <tbody>{(perf || []).map((v: any) => <tr key={v.id} className="border-t"><td className="px-4 py-3 font-medium">{v.version}</td><td className="px-4 py-3 text-right">{v.accuracy ? `${(v.accuracy * 100).toFixed(1)}%` : '-'}</td><td className="px-4 py-3 text-right">{v.f1 ? `${(v.f1 * 100).toFixed(1)}%` : '-'}</td><td className="px-4 py-3 text-right">{v.auc ? `${(v.auc * 100).toFixed(1)}%` : '-'}</td><td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${v.status === 'PRODUCTION' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{v.status}</span></td></tr>)}</tbody>
      </table></div></div>)
}
