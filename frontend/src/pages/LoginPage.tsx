import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useAuthStore, User } from '../store/authStore'
import { useToastStore } from '../store/toastStore'
import { Lock, Mail, Eye, EyeOff, ShieldCheck, Sparkles, UserCheck } from 'lucide-react'

const DEMO_ACCOUNTS: Record<string, { user: User; pass: string; label: string; badge: string }> = {
  'admin@fedbank.com': {
    user: {
      id: 'usr-admin-01',
      email: 'admin@fedbank.com',
      full_name: 'Dr. Sarah Jenkins',
      role: { id: 'r-admin', name: 'SUPER_ADMIN', description: 'Consortium Super Administrator' },
      is_active: true,
    },
    pass: 'Admin@123',
    label: 'Super Admin',
    badge: 'Full Access',
  },
  'banka.admin@fedbank.com': {
    user: {
      id: 'usr-banka-01',
      email: 'banka.admin@fedbank.com',
      full_name: 'Vikram Malhotra',
      role: { id: 'r-bank-admin', name: 'BANK_ADMIN', description: 'Alpha National Bank Admin' },
      is_active: true,
    },
    pass: 'BankA@123',
    label: 'Bank Admin',
    badge: 'Alpha Bank Node',
  },
  'ml.engineer@fedbank.com': {
    user: {
      id: 'usr-mleng-01',
      email: 'ml.engineer@fedbank.com',
      full_name: 'Priya Sundaram',
      role: { id: 'r-mlops', name: 'MLOPS_ENGINEER', description: 'MLOps Pipeline Engineer' },
      is_active: true,
    },
    pass: 'MLEng@123',
    label: 'MLOps Engineer',
    badge: 'FL & Models',
  },
  'data.scientist@fedbank.com': {
    user: {
      id: 'usr-datsci-01',
      email: 'data.scientist@fedbank.com',
      full_name: 'Aarav Sharma',
      role: { id: 'r-datascientist', name: 'DATA_SCIENTIST', description: 'Data Scientist' },
      is_active: true,
    },
    pass: 'DataSci@123',
    label: 'Data Scientist',
    badge: 'SHAP & Experiments',
  },
  'auditor@fedbank.com': {
    user: {
      id: 'usr-audit-01',
      email: 'auditor@fedbank.com',
      full_name: 'Marcus Chen',
      role: { id: 'r-auditor', name: 'AUDITOR', description: 'Compliance & AML Auditor' },
      is_active: true,
    },
    pass: 'Auditor@123',
    label: 'Compliance Auditor',
    badge: 'AML & Sanctions',
  },
  'customer@fedbank.com': {
    user: {
      id: 'usr-cust-01',
      email: 'customer@fedbank.com',
      full_name: 'Rajesh Kumar',
      role: { id: 'r-customer', name: 'CUSTOMER', description: 'Retail Customer' },
      is_active: true,
    },
    pass: 'Customer@123',
    label: 'Retail Customer',
    badge: 'UPI & Accounts',
  },
}

export default function LoginPage() {
  const [email, setEmail] = useState('admin@fedbank.com')
  const [password, setPassword] = useState('Admin@123')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const { addToast } = useToastStore()

  const executeLogin = async (loginEmail: string, loginPass: string) => {
    setLoading(true)
    setError('')
    try {
      // 1. Try calling the live backend API
      const { data } = await api.post('/auth/login', { email: loginEmail, password: loginPass })
      login(data.user, data.access_token, data.refresh_token)
      addToast('success', `Welcome back, ${data.user.full_name}!`)
      navigate('/dashboard')
    } catch (err: any) {
      // 2. Fallback for Static Host / Cloud Previews (Netlify/Vercel)
      const demoAccount = DEMO_ACCOUNTS[loginEmail.toLowerCase().trim()]
      if (demoAccount && demoAccount.pass === loginPass) {
        const dummyToken = `demo-token-${Date.now()}`
        login(demoAccount.user, dummyToken, dummyToken)
        addToast('success', `Signed in as ${demoAccount.user.full_name} (${demoAccount.label})`)
        navigate('/dashboard')
      } else {
        setError(err.response?.data?.detail || 'Invalid email or password. Please select a demo account below.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    executeLogin(email, password)
  }

  const handleQuickLogin = (demoEmail: string) => {
    const demo = DEMO_ACCOUNTS[demoEmail]
    if (demo) {
      setEmail(demo.user.email)
      setPassword(demo.pass)
      executeLogin(demo.user.email, demo.pass)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 flex items-center justify-center p-4">
      <div className="w-full max-w-lg space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 px-3 py-1 rounded-full text-blue-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            Enterprise Global & India-First Platform
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            🏦 FedBank MLOps
          </h1>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Privacy-Preserving Federated Learning, Multi-Rail Payments, Risk & Compliance Engine
          </p>
        </div>

        {/* Form Box */}
        <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl p-6 sm:p-8 space-y-6 border border-slate-100">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h2 className="text-lg font-bold text-slate-900">Sign In to Consortium</h2>
            <span className="badge badge-success text-[10px]">Zero-Trust Auth</span>
          </div>

          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
              <span className="font-semibold">Error:</span> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Work Email Address</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3.5 top-3 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input pl-10 text-xs"
                  placeholder="admin@fedbank.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3.5 top-3 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pl-10 pr-10 text-xs"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-2.5 text-xs font-semibold flex items-center justify-center gap-2 shadow-md"
            >
              {loading ? 'Authenticating Credentials...' : 'Sign In'}
            </button>
          </form>

          {/* 1-Click Demo Profiles */}
          <div className="pt-2 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
              <span className="flex items-center gap-1.5">
                <UserCheck className="w-3.5 h-3.5 text-blue-600" />
                1-Click Quick Demo Access
              </span>
              <span className="text-[10px] text-slate-400">Click any role to enter</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {Object.entries(DEMO_ACCOUNTS).map(([demoEmail, d]) => (
                <button
                  key={demoEmail}
                  type="button"
                  onClick={() => handleQuickLogin(demoEmail)}
                  className="p-2 text-left rounded-xl border border-slate-200 hover:border-blue-500 hover:bg-blue-50/50 transition-all flex flex-col justify-between group"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-slate-900 group-hover:text-blue-600">
                      {d.label}
                    </span>
                    <span className="badge badge-info text-[9px] py-0 px-1.5">
                      {d.badge}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">{demoEmail}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Security Footer */}
        <div className="text-center text-xs text-slate-500 flex items-center justify-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>PCI-DSS & RBI Regulatory Sandbox Architecture</span>
        </div>
      </div>
    </div>
  )
}
