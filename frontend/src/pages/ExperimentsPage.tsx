import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
export default function ExperimentsPage() {
  const { data } = useQuery({ queryKey: ['experiments'], queryFn: () => api.get('/experiments', { params: { page_size: 50 } }).then(r => r.data.data) })
  const items = data?.items || []
  return (<div className="space-y-6"><h1 className="text-2xl font-bold">Experiments</h1>
    <div className="bg-white rounded-xl shadow-sm border overflow-hidden"><table className="w-full text-sm">
      <thead className="bg-gray-50"><tr><th className="px-4 py-3 text-left">Name</th><th className="px-4 py-3 text-left">Use Case</th><th className="px-4 py-3 text-right">Runs</th><th className="px-4 py-3 text-left">Status</th><th className="px-4 py-3 text-left">Created</th></tr></thead>
      <tbody>{items.map((e: any) => <tr key={e.id} className="border-t hover:bg-gray-50"><td className="px-4 py-3 font-medium">{e.name}</td><td className="px-4 py-3">{e.use_case}</td><td className="px-4 py-3 text-right">{e.training_runs_count}</td><td className="px-4 py-3"><span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">{e.status}</span></td><td className="px-4 py-3 text-gray-500 text-xs">{e.created_at ? new Date(e.created_at).toLocaleDateString() : ''}</td></tr>)}</tbody>
    </table></div>
    {items.length === 0 && <div className="text-center py-12 text-gray-400">No experiments yet</div>}
  </div>)
}
