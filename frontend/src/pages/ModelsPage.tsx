import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'
export default function ModelsPage() {
  const { data } = useQuery({ queryKey: ['models'], queryFn: () => api.get('/models', { params: { page_size: 50 } }).then(r => r.data.data) })
  const items = data?.items || []
  return (<div className="space-y-6"><h1 className="text-2xl font-bold">Model Registry</h1>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((m: any) => <Link key={m.id} to={`/models/${m.id}`} className="bg-white rounded-xl p-5 shadow-sm border hover:shadow-md transition">
        <div className="flex items-center justify-between mb-2"><h3 className="font-semibold">{m.name}</h3><span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{m.use_case}</span></div>
        <p className="text-sm text-gray-500 mb-3">{m.algorithm} • {m.versions_count} versions</p>
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-400">Latest: {m.latest_version || 'N/A'}</span>
          {m.production_version && <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded">Production: {m.production_version}</span>}
        </div>
      </Link>)}
    </div>{items.length === 0 && <div className="text-center py-12 text-gray-400">No models registered yet. Complete a training run to register models.</div>}
  </div>)
}
