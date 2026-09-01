import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'
import { Database, Upload, Sparkles } from 'lucide-react'

export default function DatasetsPage() {
  const [useCase, setUseCase] = useState('')
  const qc = useQueryClient()
  const { addToast } = useToastStore()
  const { data, isLoading } = useQuery({ queryKey: ['datasets', useCase], queryFn: () => api.get('/datasets', { params: { page_size: 50, use_case: useCase || undefined } }).then(r => r.data.data) })
  const generate = useMutation({ mutationFn: () => api.post('/datasets/generate-demo'), onSuccess: () => { qc.invalidateQueries({ queryKey: ['datasets'] }); addToast('success', 'Demo data generated!') } })
  if (isLoading) return <div className="animate-pulse space-y-4">{[1,2,3].map(i => <div key={i} className="h-16 bg-gray-200 rounded-xl" />)}</div>
  const datasets = data?.items || []
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold">Datasets</h1><p className="text-gray-500 text-sm">{data?.total || 0} datasets</p></div>
        <button onClick={() => generate.mutate()} disabled={generate.isPending}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">
          <Sparkles size={16} />{generate.isPending ? 'Generating...' : 'Generate Demo Data'}
        </button>
      </div>
      <select value={useCase} onChange={e => setUseCase(e.target.value)} className="border rounded-lg px-3 py-2">
        <option value="">All Use Cases</option>
        <option value="credit_risk">Credit Risk</option><option value="fraud">Fraud Detection</option>
        <option value="churn">Churn</option><option value="aml">AML</option>
      </select>
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50"><tr>
            <th className="text-left px-4 py-3 font-medium">Name</th><th className="text-left px-4 py-3 font-medium">Bank</th>
            <th className="text-left px-4 py-3 font-medium">Use Case</th><th className="text-right px-4 py-3 font-medium">Rows</th>
            <th className="text-right px-4 py-3 font-medium">Quality</th><th className="text-left px-4 py-3 font-medium">Status</th>
          </tr></thead>
          <tbody>{datasets.map((d: any) => (
            <tr key={d.id} className="border-t hover:bg-gray-50 cursor-pointer" onClick={() => window.location.href=`/datasets/${d.id}`}>
              <td className="px-4 py-3 font-medium">{d.name}</td><td className="px-4 py-3 text-gray-500">{d.bank_name}</td>
              <td className="px-4 py-3"><span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{d.use_case}</span></td>
              <td className="px-4 py-3 text-right">{d.rows?.toLocaleString()}</td>
              <td className="px-4 py-3 text-right"><span className={`font-medium ${d.quality_score >= 80 ? 'text-green-600' : d.quality_score >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>{d.quality_score?.toFixed(0)}/100</span></td>
              <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${d.status === 'VALIDATED' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{d.status}</span></td>
            </tr>))}
          </tbody>
        </table>
        {datasets.length === 0 && <div className="text-center py-12 text-gray-400"><Database size={48} className="mx-auto mb-4 opacity-50" /><p>No datasets. Click "Generate Demo Data" to create synthetic banking data.</p></div>}
      </div>
    </div>
  )
}
