import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { Wifi, WifiOff } from 'lucide-react'

export default function ClientsPage() {
  const { data, isLoading } = useQuery({ queryKey: ['clients'], queryFn: () => api.get('/clients', { params: { page_size: 50 } }).then(r => r.data.data) })
  if (isLoading) return <div className="animate-pulse space-y-4">{[1,2,3].map(i => <div key={i} className="h-20 bg-gray-200 rounded-xl" />)}</div>
  const clients = data?.items || []
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Federated Clients</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clients.map((c: any) => (
          <div key={c.id} className="bg-white rounded-xl p-5 shadow-sm border">
            <div className="flex items-center gap-3 mb-3">
              {c.status === 'OFFLINE' || c.status === 'DISABLED' ? <WifiOff size={20} className="text-red-400" /> : <Wifi size={20} className="text-green-500" />}
              <div><h3 className="font-semibold">{c.name}</h3><p className="text-xs text-gray-400">{c.bank_name}</p></div>
              <span className={`ml-auto px-2 py-0.5 rounded-full text-xs font-medium ${c.status === 'TRAINING' ? 'bg-blue-100 text-blue-700' : c.status === 'IDLE' || c.status === 'ONLINE' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{c.status}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div><span className="text-gray-500">Host:</span> {c.host}:{c.port}</div>
              <div><span className="text-gray-500">Round:</span> {c.current_round}</div>
              {c.local_accuracy && <div><span className="text-gray-500">Accuracy:</span> {(c.local_accuracy * 100).toFixed(1)}%</div>}
              {c.local_loss !== null && <div><span className="text-gray-500">Loss:</span> {c.local_loss?.toFixed(4)}</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
