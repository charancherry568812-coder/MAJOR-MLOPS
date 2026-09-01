import { useState, useEffect } from 'react'
import {
  ShieldCheck, AlertTriangle, Search, CheckCircle2, XCircle,
  FileText, UserCheck, RefreshCw, Eye, Flag, Scale
} from 'lucide-react'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'

export default function ComplianceHubPage() {
  const [activeTab, setActiveTab] = useState<'kyc' | 'aml' | 'sanctions'>('kyc')
  const [loading, setLoading] = useState(false)

  // KYC State
  const [kycCases, setKycCases] = useState<any[]>([])
  const [panNumber, setPanNumber] = useState('ABCDE1234F')
  const [panName, setPanName] = useState('Rajesh Kumar')
  const [panResult, setPanResult] = useState<any>(null)

  const [aadhaarNumber, setAadhaarNumber] = useState('987654321099')
  const [aadhaarName, setAadhaarName] = useState('Rajesh Kumar')
  const [aadhaarResult, setAadhaarResult] = useState<any>(null)

  // AML State
  const [amlAlerts, setAmlAlerts] = useState<any[]>([])
  const [selectedAlert, setSelectedAlert] = useState<any>(null)
  const [resolveNotes, setResolveNotes] = useState('')
  const [resolutionType, setResolutionType] = useState('RESOLVED')

  // Sanctions State
  const [sanctionsWatchlist, setSanctionsWatchlist] = useState<any[]>([])
  const [screenQuery, setScreenQuery] = useState('Viktor Chernov')
  const [screenThreshold, setScreenThreshold] = useState(70)
  const [screenResult, setScreenResult] = useState<any>(null)

  const { addToast } = useToastStore()

  useEffect(() => {
    fetchComplianceData()
  }, [])

  const fetchComplianceData = async () => {
    try {
      setLoading(true)
      const [kycRes, amlRes, sancRes] = await Promise.all([
        api.get('/kyc/cases'),
        api.get('/aml/alerts'),
        api.get('/sanctions/watchlist'),
      ])
      setKycCases(kycRes.data.data.items || [])
      setAmlAlerts(amlRes.data.data.items || [])
      setSanctionsWatchlist(sancRes.data.data || [])
    } catch (err) {
      addToast('error', 'Failed to load compliance data')
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyPAN = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await api.post('/kyc/verify-pan', { pan_number: panNumber, full_name: panName })
      setPanResult(res.data.data)
      addToast('success', `PAN verification result: ${res.data.data.status}`)
    } catch (err) {
      addToast('error', 'PAN verification failed')
    }
  }

  const handleVerifyAadhaar = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await api.post('/kyc/verify-aadhaar', { aadhaar_number: aadhaarNumber, full_name: aadhaarName })
      setAadhaarResult(res.data.data)
      addToast('success', `Aadhaar verification result: ${res.data.data.status}`)
    } catch (err) {
      addToast('error', 'Aadhaar verification failed')
    }
  }

  const handleResolveAlert = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedAlert) return
    try {
      await api.put(`/aml/alerts/${selectedAlert.id}/resolve`, {
        resolution: resolutionType,
        notes: resolveNotes,
      })
      addToast('success', `Alert resolved as ${resolutionType}`)
      setSelectedAlert(null)
      fetchComplianceData()
    } catch (err) {
      addToast('error', 'Failed to resolve AML alert')
    }
  }

  const handleScreenSanctions = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await api.post(`/sanctions/screen?name=${encodeURIComponent(screenQuery)}&threshold=${screenThreshold}`)
      setScreenResult(res.data.data)
      addToast('info', `Found ${res.data.data.total_matches} watchlist matches`)
    } catch (err) {
      addToast('error', 'Sanctions screening failed')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            ⚖️ <span>Risk, KYC, AML & Sanctions Governance Hub</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated regulatory identity verification (PAN/Aadhaar sandbox), rule-based AML monitoring, and fuzzy OFAC/UN sanctions screening.
          </p>
        </div>
        <button onClick={fetchComplianceData} className="btn-secondary flex items-center gap-2 text-xs">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Governance
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-4">
        {[
          { id: 'kyc', label: 'KYC & Identity Verification', icon: UserCheck },
          { id: 'aml', label: 'AML Transaction Alerts & SAR Cases', icon: AlertTriangle },
          { id: 'sanctions', label: 'Sanctions Watchlist & Fuzzy Screening', icon: Scale },
        ].map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-3 px-2 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* TAB 1: KYC VERIFICATION */}
      {activeTab === 'kyc' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* PAN Verification Simulator */}
            <div className="card">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <h3 className="font-bold text-sm text-slate-900">NSDL / Income Tax PAN Adapter</h3>
                <span className="badge badge-info text-[10px]">SANDBOX</span>
              </div>
              <form onSubmit={handleVerifyPAN} className="space-y-3 mt-4">
                <div>
                  <label className="label">PAN Number (Format: ABCDE1234F)</label>
                  <input
                    type="text"
                    className="input font-mono uppercase"
                    value={panNumber}
                    onChange={(e) => setPanNumber(e.target.value.toUpperCase())}
                    required
                  />
                </div>
                <div>
                  <label className="label">Cardholder Full Name</label>
                  <input
                    type="text"
                    className="input"
                    value={panName}
                    onChange={(e) => setPanName(e.target.value)}
                    required
                  />
                </div>
                <button type="submit" className="btn-primary w-full text-xs">Verify PAN via Sandbox</button>
              </form>

              {panResult && (
                <div className="mt-4 p-3 bg-slate-50 border rounded-xl text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Status:</span>
                    <span className={`font-bold ${panResult.status === 'VALID' ? 'text-emerald-600' : 'text-rose-600'}`}>{panResult.status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Name Match Score:</span>
                    <span className="font-semibold text-slate-800">{panResult.name_match_score}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Provider:</span>
                    <span className="font-mono text-slate-600">{panResult.provider}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Aadhaar Verification Simulator */}
            <div className="card">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <h3 className="font-bold text-sm text-slate-900">UIDAI Gateway Aadhaar Adapter</h3>
                <span className="badge badge-info text-[10px]">SANDBOX VAULT</span>
              </div>
              <form onSubmit={handleVerifyAadhaar} className="space-y-3 mt-4">
                <div>
                  <label className="label">12-Digit Aadhaar Number</label>
                  <input
                    type="text"
                    className="input font-mono"
                    value={aadhaarNumber}
                    onChange={(e) => setAadhaarNumber(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="label">Full Legal Name</label>
                  <input
                    type="text"
                    className="input"
                    value={aadhaarName}
                    onChange={(e) => setAadhaarName(e.target.value)}
                    required
                  />
                </div>
                <button type="submit" className="btn-primary w-full text-xs">Verify Aadhaar Demographic</button>
              </form>

              {aadhaarResult && (
                <div className="mt-4 p-3 bg-slate-50 border rounded-xl text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Masked ID:</span>
                    <span className="font-mono font-bold text-slate-800">{aadhaarResult.aadhaar_masked}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Demographic Match:</span>
                    <span className="font-semibold text-emerald-600">{aadhaarResult.status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Vault Token:</span>
                    <span className="font-mono text-[10px] text-slate-600 truncate max-w-[180px]">{aadhaarResult.vault_token}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* KYC Cases Queue */}
          <div className="card overflow-hidden">
            <h3 className="text-base font-semibold text-slate-900 mb-4">KYC Applications Queue</h3>
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
                <tr>
                  <th className="p-3">Case Number</th>
                  <th className="p-3">Customer</th>
                  <th className="p-3">Score</th>
                  <th className="p-3">PAN</th>
                  <th className="p-3">Aadhaar</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {kycCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="p-3 font-mono font-medium text-slate-900">{c.case_number}</td>
                    <td className="p-3 font-semibold text-slate-800">{c.customer_name}</td>
                    <td className="p-3"><span className="badge badge-info">{c.verification_score}%</span></td>
                    <td className="p-3">{c.pan_verified ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <XCircle className="w-4 h-4 text-rose-500" />}</td>
                    <td className="p-3">{c.aadhaar_verified ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <XCircle className="w-4 h-4 text-rose-500" />}</td>
                    <td className="p-3"><span className="badge badge-success">{c.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: AML ALERTS */}
      {activeTab === 'aml' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="card lg:col-span-2 overflow-hidden">
            <h3 className="text-base font-semibold text-slate-900 mb-4">Real-Time AML Rule Monitoring Queue</h3>
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                <tr>
                  <th className="p-3">Alert Code</th>
                  <th className="p-3">Customer</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Severity</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {amlAlerts.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50">
                    <td className="p-3 font-mono font-medium text-slate-900">{a.alert_code}</td>
                    <td className="p-3 font-semibold text-slate-800">{a.customer_name}</td>
                    <td className="p-3"><span className="badge badge-warning">{a.alert_type}</span></td>
                    <td className="p-3">
                      <span className={`badge ${a.severity === 'CRITICAL' ? 'badge-danger' : a.severity === 'HIGH' ? 'badge-warning' : 'badge-info'}`}>
                        {a.severity}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`badge ${a.status === 'OPEN' ? 'badge-danger' : 'badge-success'}`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="p-3">
                      <button
                        onClick={() => setSelectedAlert(a)}
                        className="btn-secondary text-[11px] py-1 px-2.5"
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Alert Review Box */}
          <div className="card">
            <h3 className="text-base font-semibold text-slate-900 mb-3">Investigation Panel</h3>
            {selectedAlert ? (
              <form onSubmit={handleResolveAlert} className="space-y-4">
                <div className="p-3 bg-slate-50 rounded-xl border space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400">Alert:</span>
                    <p className="font-bold text-slate-900">{selectedAlert.alert_code} ({selectedAlert.alert_type})</p>
                  </div>
                  <div>
                    <span className="text-slate-400">Trigger Reason:</span>
                    <p className="text-slate-700">{selectedAlert.resolution_notes}</p>
                  </div>
                </div>

                <div>
                  <label className="label">Resolution Action</label>
                  <select
                    className="input text-xs"
                    value={resolutionType}
                    onChange={(e) => setResolutionType(e.target.value)}
                  >
                    <option value="RESOLVED">RESOLVED (Verified Source of Funds)</option>
                    <option value="FALSE_POSITIVE">FALSE POSITIVE (Legitimate Transfer)</option>
                    <option value="ESCALATED">ESCALATE TO SAR CASE (File Regulatory Report)</option>
                  </select>
                </div>

                <div>
                  <label className="label">Auditor Investigation Notes</label>
                  <textarea
                    className="input text-xs h-24"
                    value={resolveNotes}
                    onChange={(e) => setResolveNotes(e.target.value)}
                    placeholder="Enter compliance rationale..."
                    required
                  />
                </div>

                <div className="flex gap-2">
                  <button type="button" onClick={() => setSelectedAlert(null)} className="btn-secondary flex-1 text-xs">
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary flex-1 text-xs">
                    Submit Resolution
                  </button>
                </div>
              </form>
            ) : (
              <div className="text-center py-16 text-slate-400 text-xs">
                <ShieldCheck className="w-10 h-10 mx-auto mb-2 opacity-40" />
                Select an alert from the AML queue to review trigger details and assign resolution.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: SANCTIONS SCREENING */}
      {activeTab === 'sanctions' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="card space-y-4">
            <h3 className="text-base font-semibold text-slate-900">Live Fuzzy Screening Simulator</h3>
            <form onSubmit={handleScreenSanctions} className="space-y-4">
              <div>
                <label className="label">Query Entity / Person Name</label>
                <input
                  type="text"
                  className="input"
                  value={screenQuery}
                  onChange={(e) => setScreenQuery(e.target.value)}
                  placeholder="e.g. Viktor Chernov"
                  required
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span>Similarity Threshold</span>
                  <span className="font-bold text-blue-600">{screenThreshold}%</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="100"
                  value={screenThreshold}
                  onChange={(e) => setScreenThreshold(Number(e.target.value))}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2 text-xs">
                <Search className="w-4 h-4" />
                Screen Against Watchlists
              </button>
            </form>

            {screenResult && (
              <div className="mt-4 p-4 rounded-xl border text-xs space-y-2 bg-slate-50">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-700">Screening Result:</span>
                  <span className={`badge ${screenResult.is_flagged ? 'badge-danger' : 'badge-success'}`}>
                    {screenResult.is_flagged ? 'MATCH FLAGGED' : 'CLEAN'}
                  </span>
                </div>
                <p className="text-slate-500">Total potential matches: <span className="font-bold text-slate-900">{screenResult.total_matches}</span></p>

                {screenResult.matches?.map((m: any) => (
                  <div key={m.id} className="p-2.5 bg-white border border-rose-200 rounded-lg space-y-1">
                    <div className="flex justify-between font-bold text-rose-700">
                      <span>{m.match_type} Match</span>
                      <span>{m.match_score}% Similarity</span>
                    </div>
                    <p className="text-[11px] text-slate-600">{m.notes}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card lg:col-span-2 overflow-hidden">
            <h3 className="text-base font-semibold text-slate-900 mb-4">Synthetic Watchlist Entities (OFAC, UN, EU, RBI)</h3>
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                <tr>
                  <th className="p-3">Entity Name</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Country</th>
                  <th className="p-3">Watchlist Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sanctionsWatchlist.map((w) => (
                  <tr key={w.id} className="hover:bg-slate-50">
                    <td className="p-3 font-semibold text-slate-900">{w.entity_name}</td>
                    <td className="p-3"><span className="badge badge-info">{w.entity_type}</span></td>
                    <td className="p-3 font-mono font-medium text-slate-700">{w.country_code}</td>
                    <td className="p-3 font-mono text-slate-600">{w.list_source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
