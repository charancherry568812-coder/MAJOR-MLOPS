import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'
import { Building2, Plus, Search } from 'lucide-react'

export default function BanksPage() {
  const [search, setSearch] = useState('')
  const { addToast } = useToastStore()
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['banks', search], queryFn: () => api.get('/banks', { params: { search, page_size: 50 } }).then(r => r.data.data) })

  if (isLoading) return <div className="animate-pulse space-y-4">{[1,2,3].map(i => <div key={i} className="h-20 bg-gray-200 rounded-xl" />)}</div>

  const banks = data?.items || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold">Bank Management</h1><p className="text-gray-500 text-sm">{data?.total || 0} banks registered</p></div>
      </div>
      <div className="relative max-w-md">
        <Search size={18} className="absolute left-3 top-2.5 text-gray-400" />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search banks..."
          className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {banks.map((b: any) => (
          <Link key={b.id} to={`/banks/${b.id}`} className="bg-white rounded-xl p-5 shadow-sm border hover:shadow-md transition">
            <div className="flex items-center gap-3 mb-3">
              <div className="bg-blue-100 p-2 rounded-lg"><Building2 size={20} className="text-blue-600" /></div>
              <div><h3 className="font-semibold">{b.name}</h3><p className="text-xs text-gray-400">{b.code}</p></div>
              <span className={`ml-auto px-2 py-0.5 rounded-full text-xs font-medium ${b.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{b.status}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-gray-50 rounded-lg p-2"><p className="text-lg font-bold text-blue-600">{b.client_count}</p><p className="text-xs text-gray-500">Clients</p></div>
              <div className="bg-gray-50 rounded-lg p-2"><p className="text-lg font-bold text-green-600">{b.dataset_count}</p><p className="text-xs text-gray-500">Datasets</p></div>
              <div className="bg-gray-50 rounded-lg p-2"><p className="text-xs text-gray-500 mt-1">{b.location}</p></div>
            </div>
          </Link>
        ))}
      </div>
      {banks.length === 0 && <div className="text-center py-12 text-gray-400"><Building2 size={48} className="mx-auto mb-4 opacity-50" /><p>No banks found</p></div>}
    </div>
  )
}
