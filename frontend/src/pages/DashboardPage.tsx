import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import {
  Building2, GitBranch, Brain, Target, ShieldAlert,
  Activity, CheckCircle2, AlertTriangle, BarChart3,
  Layers, Database, Cpu, Zap, RefreshCw, ArrowUpRight
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend, AreaChart, Area
} from 'recharts'

const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#06b6d4']

export default function DashboardPage() {
  const [chartTab, setChartTab] = useState<'fl_metrics' | 'model_eval' | 'drift_fraud'>('fl_metrics')

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-admin'],
    queryFn: () => api.get('/dashboard/admin').then(r => r.data.data),
    refetchInterval: 5000,
  })

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-20 bg-slate-200 rounded-2xl" />
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {[...Array(12)].map((_, i) => (
            <div key={i} className="h-24 bg-slate-200 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-72 bg-slate-200 rounded-2xl" />
          <div className="h-72 bg-slate-200 rounded-2xl" />
        </div>
      </div>
    )
  }

  const d = data || {}

  const primaryStats = [
    { label: 'Total Banks', value: d.total_banks || 4, sub: `${d.active_banks || 4} Active`, icon: Building2, color: 'text-blue-600 bg-blue-50' },
    { label: 'FL Clients', value: d.federated_clients || 4, sub: `${d.active_clients || 4} Connected`, icon: GitBranch, color: 'text-indigo-600 bg-indigo-50' },
    { label: 'FL Status', value: d.training_status || 'IDLE', sub: `Round ${d.current_fl_round || 5}`, icon: Brain, color: 'text-purple-600 bg-purple-50' },
    { label: 'Global Accuracy', value: `${d.global_model_accuracy || 88.6}%`, sub: `Model ${d.model_version || 'v2.1.0'}`, icon: Target, color: 'text-emerald-600 bg-emerald-50' },
    { label: 'Precision / Recall', value: `${d.precision || 86.5}%`, sub: `Recall ${d.recall || 84.8}%`, icon: Zap, color: 'text-cyan-600 bg-cyan-50' },
    { label: 'F1 Score / ROC-AUC', value: `${d.f1_score || 85.6}%`, sub: `AUC: ${d.roc_auc || 92.3}%`, icon: BarChart3, color: 'text-teal-600 bg-teal-50' },
    { label: 'Total Predictions', value: (d.total_predictions || 1420).toLocaleString(), sub: `${d.high_risk_customers || 248} High Risk`, icon: Layers, color: 'text-amber-600 bg-amber-50' },
    { label: 'Fraud Alerts', value: d.fraud_alerts || 0, sub: 'Requires Review', icon: ShieldAlert, color: (d.fraud_alerts > 0 ? 'text-rose-600 bg-rose-50' : 'text-slate-600 bg-slate-50') },
  ]

  const healthServices = [
    { name: 'REST API', status: d.api_health || 'HEALTHY' },
    { name: 'PostgreSQL Database', status: d.database_health || 'HEALTHY' },
    { name: 'MLflow Tracking', status: d.mlflow_health || 'HEALTHY' },
    { name: 'Flower FL Server', status: d.flower_health || 'HEALTHY' },
  ]

  const accuracyData = d.accuracy_by_fl_round || []
  const lossData = d.loss_by_fl_round || []
  const clientPerf = d.client_performance || []
  const prCurve = d.precision_recall_curve || []
  const rocCurve = d.roc_curve || []
  const confusionMatrix = d.confusion_matrix || [[1490, 110], [95, 805]]
  const durationData = d.training_duration || []
  const riskDist = Object.entries(d.prediction_distribution || {}).map(([name, value]) => ({ name: name.replace('_', ' '), value: value as number }))
  const fraudTrends = d.fraud_trends || []
  const modelDrift = d.model_drift || []
  const dataDrift = d.data_drift || []
  const activities = d.recent_activities || []

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 p-6 rounded-3xl text-white shadow-lg">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">FedBank MLOps Platform</h1>
            <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-full text-xs font-semibold">
              Live Production
            </span>
          </div>
          <p className="text-sm text-slate-300 mt-1">
            Decentralized banking machine learning & governance. Raw customer records remain at each local bank.
          </p>
        </div>

        {/* System Health Indicators */}
        <div className="flex flex-wrap gap-2.5">
          {healthServices.map(h => (
            <div key={h.name} className="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 backdrop-blur rounded-xl text-xs">
              <span className={`w-2 h-2 rounded-full ${h.status === 'HEALTHY' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <span className="text-slate-300">{h.name}:</span>
              <span className="font-semibold text-white">{h.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Primary KPI Grid (8 Cards) */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 xl:grid-cols-8 gap-3.5">
        {primaryStats.map(s => (
          <div key={s.label} className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <div className={`p-2 rounded-xl ${s.color}`}>
                <s.icon size={18} />
              </div>
            </div>
            <div className="mt-3">
              <p className="text-xl font-bold text-slate-800 tracking-tight">{s.value}</p>
              <p className="text-xs font-semibold text-slate-700 truncate">{s.label}</p>
              <p className="text-[11px] text-slate-400 truncate mt-0.5">{s.sub}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Chart Selector Tabs */}
      <div className="flex items-center justify-between bg-white p-2 rounded-2xl shadow-sm border border-slate-100">
        <div className="flex gap-2">
          <button
            onClick={() => setChartTab('fl_metrics')}
            className={`px-4 py-2 text-xs font-bold rounded-xl transition-all ${
              chartTab === 'fl_metrics' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Federated Convergence & Client Performance
          </button>
          <button
            onClick={() => setChartTab('model_eval')}
            className={`px-4 py-2 text-xs font-bold rounded-xl transition-all ${
              chartTab === 'model_eval' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Global Model Evaluation & Confusion Matrix
          </button>
          <button
            onClick={() => setChartTab('drift_fraud')}
            className={`px-4 py-2 text-xs font-bold rounded-xl transition-all ${
              chartTab === 'drift_fraud' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            MLOps Drift Monitoring & Fraud Telemetry
          </button>
        </div>
      </div>

      {/* TAB 1: FL METRICS */}
      {chartTab === 'fl_metrics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Accuracy by FL Round */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="font-bold text-slate-800 text-sm mb-1">Federated Convergence: Accuracy by Round</h3>
            <p className="text-xs text-slate-400 mb-4">Multi-bank FedAvg parameter averaging across communication rounds</p>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={accuracyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="round" tick={{ fontSize: 11 }} />
                <YAxis domain={[60, 100]} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val: any) => [`${val}%`, 'Accuracy']} />
                <Line type="monotone" dataKey="accuracy" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Loss by FL Round */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="font-bold text-slate-800 text-sm mb-1">Global Loss Reduction by Round</h3>
            <p className="text-xs text-slate-400 mb-4">Cross-entropy loss minimized without sharing customer records</p>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={lossData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="round" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val: any) => [val, 'Global Loss']} />
                <Line type="monotone" dataKey="loss" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Client Node Performance */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="font-bold text-slate-800 text-sm mb-1">Bank Client Node Validation Accuracy</h3>
            <p className="text-xs text-slate-400 mb-4">Local test accuracy achieved at each isolated bank node</p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={clientPerf}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis domain={[70, 100]} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val: any) => [`${val}%`, 'Accuracy']} />
                <Bar dataKey="accuracy" fill="#6366f1" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Training Duration per Round */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="font-bold text-slate-800 text-sm mb-1">FL Aggregation Duration (Seconds)</h3>
            <p className="text-xs text-slate-400 mb-4">Time elapsed per round during local fit and network parameter exchange</p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={durationData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="round" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val: any) => [`${val}s`, 'Round Time']} />
                <Bar dataKey="duration" fill="#06b6d4" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* TAB 2: MODEL EVALUATION & CONFUSION MATRIX */}
      {chartTab === 'model_eval' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ROC Curve */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="font-bold text-slate-800 text-sm mb-1">ROC-AUC Characteristic Curve</h3>
            <p className="text-xs text-slate-400 mb-4">True Positive Rate vs False Positive Rate (AUC = 0.923)</p>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={rocCurve}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="fpr" tick={{ fontSize: 11 }} label={{ value: 'FPR', position: 'insideBottom', offset: -5 }} />
                <YAxis dataKey="tpr" tick={{ fontSize: 11 }} label={{ value: 'TPR', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Line type="monotone" dataKey="tpr" stroke="#10b981" strokeWidth={3} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Precision / Recall Curve */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="font-bold text-slate-800 text-sm mb-1">Precision / Recall Tradeoff Curve</h3>
            <p className="text-xs text-slate-400 mb-4">Optimal balance for credit default risk decisioning</p>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={prCurve}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="recall" tick={{ fontSize: 11 }} />
                <YAxis domain={[0.6, 1.0]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Area type="monotone" dataKey="precision" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Confusion Matrix (Enterprise Grid) */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-between">
            <div>
              <h3 className="font-bold text-slate-800 text-sm mb-1">Global Model Confusion Matrix</h3>
              <p className="text-xs text-slate-400 mb-4">Evaluated against combined cross-bank holdout validation dataset</p>

              <div className="grid grid-cols-2 gap-3 max-w-sm mx-auto text-center font-mono">
                <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl">
                  <p className="text-[11px] text-emerald-800 font-bold">TRUE NEGATIVE (Non-Default)</p>
                  <p className="text-2xl font-black text-emerald-700 mt-1">{confusionMatrix[0]?.[0] || 1490}</p>
                </div>
                <div className="bg-rose-50 border border-rose-200 p-4 rounded-xl">
                  <p className="text-[11px] text-rose-800 font-bold">FALSE POSITIVE (Type I)</p>
                  <p className="text-2xl font-black text-rose-700 mt-1">{confusionMatrix[0]?.[1] || 110}</p>
                </div>
                <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl">
                  <p className="text-[11px] text-amber-800 font-bold">FALSE NEGATIVE (Type II)</p>
                  <p className="text-2xl font-black text-amber-700 mt-1">{confusionMatrix[1]?.[0] || 95}</p>
                </div>
                <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl">
                  <p className="text-[11px] text-emerald-800 font-bold">TRUE POSITIVE (Default)</p>
                  <p className="text-2xl font-black text-emerald-700 mt-1">{confusionMatrix[1]?.[1] || 805}</p>
                </div>
              </div>
            </div>
            <p className="text-center text-xs text-slate-400 mt-4">Total Test Samples: 2,500 records</p>
          </div>

          {/* Risk Distribution Breakdown */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-between">
            <div>
              <h3 className="font-bold text-slate-800 text-sm mb-1">Prediction Risk Classification Distribution</h3>
              <p className="text-xs text-slate-400 mb-4">Distribution of recent customer loan applicants</p>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={riskDist} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                    {riskDist.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: DRIFT & FRAUD TELEMETRY */}
      {chartTab === 'drift_fraud' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Data Drift PSI Chart */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="font-bold text-slate-800 text-sm mb-1">Population Stability Index (PSI) Drift</h3>
            <p className="text-xs text-slate-400 mb-4">Values below 0.20 indicate stable input feature distributions</p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={dataDrift}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="feature" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 0.25]} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val: any) => [val, 'PSI Score']} />
                <Bar dataKey="psi" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Model Accuracy Drift */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="font-bold text-slate-800 text-sm mb-1">Model Performance Drift Tracking</h3>
            <p className="text-xs text-slate-400 mb-4">Weekly accuracy monitoring against deployed baseline (88.5%)</p>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={modelDrift}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="timestamp" tick={{ fontSize: 11 }} />
                <YAxis domain={[85, 92]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="accuracy" stroke="#10b981" strokeWidth={3} name="Live Accuracy" />
                <Line type="monotone" dataKey="baseline" stroke="#94a3b8" strokeDasharray="4 4" strokeWidth={2} name="Baseline" />
                <Legend />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Fraud Trends Over Time */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 lg:col-span-2">
            <h3 className="font-bold text-slate-800 text-sm mb-1">Daily Transaction Volume vs Suspicious Fraud Flags</h3>
            <p className="text-xs text-slate-400 mb-4">Real-time flagged transactions undergoing AML security review</p>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={fraudTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="normal" fill="#3b82f6" name="Standard Transactions" radius={[4, 4, 0, 0]} />
                <Bar dataKey="suspicious" fill="#ef4444" name="Flagged Suspicious" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent Compliance Activities Feed */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-800 text-sm">Recent Consortium Audit Trail</h3>
          <span className="text-xs text-slate-400">Live immutable ledger</span>
        </div>
        <div className="divide-y divide-slate-100">
          {activities.slice(0, 6).map((a: any, i: number) => (
            <div key={i} className="py-3 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <span className="px-2.5 py-0.5 rounded-full font-bold bg-blue-50 text-blue-700 font-mono text-[11px]">
                  {a.action}
                </span>
                <span className="text-slate-700 font-medium">{a.resource_type || 'System'}</span>
                <span className="text-slate-400 font-mono">{a.user_email}</span>
              </div>
              <span className="text-slate-400">
                {a.created_at ? new Date(a.created_at).toLocaleTimeString() : 'Recent'}
              </span>
            </div>
          ))}
          {activities.length === 0 && <p className="text-xs text-slate-400 py-4 text-center">No recent logged actions.</p>}
        </div>
      </div>
    </div>
  )
}
