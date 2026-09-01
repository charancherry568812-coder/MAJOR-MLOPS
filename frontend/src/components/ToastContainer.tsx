/** Toast notification display component. */
import { useToastStore } from '../store/toastStore'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'

const ICONS = { success: CheckCircle, error: AlertCircle, info: Info, warning: AlertTriangle }
const COLORS = { success: 'bg-green-50 border-green-500 text-green-800', error: 'bg-red-50 border-red-500 text-red-800',
  info: 'bg-blue-50 border-blue-500 text-blue-800', warning: 'bg-yellow-50 border-yellow-500 text-yellow-800' }

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore()
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map((t) => {
        const Icon = ICONS[t.type]
        return (
          <div key={t.id} className={`flex items-center gap-3 px-4 py-3 rounded-lg border-l-4 shadow-lg ${COLORS[t.type]} min-w-[300px] max-w-md animate-in`}>
            <Icon size={18} /><span className="flex-1 text-sm">{t.message}</span>
            <button onClick={() => removeToast(t.id)}><X size={14} /></button>
          </div>
        )
      })}
    </div>
  )
}
