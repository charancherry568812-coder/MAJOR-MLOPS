import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
export default function ModelDetailPage() {
  const { id } = useParams(); const qc = useQueryClient(); const { addToast } = useToastStore()
  const { data } = useQuery({ queryKey: ['model', id], queryFn: () => api.get(`/models/${id}`).then(r => r.data.data) })
  const approve = useMutation({ mutationFn: (vid: string) => api.post(`/models/${vid}/approve`, { reason: 'Approved after review' }), onSuccess: () => { qc.invalidateQueries({ queryKey: ['model', id] }); addToast('success', 'Model approved!') } })
  const deploy = useMutation({ mutationFn: (vid: string) => api.post(`/models/${vid}/deploy`), onSuccess: () => { qc.invalidateQueries({ queryKey: ['model', id] }); addToast('success', 'Model deployed!') } })
  const m = data || {}; const versions = m.versions || []
  return (<div className="space-y-6">
    <div><h1 className="text-2xl font-bold">{m.name}</h1><p className="text-gray-500">{m.algorithm} • {m.use_case}</p></div>
    {versions.map((v: any) => {
      const fi = Object.entries(v.feature_importance || {}).slice(0, 10).map(([k, val]: any) => ({ name: k, importance: (val * 100).toFixed(1) }))
      return (<div key={v.id} className="bg-white rounded-xl p-6 shadow-sm border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3"><h3 className="font-semibold">{v.version}</h3><span className={`px-2 py-0.5 rounded text-xs ${v.status === 'PRODUCTION' ? 'bg-green-100 text-green-700' : v.status === 'APPROVED' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}>{v.status}</span></div>
          <div className="flex gap-2">{v.status === 'REGISTERED' && <button onClick={() => approve.mutate(v.id)} className="bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-700">Approve</button>}
            {(v.status === 'APPROVED' || v.status === 'STAGING') && <button onClick={() => deploy.mutate(v.id)} className="bg-green-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-green-700">Deploy to Production</button>}
          </div></div>
        <div className="grid grid-cols-5 gap-3 mb-4">{[['Accuracy', v.accuracy], ['Precision', v.precision_score], ['Recall', v.recall], ['F1', v.f1], ['AUC', v.auc]].map(([label, val]) =>
          <div key={label as string} className="bg-gray-50 rounded-lg p-3 text-center"><p className="text-xl font-bold text-blue-600">{val ? `${(Number(val) * 100).toFixed(1)}%` : 'N/A'}</p><p className="text-xs text-gray-500">{label}</p></div>)}</div>
        {fi.length > 0 && <div><h4 className="text-sm font-medium text-gray-500 mb-2">Feature Importance</h4><ResponsiveContainer width="100%" height={200}><BarChart data={fi} layout="vertical"><XAxis type="number" /><YAxis type="category" dataKey="name" width={120} /><Tooltip /><Bar dataKey="importance" fill="#3b82f6" /></BarChart></ResponsiveContainer></div>}
      </div>)})}
    {versions.length === 0 && <div className="text-center py-12 text-gray-400">No versions found</div>}
  </div>)
}
