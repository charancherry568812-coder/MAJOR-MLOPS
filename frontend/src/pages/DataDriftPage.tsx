import { useState, useEffect } from 'react'
import {
  Activity, Play, AlertTriangle, CheckCircle2, TrendingUp,
  RefreshCw, BarChart2, Zap
} from 'lucide-react'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'

export default function DataDriftPage() {
  const [reports, setReports] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [calculating, setCalculating] = useState(false)
  const { addToast } = useToastStore()

  useEffect(() => {
    fetchDriftReports()
  }, [])

  const fetchDriftReports = async () => {
    try {
      setLoading(true)
      const res = await api.get('/data-drift/psi')
      setReports(res.data.data || [])
    } catch (err) {
      addToast('error', 'Failed to load PSI drift reports')
    } finally {
      setLoading(false)
    }
  }

  const handleRunDriftAnalysis = async () => {
    try {
      setCalculating(true)
      const res = await api.post('/data-drift/calculate')
      addToast('success', `Statistical PSI analysis completed across ${res.data.data.features_analyzed} features!`)
      fetchDriftReports()
    } catch (err) {
      addToast('error', 'Drift analysis calculation failed')
    } finally {
      setCalculating(false)
    }
  }

  const getStatusBadge = (status: string) => {
    if (status === 'DRIFT' || status === 'CRITICAL') {
      return <span className="badge badge-danger">SIGNIFICANT DRIFT</span>
    }
    if (status === 'WARNING') {
      return <span className="badge badge-warning">MODERATE SHIFT</span>
    }
    return <span className="badge badge-success">STABLE POPULATION</span>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            📊 <span>Statistical Data Drift & Model Decay Analytics</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Population Stability Index (PSI) $\sum (A_i - E_i) \cdot \ln(A_i/E_i)$ and 2-Sample Kolmogorov-Smirnov continuous distribution tests.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRunDriftAnalysis}
            disabled={calculating}
            className="btn-primary flex items-center gap-2 text-xs"
          >
            <Zap className="w-3.5 h-3.5 fill-current" />
            {calculating ? 'Computing PSI & KS Tests...' : 'Calculate Dataset Drift'}
          </button>
          <button onClick={fetchDriftReports} className="btn-secondary flex items-center gap-2 text-xs">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-5 border-l-4 border-l-emerald-500 space-y-1">
          <span className="text-xs text-slate-500 font-semibold">Population Stability Index (PSI &lt; 0.10)</span>
          <h3 className="text-2xl font-bold text-slate-900">
            {reports.filter(r => r.drift_score < 0.10).length} Features
          </h3>
          <p className="text-[11px] text-emerald-600 font-medium">No significant distribution shift</p>
        </div>

        <div className="card p-5 border-l-4 border-l-amber-500 space-y-1">
          <span className="text-xs text-slate-500 font-semibold">Moderate Shift (0.10 &le; PSI &le; 0.25)</span>
          <h3 className="text-2xl font-bold text-slate-900">
            {reports.filter(r => r.drift_score >= 0.10 && r.drift_score < 0.25).length} Features
          </h3>
          <p className="text-[11px] text-amber-600 font-medium">Monitor during next federated cycle</p>
        </div>

        <div className="card p-5 border-l-4 border-l-rose-500 space-y-1">
          <span className="text-xs text-slate-500 font-semibold">Significant Drift (PSI &gt; 0.25)</span>
          <h3 className="text-2xl font-bold text-slate-900">
            {reports.filter(r => r.drift_score >= 0.25).length} Features
          </h3>
          <p className="text-[11px] text-rose-600 font-medium">Triggers automated federated retraining</p>
        </div>
      </div>

      {/* Table Card */}
      <div className="card overflow-hidden">
        <h2 className="text-base font-semibold text-slate-900 mb-4">Feature-Level Statistical Metrics</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="p-3">Feature Name</th>
                <th className="p-3">Statistical Method</th>
                <th className="p-3">PSI Score</th>
                <th className="p-3">KS Statistic</th>
                <th className="p-3">KS p-value</th>
                <th className="p-3">Threshold</th>
                <th className="p-3">Evaluation Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {reports.length > 0 ? (
                reports.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50">
                    <td className="p-3 font-mono font-semibold text-slate-900">{r.feature_name}</td>
                    <td className="p-3"><span className="badge badge-info">{r.drift_method}</span></td>
                    <td className="p-3 font-mono font-bold text-slate-800">{r.drift_score?.toFixed(4)}</td>
                    <td className="p-3 font-mono text-slate-600">{r.ks_statistic !== undefined ? r.ks_statistic : '-'}</td>
                    <td className="p-3 font-mono text-slate-600">{r.p_value !== undefined ? r.p_value : '-'}</td>
                    <td className="p-3 font-mono text-slate-500">{r.threshold?.toFixed(2)}</td>
                    <td className="p-3">{getStatusBadge(r.status)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="p-12 text-center text-slate-400">
                    <Activity className="w-8 h-8 mx-auto mb-2 opacity-40" />
                    No drift calculations found. Click "Calculate Dataset Drift" to run PSI and KS tests on live banking datasets.
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
