import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import api from '../services/api'
import {
  FileText, Download, CheckCircle, Clock, Sparkles
} from 'lucide-react'
import { useToastStore } from '../store/toastStore'

export default function ReportsPage() {
  const { addToast } = useToastStore()
  const [reportType, setReportType] = useState('TRAINING')
  const [format, setFormat] = useState('CSV')

  const { data: reportTypes } = useQuery({
    queryKey: ['reports-list'],
    queryFn: () => api.get('/reports').then(r => r.data.data),
  })

  const generateMutation = useMutation({
    mutationFn: () => api.post(`/reports/generate?report_type=${reportType}&format=${format}`),
    onSuccess: (res: any) => {
      addToast('success', `${reportType} Report generated successfully! (${res.data.data?.rows || 0} records)`)
      // Trigger download
      const path = res.data.data?.file_path
      if (path) {
        window.open(`${api.defaults.baseURL}/reports/generate?report_type=${reportType}&format=${format}`, '_blank')
      }
    },
    onError: () => addToast('error', 'Report generation failed'),
  })

  const reports: any[] = reportTypes || [
    { type: 'TRAINING', name: 'Federated Training Report', description: 'FL rounds, client contributions, and global convergence metrics' },
    { type: 'MODEL_PERFORMANCE', name: 'Model Benchmark & Evaluation Report', description: 'Cross-bank ROC-AUC, F1, precision, and recall comparisons' },
    { type: 'DRIFT', name: 'Population & Data Drift Report', description: 'PSI calculations, feature distribution shifts, and covariate checks' },
    { type: 'AUDIT', name: 'Enterprise Regulatory Audit Report', description: 'Full immutable trail of logins, training runs, deployments, and alerts' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Compliance & Performance Reports</h1>
          <p className="text-sm text-slate-500 mt-1">
            Generate and export signed audit trails, model validation certificates, and federated performance digests.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reports.map((r: any) => (
          <div key={r.type} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl">
                  <FileText size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-slate-800 text-sm">{r.name}</h3>
                  <span className="text-[10px] font-mono uppercase bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-semibold">
                    {r.type}
                  </span>
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-2">{r.description}</p>
            </div>

            <div className="flex items-center justify-between pt-6 border-t border-slate-100 mt-4">
              <span className="text-xs text-slate-400">Formats: CSV / PDF</span>
              <button
                onClick={() => {
                  setReportType(r.type)
                  generateMutation.mutate()
                }}
                disabled={generateMutation.isPending}
                className="flex items-center gap-2 px-3.5 py-1.5 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
              >
                <Download size={14} />
                Export CSV
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
