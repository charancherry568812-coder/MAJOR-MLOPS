import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import {
  ShieldAlert, AlertTriangle, CheckCircle2, XCircle, Search,
  Filter, ArrowUpDown, ShieldCheck, DollarSign, Activity, FileText, Send
} from 'lucide-react'
import { useToastStore } from '../store/toastStore'

export default function FraudPage() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()

  // Tab State
  const [activeTab, setActiveTab] = useState<'alerts' | 'score' | 'transactions'>('alerts')
  const [selectedAlert, setSelectedAlert] = useState<any>(null)
  const [resolutionNotes, setResolutionNotes] = useState('')
  const [resolveAction, setResolveAction] = useState<'RESOLVED' | 'REJECTED'>('RESOLVED')

  // Transaction Scoring Form State
  const [scoreForm, setScoreForm] = useState({
    customer_id: 'CUST-10492',
    amount: 8500,
    transaction_type: 'TRANSFER',
    merchant_category: 'International Wire',
    velocity_score: 82,
    amount_deviation: 4.5,
    num_devices: 3,
    account_age_months: 18,
  })
  const [scoreResult, setScoreResult] = useState<any>(null)

  // Fetch Fraud Summary
  const { data: summary } = useQuery({
    queryKey: ['fraud-summary'],
    queryFn: () => api.get('/fraud/summary').then(r => r.data),
  })

  // Fetch Fraud Alerts
  const { data: alertsData, refetch: refetchAlerts } = useQuery({
    queryKey: ['fraud-alerts'],
    queryFn: () => api.get('/fraud/alerts?page_size=50').then(r => r.data.data),
  })

  // Fetch Scored Transactions
  const { data: txnsData } = useQuery({
    queryKey: ['fraud-transactions'],
    queryFn: () => api.get('/fraud/transactions?page_size=50').then(r => r.data.data),
  })

  // Score Transaction Mutation
  const scoreMutation = useMutation({
    mutationFn: (payload: any) => api.post('/fraud/score-transaction', payload),
    onSuccess: (res: any) => {
      setScoreResult(res.data)
      addToast('success', `Transaction scored: ${res.data.risk_level} risk detected`)
      queryClient.invalidateQueries({ queryKey: ['fraud-summary'] })
      queryClient.invalidateQueries({ queryKey: ['fraud-alerts'] })
      queryClient.invalidateQueries({ queryKey: ['fraud-transactions'] })
    },
    onError: (err: any) => addToast('error', 'Scoring evaluation failed'),
  })

  // Resolve Alert Mutation
  const resolveMutation = useMutation({
    mutationFn: ({ id, notes, action }: { id: string; notes: string; action: string }) =>
      api.put(`/fraud/alerts/${id}/resolve`, { resolution_notes: notes, action }),
    onSuccess: () => {
      addToast('success', `Alert marked as ${resolveAction}`)
      setSelectedAlert(null)
      setResolutionNotes('')
      refetchAlerts()
      queryClient.invalidateQueries({ queryKey: ['fraud-summary'] })
    },
    onError: (err: any) => addToast('error', 'Failed to resolve alert'),
  })

  const alerts = alertsData?.items || []
  const transactions = txnsData?.items || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-800">Fraud Detection & Anti-Money Laundering</h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-rose-100 text-rose-800">
              Live Monitoring
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Real-time transaction risk scoring, behavioral velocity tracking, and centralized alert management.
          </p>
        </div>

        {/* Tab Buttons */}
        <div className="flex bg-slate-100 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab('alerts')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'alerts' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Alert Queue ({summary?.open_alerts || 0})
          </button>
          <button
            onClick={() => setActiveTab('score')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'score' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Transaction Scorer
          </button>
          <button
            onClick={() => setActiveTab('transactions')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'transactions' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All Transactions
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs text-slate-500 font-medium">Total Transactions</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{summary?.total_transactions || 0}</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs text-slate-500 font-medium">Suspicious Flagged</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{summary?.suspicious_transactions || 0}</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs text-slate-500 font-medium">Fraud Probability Rate</p>
          <p className="text-2xl font-bold text-rose-600 mt-1">{((summary?.fraud_rate || 0) * 100).toFixed(2)}%</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs text-slate-500 font-medium">Open Security Alerts</p>
          <p className="text-2xl font-bold text-rose-700 mt-1">{summary?.open_alerts || 0}</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
          <p className="text-xs text-slate-500 font-medium">Resolved Alerts</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{summary?.resolved_alerts || 0}</p>
        </div>
      </div>

      {/* TAB 1: ALERTS QUEUE */}
      {activeTab === 'alerts' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-semibold text-slate-800 text-sm">Active & Resolved Suspicious Alerts</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold text-slate-500 border-b border-slate-100">
                <tr>
                  <th className="p-4">Alert Code</th>
                  <th className="p-4">Customer / Bank</th>
                  <th className="p-4">Fraud Prob</th>
                  <th className="p-4">Severity</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Reason</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {alerts.map((a: any) => (
                  <tr key={a.id} className="hover:bg-slate-50/50">
                    <td className="p-4 font-mono font-semibold text-slate-800">{a.alert_code}</td>
                    <td className="p-4">
                      <p className="font-medium text-slate-800">{a.customer_id}</p>
                      <p className="text-xs text-slate-400">{a.bank_name}</p>
                    </td>
                    <td className="p-4">
                      <span className="font-semibold text-slate-700">{(a.fraud_probability * 100).toFixed(1)}%</span>
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        a.severity === 'CRITICAL' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {a.severity}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        a.status === 'OPEN' ? 'bg-rose-50 text-rose-700 border border-rose-200' :
                        a.status === 'RESOLVED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                        'bg-slate-100 text-slate-600'
                      }`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="p-4 max-w-xs truncate text-xs text-slate-600">{a.flag_reason}</td>
                    <td className="p-4 text-right">
                      {a.status === 'OPEN' ? (
                        <button
                          onClick={() => { setSelectedAlert(a); setResolutionNotes('') }}
                          className="px-3 py-1 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-medium"
                        >
                          Review & Resolve
                        </button>
                      ) : (
                        <span className="text-xs text-slate-400">Resolved</span>
                      )}
                    </td>
                  </tr>
                ))}
                {alerts.length === 0 && (
                  <tr><td colSpan={7} className="p-8 text-center text-slate-400">No fraud alerts detected.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: LIVE TRANSACTION SCORER */}
      {activeTab === 'score' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">Simulate & Score Banking Transaction</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-600">Customer ID</label>
                  <input
                    type="text"
                    value={scoreForm.customer_id}
                    onChange={e => setScoreForm({ ...scoreForm, customer_id: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-600">Amount ($ USD)</label>
                  <input
                    type="number"
                    value={scoreForm.amount}
                    onChange={e => setScoreForm({ ...scoreForm, amount: parseFloat(e.target.value) || 0 })}
                    className="w-full mt-1 px-3 py-2 border rounded-xl text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-600">Transaction Type</label>
                  <select
                    value={scoreForm.transaction_type}
                    onChange={e => setScoreForm({ ...scoreForm, transaction_type: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-xl text-sm"
                  >
                    <option value="TRANSFER">WIRE TRANSFER</option>
                    <option value="PAYMENT">MERCHANT PAYMENT</option>
                    <option value="WITHDRAWAL">ATM WITHDRAWAL</option>
                    <option value="DEPOSIT">ONLINE DEPOSIT</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-600">Merchant Category</label>
                  <input
                    type="text"
                    value={scoreForm.merchant_category}
                    onChange={e => setScoreForm({ ...scoreForm, merchant_category: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-xl text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-600">Velocity (0-100)</label>
                  <input
                    type="number"
                    value={scoreForm.velocity_score}
                    onChange={e => setScoreForm({ ...scoreForm, velocity_score: parseFloat(e.target.value) || 0 })}
                    className="w-full mt-1 px-3 py-2 border rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-600">Amount Deviation (x)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={scoreForm.amount_deviation}
                    onChange={e => setScoreForm({ ...scoreForm, amount_deviation: parseFloat(e.target.value) || 0 })}
                    className="w-full mt-1 px-3 py-2 border rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-600">Num Devices</label>
                  <input
                    type="number"
                    value={scoreForm.num_devices}
                    onChange={e => setScoreForm({ ...scoreForm, num_devices: parseInt(e.target.value) || 1 })}
                    className="w-full mt-1 px-3 py-2 border rounded-xl text-sm"
                  />
                </div>
              </div>

              <button
                onClick={() => scoreMutation.mutate(scoreForm)}
                disabled={scoreMutation.isPending}
                className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold shadow-sm transition-all"
              >
                <Send size={16} />
                Evaluate Fraud Probability
              </button>
            </div>
          </div>

          {/* Scoring Results Card */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-800 mb-4">ML Inference Assessment</h2>
              {scoreResult ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 rounded-xl border bg-slate-50">
                    <div>
                      <p className="text-xs text-slate-500">Risk Classification</p>
                      <p className={`text-xl font-bold ${
                        scoreResult.risk_level === 'HIGH' ? 'text-rose-600' :
                        scoreResult.risk_level === 'MEDIUM' ? 'text-amber-600' : 'text-emerald-600'
                      }`}>
                        {scoreResult.risk_level} RISK
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-slate-500">Fraud Probability</p>
                      <p className="text-2xl font-bold text-slate-800">{(scoreResult.fraud_probability * 100).toFixed(1)}%</p>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-100 bg-white space-y-2">
                    <p className="text-xs font-semibold text-slate-700">Security Recommendation</p>
                    <p className="text-xs text-slate-600">{scoreResult.recommendation}</p>
                    {scoreResult.is_flagged && (
                      <p className="text-xs text-rose-600 font-medium">Trigger: {scoreResult.flag_reason}</p>
                    )}
                  </div>

                  <div>
                    <p className="text-xs font-semibold text-slate-700 mb-2">Risk Vector Weights</p>
                    <div className="space-y-1.5">
                      {Object.entries(scoreResult.feature_contributions || {}).map(([feat, val]: any) => (
                        <div key={feat} className="flex items-center justify-between text-xs">
                          <span className="text-slate-600">{feat}</span>
                          <span className="font-mono font-medium text-slate-800">{(val * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-16 text-center text-slate-400">
                  <ShieldCheck size={48} className="mx-auto mb-2 opacity-40" />
                  <p className="text-sm">Enter transaction parameters and run evaluation to see fraud probability breakdown.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: ALL TRANSACTIONS */}
      {activeTab === 'transactions' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="p-4 border-b border-slate-100">
            <h2 className="font-semibold text-slate-800 text-sm">Scored Transactions Audit</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold text-slate-500 border-b border-slate-100">
                <tr>
                  <th className="p-4">Reference</th>
                  <th className="p-4">Customer</th>
                  <th className="p-4">Bank</th>
                  <th className="p-4">Amount</th>
                  <th className="p-4">Type</th>
                  <th className="p-4">Risk Level</th>
                  <th className="p-4">Fraud Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {transactions.map((t: any) => (
                  <tr key={t.id} className="hover:bg-slate-50/50">
                    <td className="p-4 font-mono font-medium text-slate-800">{t.transaction_reference}</td>
                    <td className="p-4">{t.customer_id}</td>
                    <td className="p-4">{t.bank_name}</td>
                    <td className="p-4 font-semibold">${t.amount.toLocaleString()}</td>
                    <td className="p-4 text-xs text-slate-600">{t.transaction_type}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        t.risk_level === 'HIGH' ? 'bg-rose-100 text-rose-800' :
                        t.risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {t.risk_level}
                      </span>
                    </td>
                    <td className="p-4 font-mono">{(t.fraud_score * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* RESOLUTION MODAL */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <h3 className="font-bold text-lg text-slate-800">Resolve Fraud Alert: {selectedAlert.alert_code}</h3>
            <p className="text-xs text-slate-500">Reason: {selectedAlert.flag_reason}</p>

            <div>
              <label className="text-xs font-semibold text-slate-700">Resolution Decision</label>
              <div className="flex gap-4 mt-1">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="radio"
                    name="decision"
                    value="RESOLVED"
                    checked={resolveAction === 'RESOLVED'}
                    onChange={() => setResolveAction('RESOLVED')}
                  />
                  Resolve & Clear (Verified with cardholder)
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="radio"
                    name="decision"
                    value="REJECTED"
                    checked={resolveAction === 'REJECTED'}
                    onChange={() => setResolveAction('REJECTED')}
                  />
                  Reject & Dismiss (False positive)
                </label>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700">Investigation & Resolution Notes</label>
              <textarea
                value={resolutionNotes}
                onChange={e => setResolutionNotes(e.target.value)}
                placeholder="Enter audit verification details..."
                className="w-full mt-1 p-3 border rounded-xl text-sm h-24"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setSelectedAlert(null)}
                className="px-4 py-2 border rounded-xl text-sm font-medium hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={() => resolveMutation.mutate({ id: selectedAlert.id, notes: resolutionNotes, action: resolveAction })}
                disabled={resolveMutation.isPending || !resolutionNotes}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold disabled:opacity-50"
              >
                Submit Resolution
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
