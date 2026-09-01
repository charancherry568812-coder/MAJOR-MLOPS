import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
export default function SystemHealthPage() {
  const { data } = useQuery({ queryKey: ['system-health'], queryFn: () => api.get('/monitoring/system').then(r => r.data.data), refetchInterval: 5000 })
  const d = data || {}
  const pieData = [{ name: 'CPU Used', value: d.cpu_percent || 0 }, { name: 'CPU Free', value: 100 - (d.cpu_percent || 0) }]
  const memData = [{ name: 'Memory Used', value: d.memory_percent || 0 }, { name: 'Memory Free', value: 100 - (d.memory_percent || 0) }]
  return (<div className="space-y-6"><h1 className="text-2xl font-bold">System Health</h1>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[['CPU', `${d.cpu_percent?.toFixed(1) || 0}%`], ['Memory', `${d.memory_percent?.toFixed(1) || 0}%`], ['Disk', `${d.disk_percent?.toFixed(1) || 0}%`], ['Requests', d.request_count || 0]].map(([l, v]) =>
        <div key={l as string} className="bg-white rounded-xl p-5 shadow-sm border text-center"><p className="text-3xl font-bold text-blue-600">{v}</p><p className="text-sm text-gray-500">{l}</p></div>)}
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {[['CPU Usage', pieData], ['Memory Usage', memData]].map(([title, pd]) => (
        <div key={title as string} className="bg-white rounded-xl p-6 shadow-sm border"><h3 className="font-semibold mb-4">{title as string}</h3>
          <ResponsiveContainer width="100%" height={200}><PieChart><Pie data={pd as any} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label>
            {(pd as any[]).map((_: any, i: number) => <Cell key={i} fill={COLORS[i]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></div>))}
    </div>
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      <h3 className="font-semibold mb-3">System Information</h3>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div><span className="text-gray-500">Platform:</span> {d.platform}</div>
        <div><span className="text-gray-500">Python:</span> {d.python_version}</div>
        <div><span className="text-gray-500">Total Memory:</span> {d.memory_total_gb} GB</div>
        <div><span className="text-gray-500">Total Disk:</span> {d.disk_total_gb} GB</div>
      </div></div></div>)
}
