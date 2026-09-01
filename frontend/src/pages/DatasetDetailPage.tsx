import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function DatasetDetailPage() {
  const { id } = useParams()
  const { data, isLoading } = useQuery({ queryKey: ['dataset', id], queryFn: () => api.get(`/datasets/${id}`).then(r => r.data.data) })
  if (isLoading) return <div className="animate-pulse h-64 bg-gray-200 rounded-xl" />
  const d = data || {}
  const latestVersion = d.versions?.[0]
  const stats = latestVersion?.statistics ? Object.entries(latestVersion.statistics).slice(0, 10).map(([k, v]: any) => ({ name: k, mean: v?.mean || 0, std: v?.std || 0 })) : []
  const qr = latestVersion?.quality_report

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold">{d.name}</h1><p className="text-gray-500">{d.bank_name} • {d.use_case}</p></div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[['Rows', d.rows], ['Features', latestVersion?.features || 0], ['Quality', `${d.quality_score?.toFixed(0)}/100`], ['Missing', latestVersion?.missing_values || 0], ['Version', d.current_version]].map(([label, val]) => (
          <div key={label as string} className="bg-white rounded-xl p-4 shadow-sm border text-center"><p className="text-2xl font-bold text-blue-600">{val}</p><p className="text-xs text-gray-500">{label}</p></div>
        ))}
      </div>
      {stats.length > 0 && <div className="bg-white rounded-xl p-6 shadow-sm border"><h3 className="font-semibold mb-4">Feature Statistics</h3>
        <ResponsiveContainer width="100%" height={300}><BarChart data={stats}><XAxis dataKey="name" angle={-45} textAnchor="end" height={80} /><YAxis /><Tooltip /><Bar dataKey="mean" fill="#3b82f6" /></BarChart></ResponsiveContainer>
      </div>}
      {qr && <div className="bg-white rounded-xl p-6 shadow-sm border"><h3 className="font-semibold mb-4">Quality Report</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><p className="text-sm font-medium text-gray-500 mb-2">Missing Values</p>
            {Object.entries(qr.missing_value_report || {}).map(([k, v]: any) => <div key={k} className="flex justify-between text-sm py-1"><span>{k}</span><span className="text-red-500">{v.count} ({v.percentage}%)</span></div>)}
            {Object.keys(qr.missing_value_report || {}).length === 0 && <p className="text-green-600 text-sm">No missing values ✓</p>}
          </div>
          <div><p className="text-sm font-medium text-gray-500 mb-2">Recommendations</p>
            {(qr.recommendations || []).map((r: string, i: number) => <p key={i} className="text-sm text-gray-600 mb-1">• {r}</p>)}
            {(!qr.recommendations || qr.recommendations.length === 0) && <p className="text-green-600 text-sm">Dataset looks good ✓</p>}
          </div>
        </div>
      </div>}
    </div>
  )
}
