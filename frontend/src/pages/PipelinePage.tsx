import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import {
  Play, Square, RotateCcw, ArrowRight, CheckCircle2,
  Clock, AlertCircle, RefreshCw, Server, ShieldCheck,
  Terminal, Zap, Sparkles, ExternalLink
} from 'lucide-react'
import { useToastStore } from '../store/toastStore'

interface Stage {
  id: string
  name: string
  description: string
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
}

export default function PipelinePage() {
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()
  const [autoRefresh, setAutoRefresh] = useState(true)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['pipeline-status'],
    queryFn: () => api.get('/pipeline/status').then(r => r.data.data),
    refetchInterval: autoRefresh ? 2000 : false,
  })

  // Start Pipeline Mutation
  const startMutation = useMutation({
    mutationFn: () => api.post('/pipeline/start'),
    onSuccess: () => {
      addToast('success', 'MLOps pipeline started successfully')
      refetch()
    },
    onError: (err: any) => addToast('error', err.response?.data?.error?.message || 'Failed to start pipeline'),
  })

  // Stop Pipeline Mutation
  const stopMutation = useMutation({
    mutationFn: () => api.post('/pipeline/stop'),
    onSuccess: () => {
      addToast('info', 'MLOps pipeline halted')
      refetch()
    },
    onError: (err: any) => addToast('error', err.response?.data?.error?.message || 'Failed to stop pipeline'),
  })

  // Retrain Mutation
  const retrainMutation = useMutation({
    mutationFn: () => api.post('/pipeline/retrain'),
    onSuccess: () => {
      addToast('success', 'Federated retraining triggered')
      refetch()
    },
    onError: (err: any) => addToast('error', err.response?.data?.error?.message || 'Retraining failed'),
  })

  // Deploy Model Mutation
  const deployMutation = useMutation({
    mutationFn: () => api.post('/pipeline/deploy'),
    onSuccess: (res: any) => {
      addToast('success', `Model ${res.data?.data?.version || 'v2.1.0'} deployed to production`)
      refetch()
    },
    onError: (err: any) => addToast('error', err.response?.data?.error?.message || 'Deployment failed'),
  })

  // Rollback Mutation
  const rollbackMutation = useMutation({
    mutationFn: () => api.post('/pipeline/rollback'),
    onSuccess: (res: any) => {
      addToast('info', `Rolled back to version ${res.data?.data?.version || 'previous'}`)
      refetch()
    },
    onError: (err: any) => addToast('error', err.response?.data?.error?.message || 'Rollback failed'),
  })

  const stages: Stage[] = data?.stages || []
  const pipelineStatus = data?.status || 'IDLE'
  const logs: string[] = data?.logs || []

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle2 className="text-emerald-500" size={20} />
      case 'RUNNING':
        return <RefreshCw className="text-blue-500 animate-spin" size={20} />
      case 'FAILED':
        return <AlertCircle className="text-rose-500" size={20} />
      default:
        return <Clock className="text-gray-400" size={20} />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800">Completed</span>
      case 'RUNNING':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 animate-pulse">Running</span>
      case 'FAILED':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-rose-100 text-rose-800">Failed</span>
      default:
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-gray-100 text-gray-600">Pending</span>
    }
  }

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-800">MLOps Pipeline Orchestrator</h1>
            <span className={`px-3 py-1 text-xs font-bold rounded-full ${
              pipelineStatus === 'RUNNING' ? 'bg-blue-100 text-blue-700 animate-pulse' :
              pipelineStatus === 'COMPLETED' ? 'bg-emerald-100 text-emerald-700' :
              pipelineStatus === 'FAILED' ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-700'
            }`}>
              {pipelineStatus}
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Visual privacy-preserving lifecycle from multi-bank ingestion to live serving and drift monitoring.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => startMutation.mutate()}
            disabled={pipelineStatus === 'RUNNING' || startMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl font-medium shadow-sm transition-all"
          >
            <Play size={16} />
            Start Pipeline
          </button>

          <button
            onClick={() => stopMutation.mutate()}
            disabled={pipelineStatus !== 'RUNNING' || stopMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded-xl font-medium shadow-sm transition-all"
          >
            <Square size={16} />
            Stop Pipeline
          </button>

          <button
            onClick={() => retrainMutation.mutate()}
            disabled={pipelineStatus === 'RUNNING' || retrainMutation.isPending}
            className="flex items-center gap-2 px-3.5 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-xl font-medium transition-all"
          >
            <RotateCcw size={16} />
            Retrain
          </button>

          <button
            onClick={() => deployMutation.mutate()}
            disabled={deployMutation.isPending}
            className="flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-medium shadow-sm transition-all"
          >
            <Zap size={16} />
            Deploy Model
          </button>

          <button
            onClick={() => rollbackMutation.mutate()}
            disabled={rollbackMutation.isPending}
            className="flex items-center gap-2 px-3.5 py-2 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 rounded-xl font-medium transition-all"
          >
            <RefreshCw size={16} />
            Rollback
          </button>
        </div>
      </div>

      {/* Visual Pipeline Graph */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Pipeline Execution Stages</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {stages.map((stage, idx) => (
            <div
              key={stage.id}
              className={`p-4 rounded-xl border transition-all ${
                stage.status === 'RUNNING'
                  ? 'border-blue-500 bg-blue-50/40 ring-2 ring-blue-500/20'
                  : stage.status === 'COMPLETED'
                  ? 'border-emerald-200 bg-emerald-50/20'
                  : stage.status === 'FAILED'
                  ? 'border-rose-300 bg-rose-50/20'
                  : 'border-slate-200 bg-slate-50/50'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-400">#{idx + 1}</span>
                  {getStatusIcon(stage.status)}
                </div>
                {getStatusBadge(stage.status)}
              </div>
              <h3 className="font-semibold text-slate-800 text-sm mt-3">{stage.name}</h3>
              <p className="text-xs text-slate-500 mt-1 line-clamp-2">{stage.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Real-Time Terminal Logs */}
      <div className="bg-slate-900 text-slate-100 p-6 rounded-2xl shadow-lg border border-slate-800">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <Terminal size={18} className="text-emerald-400" />
            <h3 className="font-mono text-sm font-semibold">Live MLOps Pipeline Event Stream</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">Backend SSE Sync: Active</span>
        </div>
        <div className="font-mono text-xs space-y-1.5 max-h-64 overflow-y-auto pr-2 scrollbar-thin">
          {logs.map((log, i) => (
            <div key={i} className="flex gap-2 text-slate-300 hover:bg-slate-800/50 py-0.5 px-1 rounded">
              <span className="text-emerald-400 select-none">&gt;</span>
              <span>{log}</span>
            </div>
          ))}
          {logs.length === 0 && <p className="text-slate-500 italic">Awaiting pipeline trigger...</p>}
        </div>
      </div>
    </div>
  )
}
