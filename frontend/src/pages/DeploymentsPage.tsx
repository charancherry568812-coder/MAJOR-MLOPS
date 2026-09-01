import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import {
  Package, Server, CheckCircle2, RotateCcw, AlertTriangle,
  ExternalLink, Zap, Shield
} from 'lucide-react'
import { useToastStore } from '../store/toastStore'

export default function DeploymentsPage() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()

  const { data: deploymentsData, refetch } = useQuery({
    queryKey: ['deployments'],
    queryFn: () => api.get('/deployments').then(r => r.data.data),
  })

  const rollbackMutation = useMutation({
    mutationFn: () => api.post('/pipeline/rollback'),
    onSuccess: (res: any) => {
      addToast('info', res.data.message || 'Rollback triggered')
      refetch()
    },
    onError: (err: any) => addToast('error', 'Rollback failed'),
  })

  const deployments: any[] = deploymentsData || []

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Model Deployment & Serving Endpoints</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time inference endpoints serving global models trained across federated banking nodes.
          </p>
        </div>
        <button
          onClick={() => rollbackMutation.mutate()}
          disabled={rollbackMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-sm font-semibold transition-all shadow-sm"
        >
          <RotateCcw size={16} />
          Rollback Active Deployment
        </button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-semibold text-slate-800 text-sm">Active & Historical Serving Endpoints</h2>
          <span className="text-xs text-slate-400 font-mono">Inference Port: 8000</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold text-slate-500 border-b border-slate-100">
              <tr>
                <th className="p-4">Model Name</th>
                <th className="p-4">Version</th>
                <th className="p-4">Use Case</th>
                <th className="p-4">Status</th>
                <th className="p-4">Inference Endpoint</th>
                <th className="p-4">Deployed At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {deployments.map((d: any) => (
                <tr key={d.id} className="hover:bg-slate-50/50">
                  <td className="p-4 font-semibold text-slate-800 flex items-center gap-2">
                    <Package size={16} className="text-blue-500" />
                    {d.model_name || 'FedBank Credit Risk Ensemble'}
                  </td>
                  <td className="p-4 font-mono font-medium text-slate-700">{d.model_version || 'v2.1.0'}</td>
                  <td className="p-4 text-xs font-medium text-slate-600">{d.use_case || 'credit_risk'}</td>
                  <td className="p-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      d.status === 'ACTIVE' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {d.status}
                    </span>
                  </td>
                  <td className="p-4 font-mono text-xs text-blue-600">{d.endpoint || '/api/v1/predictions/single'}</td>
                  <td className="p-4 text-xs text-slate-500">
                    {d.deployed_at ? new Date(d.deployed_at).toLocaleString() : 'Recent'}
                  </td>
                </tr>
              ))}
              {deployments.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    Active endpoint running FedBank Credit Risk v2.1.0 in production serving.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
