import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function FederatedRoundsPage() {
  const { data } = useQuery({ queryKey: ['fed-rounds'], queryFn: () => api.get('/federated/rounds').then(r => r.data.data) })
  const rounds = (data || []).map((r: any) => ({ ...r, accuracy_pct: ((r.global_accuracy || 0) * 100).toFixed(1), f1_pct: ((r.global_f1 || 0) * 100).toFixed(1) }))
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Training Rounds</h1>
      {rounds.length > 0 && <div className="bg-white rounded-xl p-6 shadow-sm border"><ResponsiveContainer width="100%" height={300}>
        <LineChart data={rounds}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="round_number" /><YAxis /><Tooltip />
          <Line type="monotone" dataKey="accuracy_pct" stroke="#3b82f6" strokeWidth={2} name="Accuracy %" />
          <Line type="monotone" dataKey="f1_pct" stroke="#10b981" strokeWidth={2} name="F1 %" />
        </LineChart></ResponsiveContainer></div>}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden"><table className="w-full text-sm">
        <thead className="bg-gray-50"><tr><th className="px-4 py-3 text-left">Round</th><th className="px-4 py-3 text-right">Accuracy</th><th className="px-4 py-3 text-right">Precision</th><th className="px-4 py-3 text-right">Recall</th><th className="px-4 py-3 text-right">F1</th><th className="px-4 py-3 text-right">AUC</th><th className="px-4 py-3 text-right">Clients</th></tr></thead>
        <tbody>{rounds.map((r: any) => <tr key={r.id} className="border-t"><td className="px-4 py-3">Round {r.round_number}</td><td className="px-4 py-3 text-right">{r.accuracy_pct}%</td><td className="px-4 py-3 text-right">{((r.global_precision || 0) * 100).toFixed(1)}%</td><td className="px-4 py-3 text-right">{((r.global_recall || 0) * 100).toFixed(1)}%</td><td className="px-4 py-3 text-right">{r.f1_pct}%</td><td className="px-4 py-3 text-right">{((r.global_auc || 0) * 100).toFixed(1)}%</td><td className="px-4 py-3 text-right">{r.participating_clients}/{r.total_clients}</td></tr>)}</tbody>
      </table></div>
      {rounds.length === 0 && <div className="text-center py-12 text-gray-400">No training rounds yet. Start a federated training first.</div>}
    </div>
  )
}
