import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { GitCompare, CheckCircle2, TrendingUp, Award, Layers } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function ModelComparePage() {
  const [selectedV1, setSelectedV1] = useState<string>('')
  const [selectedV2, setSelectedV2] = useState<string>('')

  // Fetch all models to populate version selectors
  const { data: modelsData } = useQuery({
    queryKey: ['models-for-compare'],
    queryFn: () => api.get('/models', { params: { page_size: 50 } }).then(r => r.data.data),
  })

  // Fetch all versions
  const models = modelsData?.items || []
  const allVersions: any[] = []
  models.forEach((m: any) => {
    // Model summary contains latest_version
    if (m.latest_version) {
      allVersions.push({ id: m.id, label: `${m.name} (${m.latest_version})` })
    }
  })

  // Fetch Comparison Data
  const { data: compareData, isLoading } = useQuery({
    queryKey: ['models-compare-results', selectedV1, selectedV2],
    queryFn: () => {
      if (!selectedV1 || !selectedV2) return null
      return api.get(`/models/compare?version_ids=${selectedV1}&version_ids=${selectedV2}`).then(r => r.data.data)
    },
    enabled: Boolean(selectedV1 && selectedV2),
  })

  const results = compareData || []
  const v1 = results[0]
  const v2 = results[1]

  const metricsComparison = v1 && v2 ? [
    { metric: 'Accuracy', v1: ((v1.accuracy || 0) * 100).toFixed(1), v2: ((v2.accuracy || 0) * 100).toFixed(1) },
    { metric: 'Precision', v1: ((v1.precision_score || 0) * 100).toFixed(1), v2: ((v2.precision_score || 0) * 100).toFixed(1) },
    { metric: 'Recall', v1: ((v1.recall || 0) * 100).toFixed(1), v2: ((v2.recall || 0) * 100).toFixed(1) },
    { metric: 'F1 Score', v1: ((v1.f1 || 0) * 100).toFixed(1), v2: ((v2.f1 || 0) * 100).toFixed(1) },
    { metric: 'ROC-AUC', v1: ((v1.auc || 0) * 100).toFixed(1), v2: ((v2.auc || 0) * 100).toFixed(1) },
  ] : []

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <h1 className="text-2xl font-bold text-slate-800">Model Version Comparative Analysis</h1>
        <p className="text-sm text-slate-500 mt-1">
          Inspect statistical benchmarks, classification metrics, and ROC-AUC differences across federated model checkpoints.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div>
            <label className="text-xs font-semibold text-slate-600 block mb-1">Baseline Model Checkpoint</label>
            <select
              value={selectedV1}
              onChange={e => setSelectedV1(e.target.value)}
              className="w-full px-3 py-2 border rounded-xl text-sm bg-white"
            >
              <option value="">Select Model 1</option>
              {models.map((m: any) => (
                <option key={m.id} value={m.id}>{m.name} - {m.algorithm} ({m.latest_version || 'v1.0.0'})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-600 block mb-1">Challenger Model Checkpoint</label>
            <select
              value={selectedV2}
              onChange={e => setSelectedV2(e.target.value)}
              className="w-full px-3 py-2 border rounded-xl text-sm bg-white"
            >
              <option value="">Select Model 2</option>
              {models.map((m: any) => (
                <option key={m.id} value={m.id}>{m.name} - {m.algorithm} ({m.production_version || 'v2.1.0'})</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Comparison View */}
      {v1 && v2 ? (
        <div className="space-y-6">
          {/* Side by Side KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-blue-100 bg-blue-50/20">
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">Baseline</span>
              <h3 className="text-lg font-bold text-slate-800 mt-2">{v1.model_name || 'FedBank Baseline Model'}</h3>
              <p className="text-xs text-slate-500 font-mono">{v1.version} • {v1.algorithm}</p>

              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="bg-white p-3 rounded-xl border border-slate-100 text-center">
                  <p className="text-xs text-slate-400">Accuracy</p>
                  <p className="text-lg font-bold text-slate-800">{((v1.accuracy || 0) * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-white p-3 rounded-xl border border-slate-100 text-center">
                  <p className="text-xs text-slate-400">F1 Score</p>
                  <p className="text-lg font-bold text-slate-800">{((v1.f1 || 0) * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-white p-3 rounded-xl border border-slate-100 text-center">
                  <p className="text-xs text-slate-400">ROC-AUC</p>
                  <p className="text-lg font-bold text-slate-800">{((v1.auc || 0) * 100).toFixed(1)}%</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-emerald-100 bg-emerald-50/20">
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">Challenger</span>
              <h3 className="text-lg font-bold text-slate-800 mt-2">{v2.model_name || 'FedBank Candidate Model'}</h3>
              <p className="text-xs text-slate-500 font-mono">{v2.version} • {v2.algorithm}</p>

              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="bg-white p-3 rounded-xl border border-slate-100 text-center">
                  <p className="text-xs text-slate-400">Accuracy</p>
                  <p className="text-lg font-bold text-emerald-600">{((v2.accuracy || 0) * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-white p-3 rounded-xl border border-slate-100 text-center">
                  <p className="text-xs text-slate-400">F1 Score</p>
                  <p className="text-lg font-bold text-emerald-600">{((v2.f1 || 0) * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-white p-3 rounded-xl border border-slate-100 text-center">
                  <p className="text-xs text-slate-400">ROC-AUC</p>
                  <p className="text-lg font-bold text-emerald-600">{((v2.auc || 0) * 100).toFixed(1)}%</p>
                </div>
              </div>
            </div>
          </div>

          {/* Metric Comparison BarChart */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="font-bold text-slate-800 text-sm mb-4">Benchmark Delta (% Score)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={metricsComparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="metric" tick={{ fontSize: 12 }} />
                <YAxis domain={[50, 100]} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(val: any) => [`${val}%`, '']} />
                <Legend />
                <Bar dataKey="v1" name="Baseline Checkpoint" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="v2" name="Challenger Checkpoint" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl p-12 text-center text-slate-400 border border-slate-100">
          <GitCompare size={48} className="mx-auto mb-3 opacity-30" />
          <p className="font-semibold text-slate-600">Select two model versions to trigger automated side-by-side benchmark comparison.</p>
        </div>
      )}
    </div>
  )
}
