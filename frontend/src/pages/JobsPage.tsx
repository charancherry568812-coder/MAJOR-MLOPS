import { useState, useEffect } from 'react'
import {
  Cpu, Play, CheckCircle2, AlertCircle, Clock, RefreshCw,
  Layers, Terminal, Check
} from 'lucide-react'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [triggering, setTriggering] = useState(false)
  const { addToast } = useToastStore()

  useEffect(() => {
    fetchJobs()
    const interval = setInterval(fetchJobs, 3000)
    return () => clearInterval(interval)
  }, [])

  const fetchJobs = async () => {
    try {
      const res = await api.get('/jobs?page_size=25')
      setJobs(res.data.data.items || [])
    } catch (err) {
      // ignore background poll error
    }
  }

  const handleTriggerTask = async () => {
    try {
      setTriggering(true)
      const res = await api.post('/jobs/trigger-sample-task?title=Federated%20Dataset%20Audit%20Batch')
      addToast('success', `Async Job #${res.data.data.job_id.slice(0, 8)} dispatched to worker queue!`)
      fetchJobs()
    } catch (err) {
      addToast('error', 'Failed to dispatch async job')
    } finally {
      setTriggering(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            ⚡ <span>Async Background Jobs & Task Engine</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Thread-pool worker queue for long-running federated rounds, model retraining, and asynchronous batch evaluations.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleTriggerTask}
            disabled={triggering}
            className="btn-primary flex items-center gap-2 text-xs"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {triggering ? 'Dispatching...' : 'Dispatch Worker Job'}
          </button>
          <button onClick={fetchJobs} className="btn-secondary flex items-center gap-2 text-xs">
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Jobs List Card */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="p-3">Job ID</th>
                <th className="p-3">Task Title</th>
                <th className="p-3">Type</th>
                <th className="p-3">Progress</th>
                <th className="p-3">Current Step</th>
                <th className="p-3">Status</th>
                <th className="p-3">Dispatched At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {jobs.length > 0 ? (
                jobs.map((j) => (
                  <tr key={j.id} className="hover:bg-slate-50">
                    <td className="p-3 font-mono font-medium text-slate-800">{j.id.slice(0, 8)}...</td>
                    <td className="p-3 font-semibold text-slate-900">{j.title}</td>
                    <td className="p-3"><span className="badge badge-info">{j.job_type}</span></td>
                    <td className="p-3 w-44">
                      <div className="flex items-center gap-2">
                        <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full transition-all duration-300 ${
                              j.status === 'COMPLETED' ? 'bg-emerald-500' : j.status === 'FAILED' ? 'bg-rose-500' : 'bg-blue-600'
                            }`}
                            style={{ width: `${j.progress_percent}%` }}
                          />
                        </div>
                        <span className="font-mono text-[10px] text-slate-600">{j.progress_percent.toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="p-3 text-slate-600 truncate max-w-xs">{j.current_step}</td>
                    <td className="p-3">
                      <span className={`badge ${j.status === 'COMPLETED' ? 'badge-success' : j.status === 'RUNNING' ? 'badge-warning' : j.status === 'FAILED' ? 'badge-danger' : 'badge-info'}`}>
                        {j.status}
                      </span>
                    </td>
                    <td className="p-3 text-slate-400">{j.created_at ? new Date(j.created_at).toLocaleTimeString() : '-'}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="p-12 text-center text-slate-400">
                    <Layers className="w-8 h-8 mx-auto mb-2 opacity-40" />
                    No active or historical background tasks found. Click "Dispatch Worker Job" to initiate a background worker task.
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
