import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
export default function BatchPredictionPage() {
  const { data } = useQuery({ queryKey: ['batches'], queryFn: () => api.get('/predictions/batches').then(r => r.data.data) })
  return (<div className="space-y-6"><h1 className="text-2xl font-bold">Batch Prediction</h1>
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      <p className="text-gray-600 mb-4">Upload a CSV file to run batch predictions using a deployed model. The CSV should contain the same features used during training.</p>
      <p className="text-sm text-gray-400">Use the API endpoint POST /api/v1/predictions/predict/batch with a CSV file.</p>
    </div>
    <div className="bg-white rounded-xl shadow-sm border overflow-hidden"><h3 className="px-4 py-3 font-semibold bg-gray-50">Batch History</h3>
      <table className="w-full text-sm"><thead className="bg-gray-50"><tr><th className="px-4 py-3 text-left">Use Case</th><th className="px-4 py-3 text-right">Total</th><th className="px-4 py-3 text-right">Processed</th><th className="px-4 py-3 text-left">Status</th></tr></thead>
        <tbody>{(data || []).map((b: any) => <tr key={b.id} className="border-t"><td className="px-4 py-3">{b.use_case}</td><td className="px-4 py-3 text-right">{b.total_records}</td><td className="px-4 py-3 text-right">{b.processed_records}</td><td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${b.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>{b.status}</span></td></tr>)}</tbody>
      </table></div></div>)
}
