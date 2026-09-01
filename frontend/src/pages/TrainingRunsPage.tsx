import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
export default function TrainingRunsPage() {
  const { data } = useQuery({ queryKey: ['training-runs'], queryFn: () => api.get('/training-runs', { params: { page_size: 50 } }).then(r => r.data.data) })
  const items = data?.items || []
  const statusColor = (s: string) => s === 'COMPLETED' ? 'bg-green-100 text-green-700' : s === 'RUNNING' ? 'bg-blue-100 text-blue-700' : s === 'FAILED' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'
  return (<div className="space-y-6"><h1 className="text-2xl font-bold">Training Runs</h1>
    <div className="bg-white rounded-xl shadow-sm border overflow-hidden"><table className="w-full text-sm">
      <thead className="bg-gray-50"><tr><th className="px-4 py-3 text-left">Model</th><th className="px-4 py-3 text-left">Use Case</th><th className="px-4 py-3 text-left">Strategy</th><th className="px-4 py-3 text-right">Rounds</th><th className="px-4 py-3 text-right">Accuracy</th><th className="px-4 py-3 text-right">F1</th><th className="px-4 py-3 text-left">Status</th></tr></thead>
      <tbody>{items.map((r: any) => <tr key={r.id} className="border-t hover:bg-gray-50"><td className="px-4 py-3 font-medium">{r.model_type}</td><td className="px-4 py-3">{r.use_case}</td><td className="px-4 py-3">{r.federated_strategy}</td><td className="px-4 py-3 text-right">{r.num_rounds}</td><td className="px-4 py-3 text-right">{r.best_accuracy ? `${(r.best_accuracy * 100).toFixed(1)}%` : '-'}</td><td className="px-4 py-3 text-right">{r.best_f1 ? `${(r.best_f1 * 100).toFixed(1)}%` : '-'}</td><td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${statusColor(r.status)}`}>{r.status}</span></td></tr>)}</tbody>
    </table></div>{items.length === 0 && <div className="text-center py-12 text-gray-400">No training runs yet</div>}
  </div>)
}
