import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'

export default function BankDetailPage() {
  const { id } = useParams()
  const { data, isLoading } = useQuery({ queryKey: ['bank', id], queryFn: () => api.get(`/banks/${id}`).then(r => r.data.data) })
  if (isLoading) return <div className="animate-pulse h-64 bg-gray-200 rounded-xl" />
  const b = data || {}
  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold">{b.name}</h1><p className="text-gray-500">{b.code} • {b.location}</p></div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-5 shadow-sm border"><p className="text-sm text-gray-500">Contact</p><p className="font-semibold">{b.contact_person}</p><p className="text-sm text-gray-400">{b.email} • {b.phone}</p></div>
        <div className="bg-white rounded-xl p-5 shadow-sm border"><p className="text-sm text-gray-500">Clients</p><p className="text-3xl font-bold text-blue-600">{b.client_count}</p></div>
        <div className="bg-white rounded-xl p-5 shadow-sm border"><p className="text-sm text-gray-500">Datasets</p><p className="text-3xl font-bold text-green-600">{b.dataset_count}</p></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-5 shadow-sm border"><h3 className="font-semibold mb-3">Federated Clients</h3>
          {(b.clients || []).map((c: any) => <div key={c.id} className="flex items-center justify-between py-2 border-b last:border-0">
            <span>{c.name}</span><span className={`px-2 py-0.5 rounded text-xs ${c.status === 'IDLE' || c.status === 'ONLINE' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{c.status}</span>
          </div>)}
          {(!b.clients || b.clients.length === 0) && <p className="text-gray-400 text-sm">No clients</p>}
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border"><h3 className="font-semibold mb-3">Datasets</h3>
          {(b.datasets || []).map((d: any) => <div key={d.id} className="flex items-center justify-between py-2 border-b last:border-0">
            <span>{d.name}</span><span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{d.use_case}</span>
          </div>)}
          {(!b.datasets || b.datasets.length === 0) && <p className="text-gray-400 text-sm">No datasets</p>}
        </div>
      </div>
    </div>
  )
}
