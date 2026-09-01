import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'
import { Play, Square, GitBranch } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function FederatedTrainingPage() {
  const qc = useQueryClient()
  const { addToast } = useToastStore()
  const [config, setConfig] = useState({ model_type: 'random_forest', use_case: 'credit_risk', federated_strategy: 'fedavg', num_rounds: 10, num_clients: 4, local_epochs: 5, learning_rate: 0.01, batch_size: 32 })

  const { data: status } = useQuery({ queryKey: ['fed-status'], queryFn: () => api.get('/federated/status').then(r => r.data.data), refetchInterval: 3000 })
  const { data: metrics } = useQuery({ queryKey: ['fed-metrics'], queryFn: () => api.get('/federated/metrics').then(r => r.data.data), refetchInterval: 3000 })

  const start = useMutation({ mutationFn: () => api.post('/federated/start', config), onSuccess: () => { qc.invalidateQueries({ queryKey: ['fed-status'] }); addToast('success', 'Training started!') },
    onError: (e: any) => addToast('error', e.response?.data?.detail || 'Failed to start') })
  const stop = useMutation({ mutationFn: () => api.post('/federated/stop'), onSuccess: () => { qc.invalidateQueries({ queryKey: ['fed-status'] }); addToast('info', 'Training stopped') } })

  const isRunning = status?.status === 'RUNNING'
  const chartData = (metrics || []).map((m: any) => ({ round: m.round, accuracy: ((m.accuracy || 0) * 100).toFixed(1), f1: ((m.f1 || 0) * 100).toFixed(1), loss: m.loss?.toFixed(4) }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold">Federated Training</h1><p className="text-gray-500 text-sm">Train models across distributed bank nodes</p></div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${isRunning ? 'bg-blue-100 text-blue-700 animate-pulse' : 'bg-gray-100 text-gray-600'}`}>{status?.status || 'IDLE'}</span>
      </div>

      {/* Active Run */}
      {status?.active_run && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-blue-800">Active Training Run</h3>
            <button onClick={() => stop.mutate()} className="flex items-center gap-1 bg-red-500 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-red-600"><Square size={14} />Stop</button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
            <div><span className="text-blue-600">Round:</span> {status.active_run.current_round}/{status.active_run.total_rounds}</div>
            <div><span className="text-blue-600">Model:</span> {status.active_run.model_type}</div>
            <div><span className="text-blue-600">Strategy:</span> {status.active_run.strategy}</div>
            {status.active_run.global_accuracy && <div><span className="text-blue-600">Accuracy:</span> {(status.active_run.global_accuracy * 100).toFixed(1)}%</div>}
            {status.active_run.global_f1 && <div><span className="text-blue-600">F1:</span> {(status.active_run.global_f1 * 100).toFixed(1)}%</div>}
          </div>
          <div className="mt-3 bg-blue-200 rounded-full h-2"><div className="bg-blue-600 h-2 rounded-full transition-all" style={{ width: `${(status.active_run.current_round / status.active_run.total_rounds) * 100}%` }} /></div>
        </div>
      )}

      {/* Metrics Chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="font-semibold mb-4">Training Progress</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="round" /><YAxis /><Tooltip /><Legend />
              <Line type="monotone" dataKey="accuracy" stroke="#3b82f6" strokeWidth={2} name="Accuracy %" />
              <Line type="monotone" dataKey="f1" stroke="#10b981" strokeWidth={2} name="F1 %" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Config Form */}
      {!isRunning && (
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="font-semibold mb-4">Start New Training</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div><label className="block text-xs text-gray-500 mb-1">Use Case</label>
              <select value={config.use_case} onChange={e => setConfig(c => ({...c, use_case: e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="credit_risk">Credit Risk</option><option value="fraud">Fraud Detection</option><option value="churn">Churn</option><option value="aml">AML</option>
              </select></div>
            <div><label className="block text-xs text-gray-500 mb-1">Algorithm</label>
              <select value={config.model_type} onChange={e => setConfig(c => ({...c, model_type: e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="random_forest">Random Forest</option><option value="gradient_boosting">Gradient Boosting</option><option value="logistic_regression">Logistic Regression</option><option value="xgboost">XGBoost</option>
              </select></div>
            <div><label className="block text-xs text-gray-500 mb-1">Strategy</label>
              <select value={config.federated_strategy} onChange={e => setConfig(c => ({...c, federated_strategy: e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="fedavg">FedAvg</option><option value="fedprox">FedProx</option>
              </select></div>
            <div><label className="block text-xs text-gray-500 mb-1">Rounds</label>
              <input type="number" value={config.num_rounds} onChange={e => setConfig(c => ({...c, num_rounds: +e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm" min={1} max={50} /></div>
            <div><label className="block text-xs text-gray-500 mb-1">Clients</label>
              <input type="number" value={config.num_clients} onChange={e => setConfig(c => ({...c, num_clients: +e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm" min={2} max={10} /></div>
            <div><label className="block text-xs text-gray-500 mb-1">Local Epochs</label>
              <input type="number" value={config.local_epochs} onChange={e => setConfig(c => ({...c, local_epochs: +e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm" min={1} max={20} /></div>
            <div><label className="block text-xs text-gray-500 mb-1">Learning Rate</label>
              <input type="number" step="0.001" value={config.learning_rate} onChange={e => setConfig(c => ({...c, learning_rate: +e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm" /></div>
          </div>
          <button onClick={() => start.mutate()} disabled={start.isPending}
            className="mt-4 flex items-center gap-2 bg-green-600 text-white px-6 py-2.5 rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium">
            <Play size={16} />{start.isPending ? 'Starting...' : 'Start Federated Training'}
          </button>
        </div>
      )}

      {/* Clients Status */}
      <div className="bg-white rounded-xl p-6 shadow-sm border">
        <h3 className="font-semibold mb-4">Client Nodes ({status?.total_clients || 0})</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {(status?.clients || []).map((c: any) => (
            <div key={c.id} className="border rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1"><GitBranch size={14} className={c.status === 'TRAINING' ? 'text-blue-500' : 'text-green-500'} /><span className="font-medium text-sm">{c.name}</span></div>
              <p className="text-xs text-gray-400">Round: {c.current_round} {c.local_accuracy ? `• ${(c.local_accuracy * 100).toFixed(1)}%` : ''}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
