import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function SinglePredictionPage() {
  const { addToast } = useToastStore()
  const [useCase, setUseCase] = useState('credit_risk')
  const [features, setFeatures] = useState<Record<string, string>>({ age: '35', income: '65000', credit_score: '720', loan_amount: '250000', loan_term: '360', existing_loans: '1', debt_to_income: '0.35', previous_defaults: '0', account_balance: '45000', transaction_frequency: '25', employment_years: '8', credit_history_length: '10' })
  const [result, setResult] = useState<any>(null)

  const predict = useMutation({
    mutationFn: () => api.post('/predictions/predict', { use_case: useCase, features: Object.fromEntries(Object.entries(features).map(([k, v]) => [k, parseFloat(v) || 0])) }),
    onSuccess: (res) => { setResult(res.data.data); addToast('success', 'Prediction completed!') },
    onError: (e: any) => addToast('error', e.response?.data?.detail || 'Prediction failed'),
  })

  const explanationData = result?.explanation ? Object.entries(result.explanation).map(([k, v]: any) => ({ name: k, value: Math.abs(v), direction: v >= 0 ? 'positive' : 'negative' })) : []

  return (<div className="space-y-6">
    <h1 className="text-2xl font-bold">Single Prediction</h1>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white rounded-xl p-6 shadow-sm border">
        <h3 className="font-semibold mb-4">Input Features</h3>
        <div className="mb-4"><label className="text-xs text-gray-500">Use Case</label>
          <select value={useCase} onChange={e => setUseCase(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="credit_risk">Credit Risk</option><option value="fraud">Fraud Detection</option><option value="churn">Churn Prediction</option>
          </select></div>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(features).map(([k, v]) => (
            <div key={k}><label className="text-xs text-gray-500">{k.replace(/_/g, ' ')}</label>
              <input type="number" value={v} onChange={e => setFeatures(f => ({...f, [k]: e.target.value}))} className="w-full border rounded-lg px-3 py-2 text-sm" /></div>
          ))}
        </div>
        <button onClick={() => predict.mutate()} disabled={predict.isPending}
          className="mt-4 w-full bg-blue-600 text-white py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium">
          {predict.isPending ? 'Predicting...' : 'Run Prediction'}
        </button>
      </div>
      <div>
        {result && (<div className="space-y-4">
          <div className={`rounded-xl p-6 border-2 ${result.risk_category === 'HIGH_RISK' ? 'bg-red-50 border-red-300' : result.risk_category === 'MEDIUM_RISK' ? 'bg-yellow-50 border-yellow-300' : 'bg-green-50 border-green-300'}`}>
            <p className="text-sm text-gray-600 mb-1">Risk Assessment</p>
            <p className="text-3xl font-bold">{result.risk_category?.replace('_', ' ')}</p>
            <div className="mt-3 grid grid-cols-3 gap-3 text-sm">
              <div><span className="text-gray-500">Probability:</span><p className="font-bold">{(result.probability * 100).toFixed(1)}%</p></div>
              <div><span className="text-gray-500">Risk Score:</span><p className="font-bold">{result.risk_score}/100</p></div>
              <div><span className="text-gray-500">Model:</span><p className="font-bold">{result.model_version}</p></div>
            </div>
          </div>
          {explanationData.length > 0 && <div className="bg-white rounded-xl p-6 shadow-sm border">
            <h3 className="font-semibold mb-4">SHAP Explanation</h3>
            <ResponsiveContainer width="100%" height={250}><BarChart data={explanationData} layout="vertical"><XAxis type="number" /><YAxis type="category" dataKey="name" width={120} /><Tooltip /><Bar dataKey="value" fill="#3b82f6" /></BarChart></ResponsiveContainer>
          </div>}
        </div>)}
        {!result && <div className="bg-white rounded-xl p-12 shadow-sm border text-center text-gray-400"><p>Enter features and click "Run Prediction" to see results</p></div>}
      </div>
    </div>
  </div>)
}
