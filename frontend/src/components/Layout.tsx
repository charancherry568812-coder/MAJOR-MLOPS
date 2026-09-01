import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import {
  BarChart3, Building2, Database, GitBranch, LayoutDashboard, LogOut, Menu,
  Monitor, Package, PieChart, Settings, Shield, Brain, AlertTriangle,
  FileText, User, Cpu, Target, X, ChevronDown, ChevronRight, ShieldAlert,
  Sliders, Activity, RefreshCw, Send, Wallet, Landmark, CreditCard,
  UserCheck, Layers, Globe
} from 'lucide-react'

const NAV = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  {
    label: 'Digital Banking & Rails',
    icon: Wallet,
    children: [
      { label: 'Payments & UPI Hub', path: '/banking/payments' },
      { label: 'Customer Accounts', path: '/banking/accounts' },
      { label: 'Loans & Amortization', path: '/banking/loans' },
      { label: 'Card Management', path: '/banking/cards' },
      { label: 'Bank Entities & Branches', path: '/banks' },
    ],
  },
  {
    label: 'Risk & Compliance Hub',
    icon: ShieldAlert,
    children: [
      { label: 'KYC, AML & Sanctions', path: '/compliance' },
      { label: 'Real-Time Fraud Engine', path: '/fraud' },
      { label: 'Compliance Reports', path: '/reports' },
    ],
  },
  { label: 'MLOps Pipeline', icon: Cpu, path: '/pipeline' },
  { label: 'Data Management', icon: Database, path: '/datasets' },
  {
    label: 'Federated Learning',
    icon: GitBranch,
    children: [
      { label: 'Training Orchestrator', path: '/federated-training' },
      { label: 'Bank Client Nodes', path: '/federated/clients' },
      { label: 'FL Rounds History', path: '/federated/rounds' },
    ],
  },
  {
    label: 'Model Registry',
    icon: Brain,
    children: [
      { label: 'Registered Models', path: '/models' },
      { label: 'Compare Versions', path: '/models/compare' },
      { label: 'Deployments', path: '/deployments' },
      { label: 'Experiments', path: '/experiments' },
      { label: 'Training Runs', path: '/training-runs' },
    ],
  },
  {
    label: 'Credit Predictions',
    icon: Target,
    children: [
      { label: 'Single Scoring', path: '/predictions/single' },
      { label: 'Batch Prediction', path: '/predictions/batch' },
      { label: 'Scoring History', path: '/predictions/history' },
      { label: 'SHAP Explainability', path: '/explainability' },
    ],
  },
  {
    label: 'MLOps Monitoring',
    icon: Monitor,
    children: [
      { label: 'Performance & Drift', path: '/monitoring/model' },
      { label: 'Statistical Data Drift', path: '/monitoring/drift' },
      { label: 'System Telemetry', path: '/monitoring/system' },
      { label: 'Operational Alerts', path: '/alerts' },
    ],
  },
  {
    label: 'Governance & Operations',
    icon: Shield,
    children: [
      { label: 'Async Worker Jobs', path: '/jobs' },
      { label: 'Audit Logs', path: '/audit-logs' },
      { label: 'User Management', path: '/users' },
      { label: 'Security & Encryption', path: '/security' },
    ],
  },
  { label: 'System Settings', icon: Settings, path: '/settings' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    'Digital Banking & Rails': true,
    'Risk & Compliance Hub': true,
    'Federated Learning': true,
    'Model Registry': false,
    'Credit Predictions': false,
    'MLOps Monitoring': false,
    'Governance & Operations': false,
  })
  const [currentLocale, setCurrentLocale] = useState<'en' | 'hi' | 'kn'>('en')
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const toggle = (label: string) => setExpanded(e => ({ ...e, [label]: !e[label] }))
  const isActive = (path: string) => location.pathname === path || (path !== '/dashboard' && location.pathname.startsWith(path + '/'))

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 font-sans">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-0'
        } bg-slate-900 text-white flex flex-col transition-all duration-300 overflow-hidden flex-shrink-0 border-r border-slate-800`}
      >
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
              🏦 <span>FedBank MLOps</span>
            </h1>
            <p className="text-[11px] text-slate-400 mt-0.5">Global & India-First Platform</p>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto p-3 space-y-1 text-xs">
          {NAV.map((item) => {
            const Icon = item.icon
            if (item.children) {
              const isOpen = expanded[item.label]
              const hasActiveChild = item.children.some((c) => isActive(c.path))
              return (
                <div key={item.label} className="space-y-0.5">
                  <button
                    onClick={() => toggle(item.label)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg font-medium transition-colors ${
                      hasActiveChild
                        ? 'bg-slate-800/80 text-blue-400'
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    }`}
                  >
                    <span className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 text-slate-400" />
                      <span>{item.label}</span>
                    </span>
                    {isOpen ? (
                      <ChevronDown className="w-3.5 h-3.5 opacity-60" />
                    ) : (
                      <ChevronRight className="w-3.5 h-3.5 opacity-60" />
                    )}
                  </button>
                  {isOpen && (
                    <div className="pl-6 space-y-0.5 border-l border-slate-800 ml-4 py-1">
                      {item.children.map((c) => (
                        <Link
                          key={c.path}
                          to={c.path}
                          className={`block px-3 py-1.5 rounded-md transition-colors ${
                            isActive(c.path)
                              ? 'bg-blue-600 text-white font-semibold shadow-xs'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                          }`}
                        >
                          {c.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              )
            }

            return (
              <Link
                key={item.path}
                to={item.path!}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg font-medium transition-colors ${
                  isActive(item.path!)
                    ? 'bg-blue-600 text-white font-semibold shadow-xs'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4 text-slate-400" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>

        {/* User Card */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/50">
          <div className="flex items-center justify-between">
            <div className="truncate">
              <p className="text-xs font-semibold text-white truncate">{user?.full_name || 'Admin User'}</p>
              <p className="text-[10px] text-blue-400 font-mono truncate">{typeof user?.role === 'object' ? (user.role as any)?.name : user?.role || 'SUPER_ADMIN'}</p>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-14 bg-white border-b border-slate-200 px-4 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-slate-700">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>FedBank Consortium • 4 Active Nodes • Flower gRPC Ready</span>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {/* Locale Selector */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
              <Globe className="w-3.5 h-3.5 text-slate-500 ml-1" />
              <button
                onClick={() => setCurrentLocale('en')}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors ${
                  currentLocale === 'en' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600'
                }`}
              >
                EN
              </button>
              <button
                onClick={() => setCurrentLocale('hi')}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors ${
                  currentLocale === 'hi' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600'
                }`}
              >
                हिन्दी
              </button>
              <button
                onClick={() => setCurrentLocale('kn')}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors ${
                  currentLocale === 'kn' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600'
                }`}
              >
                ಕನ್ನಡ
              </button>
            </div>

            <span className="badge badge-info text-[10px]">PRODUCTION READY v2.0</span>
          </div>
        </header>

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-6 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
