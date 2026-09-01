import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
export default function PredictionHistoryPage() {
  const { data } = useQuery({ queryKey: ['predictions'], queryFn: () => api.get('/predictions', { params: { page_size: 50 } }).then(r => r.data.data) })
  const items = data?.items || []
  const riskColor = (r: string) => r === 'HIGH_RISK' ? 'bg-red-100 text-red-700' : r === 'MEDIUM_RISK' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
  return (<div className="space-y-6"><h1 className="text-2xl font-bold">Prediction History</h1>
    <div className="bg-white rounded-xl shadow-sm border overflow-hidden"><table className="w-full text-sm">
      <thead className="bg-gray-50"><tr><th className="px-4 py-3 text-left">Use Case</th><th className="px-4 py-3 text-left">Result</th><th className="px-4 py-3 text-right">Probability</th><th className="px-4 py-3 text-right">Risk Score</th><th className="px-4 py-3 text-left">Risk</th><th className="px-4 py-3 text-left">Model</th><th className="px-4 py-3 text-left">Time</th></tr></thead>
      <tbody>{items.map((p: any) => <tr key={p.id} className="border-t hover:bg-gray-50"><td className="px-4 py-3">{p.use_case}</td><td className="px-4 py-3 font-medium">{p.prediction_result}</td><td className="px-4 py-3 text-right">{p.probability ? `${(p.probability * 100).toFixed(1)}%` : '-'}</td><td className="px-4 py-3 text-right">{p.risk_score || '-'}</td><td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${riskColor(p.risk_category)}`}>{p.risk_category}</span></td><td className="px-4 py-3 text-gray-500">{p.model_version}</td><td className="px-4 py-3 text-gray-400 text-xs">{p.created_at ? new Date(p.created_at).toLocaleString() : ''}</td></tr>)}</tbody>
    </table></div>{items.length === 0 && <div className="text-center py-12 text-gray-400">No predictions yet</div>}
  </div>)
}
