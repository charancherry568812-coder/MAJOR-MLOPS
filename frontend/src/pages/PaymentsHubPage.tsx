import { useState, useEffect } from 'react'
import {
  Send, QrCode, ArrowRightLeft, CheckCircle2, AlertCircle, RefreshCw,
  Globe, Shield, DollarSign, Wallet, ArrowUpRight, Copy, Check
} from 'lucide-react'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'

export default function PaymentsHubPage() {
  const [activeTab, setActiveTab] = useState<'transfer' | 'upi_qr' | 'fx_calc' | 'history'>('transfer')
  const [accounts, setAccounts] = useState<any[]>([])
  const [rails, setRails] = useState<any[]>([])
  const [currencies, setCurrencies] = useState<any[]>([])
  const [transactions, setTransactions] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  // Transfer Form State
  const [sourceAccId, setSourceAccId] = useState('')
  const [amount, setAmount] = useState('1000')
  const [selectedRail, setSelectedRail] = useState('UPI')
  const [recipientIdentifier, setRecipientIdentifier] = useState('merchant@fedbank')
  const [recipientName, setRecipientName] = useState('Star Supermarket')
  const [description, setDescription] = useState('Payment for retail goods')
  const [transferResult, setTransferResult] = useState<any>(null)

  // UPI QR State
  const [upiPayeeVpa, setUpiPayeeVpa] = useState('store@fedbank')
  const [upiPayeeName, setUpiPayeeName] = useState('FedBank Central Retail')
  const [upiAmount, setUpiAmount] = useState('500')
  const [upiNote, setUpiNote] = useState('Invoice #90214')
  const [upiIntent, setUpiIntent] = useState<any>(null)

  // FX Converter State
  const [fxFrom, setFxFrom] = useState('USD')
  const [fxTo, setFxTo] = useState('INR')
  const [fxAmount, setFxAmount] = useState('100')
  const [fxResult, setFxResult] = useState<any>(null)

  const { addToast } = useToastStore()

  useEffect(() => {
    fetchInitialData()
  }, [])

  const fetchInitialData = async () => {
    try {
      setLoading(true)
      const [accRes, railsRes, curRes, txRes] = await Promise.all([
        api.get('/accounts'),
        api.get('/payment-rails'),
        api.get('/currencies'),
        api.get('/transactions?page_size=15'),
      ])
      const accItems = accRes.data.data.items || []
      setAccounts(accItems)
      if (accItems.length > 0) setSourceAccId(accItems[0].id)
      setRails(railsRes.data.data || [])
      setCurrencies(curRes.data.data || [])
      setTransactions(txRes.data.data.items || [])
    } catch (err: any) {
      addToast('error', 'Failed to load banking rails data')
    } finally {
      setLoading(false)
    }
  }

  const handleExecuteTransfer = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      const res = await api.post('/payments/transfer', {
        source_account_id: sourceAccId,
        amount: parseFloat(amount),
        payment_rail: selectedRail,
        recipient_identifier: recipientIdentifier,
        recipient_name: recipientName,
        description: description,
      })
      setTransferResult(res.data.data)
      addToast('success', `Transfer of ₹${amount} executed successfully via ${selectedRail}!`)
      fetchInitialData()
    } catch (err: any) {
      addToast('error', err.response?.data?.detail || 'Payment execution failed')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateUPIQR = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      const res = await api.post('/payments/upi/create-intent', {
        payee_vpa: upiPayeeVpa,
        payee_name: upiPayeeName,
        amount: parseFloat(upiAmount),
        currency: 'INR',
        note: upiNote,
      })
      setUpiIntent(res.data.data)
      addToast('success', 'UPI Dynamic QR Intent generated!')
    } catch (err: any) {
      addToast('error', 'Failed to generate UPI QR')
    } finally {
      setLoading(false)
    }
  }

  const handleCalculateFX = async () => {
    try {
      const res = await api.post('/currencies/convert', {
        amount: parseFloat(fxAmount),
        from_currency: fxFrom,
        to_currency: fxTo,
      })
      setFxResult(res.data.data)
    } catch (err: any) {
      addToast('error', 'FX calculation failed')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            ⚡ <span>Global & Domestic Payments Hub</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            India-First UPI / IMPS / NEFT / RTGS & International SWIFT / SEPA / ACH Payment Rails
          </p>
        </div>
        <button
          onClick={fetchInitialData}
          className="btn-secondary flex items-center gap-2 text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Rails
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-4">
        {[
          { id: 'transfer', label: 'Multi-Rail Transfer', icon: Send },
          { id: 'upi_qr', label: 'UPI QR Intent Generator', icon: QrCode },
          { id: 'fx_calc', label: 'Multi-Currency FX Converter', icon: ArrowRightLeft },
          { id: 'history', label: 'Payment Ledger History', icon: DollarSign },
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

      {/* TAB 1: MULTI-RAIL TRANSFER */}
      {activeTab === 'transfer' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card">
            <h2 className="text-base font-semibold text-slate-900 mb-4">Execute Funds Transfer</h2>
            <form onSubmit={handleExecuteTransfer} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Source Account</label>
                  <select
                    className="input"
                    value={sourceAccId}
                    onChange={(e) => setSourceAccId(e.target.value)}
                  >
                    {accounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>
                        {acc.account_number} ({acc.currency} {acc.balance.toLocaleString()}) - {acc.account_type}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Payment Rail</label>
                  <select
                    className="input"
                    value={selectedRail}
                    onChange={(e) => setSelectedRail(e.target.value)}
                  >
                    <option value="UPI">UPI (Unified Payments Interface - Instant)</option>
                    <option value="IMPS">IMPS (Immediate Payment Service - 24x7)</option>
                    <option value="NEFT">NEFT (National Electronic Funds Transfer)</option>
                    <option value="RTGS">RTGS (Real Time Gross Settlement &gt; ₹2L)</option>
                    <option value="SWIFT">SWIFT Cross-Border Wire (ISO 20022)</option>
                    <option value="SEPA">SEPA Instant Euro Credit</option>
                    <option value="ACH">US ACH Clearing</option>
                    <option value="FEDWIRE">Fedwire Real-Time Gross</option>
                    <option value="FASTER_PAYMENTS">UK Faster Payments (FPS)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    className="input"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="label">Recipient Identifier (VPA / Account / IBAN)</label>
                  <input
                    type="text"
                    className="input"
                    value={recipientIdentifier}
                    onChange={(e) => setRecipientIdentifier(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Recipient Name / Beneficiary</label>
                  <input
                    type="text"
                    className="input"
                    value={recipientName}
                    onChange={(e) => setRecipientName(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="label">Transfer Description / Reference Note</label>
                  <input
                    type="text"
                    className="input"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  {loading ? 'Routing Payment through Sandbox Rail...' : 'Confirm & Transfer Funds'}
                </button>
              </div>
            </form>
          </div>

          {/* Transfer Result / Receipt */}
          <div className="card bg-slate-900 text-white flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h3 className="font-semibold text-sm text-slate-200">Execution Receipt</h3>
                <span className="badge badge-success text-[10px]">SANDBOX SECURE</span>
              </div>

              {transferResult ? (
                <div className="mt-4 space-y-3 text-xs">
                  <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Transaction Succeeded</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Transaction Ref:</span>
                    <p className="font-mono text-slate-100 font-medium">{transferResult.transaction_reference}</p>
                  </div>
                  <div>
                    <span className="text-slate-400">Provider Reference (RRN/UETR):</span>
                    <p className="font-mono text-emerald-300">{transferResult.provider_reference}</p>
                  </div>
                  <div className="flex justify-between py-1 border-y border-slate-800">
                    <span className="text-slate-400">Settled Amount:</span>
                    <span className="font-bold text-white">{transferResult.currency} {transferResult.amount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Rail / Provider:</span>
                    <span className="text-slate-200">{transferResult.payment_rail} ({transferResult.provider_name})</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Clearing Latency:</span>
                    <span className="text-slate-200">{transferResult.clearing_time_ms} ms</span>
                  </div>
                </div>
              ) : (
                <div className="mt-12 text-center text-slate-500 text-xs">
                  <Wallet className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  Fill out the transfer form to dispatch transaction across domestic & international payment networks.
                </div>
              )}
            </div>

            <div className="mt-6 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center gap-2">
              <Shield className="w-3.5 h-3.5 text-blue-400" />
              Protected by Real-Time Sanctions Screening & AML Rule Engine
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: UPI QR INTENT GENERATOR */}
      {activeTab === 'upi_qr' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="text-base font-semibold text-slate-900 mb-4">Generate Dynamic UPI Intent QR</h2>
            <form onSubmit={handleGenerateUPIQR} className="space-y-4">
              <div>
                <label className="label">Payee VPA (Virtual Payment Address)</label>
                <input
                  type="text"
                  className="input"
                  value={upiPayeeVpa}
                  onChange={(e) => setUpiPayeeVpa(e.target.value)}
                  placeholder="name@fedbank"
                  required
                />
              </div>
              <div>
                <label className="label">Payee Legal Name</label>
                <input
                  type="text"
                  className="input"
                  value={upiPayeeName}
                  onChange={(e) => setUpiPayeeName(e.target.value)}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Amount (INR)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="input"
                    value={upiAmount}
                    onChange={(e) => setUpiAmount(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="label">Transaction Note</label>
                  <input
                    type="text"
                    className="input"
                    value={upiNote}
                    onChange={(e) => setUpiNote(e.target.value)}
                  />
                </div>
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
                <QrCode className="w-4 h-4" />
                Generate UPI Deep Link & QR
              </button>
            </form>
          </div>

          <div className="card flex flex-col items-center justify-center text-center p-6 border-2 border-dashed border-slate-200">
            {upiIntent ? (
              <div className="space-y-4">
                <div className="p-4 bg-white rounded-xl shadow-md border border-slate-200 inline-block">
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(upiIntent.qr_payload)}`}
                    alt="UPI QR Code"
                    className="w-44 h-44 rounded"
                  />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-lg">₹{upiIntent.amount.toLocaleString()}</h3>
                  <p className="text-xs text-slate-500">Scan with any UPI App (BHIM, Google Pay, PhonePe, Paytm)</p>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-lg text-left text-xs font-mono text-slate-700 max-w-sm overflow-x-auto">
                  {upiIntent.qr_payload}
                </div>
              </div>
            ) : (
              <div className="text-slate-400 text-xs">
                <QrCode className="w-16 h-16 mx-auto mb-3 opacity-40 text-slate-500" />
                Configure payment parameters to create standard NPCI-compliant UPI payment intent string.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: FX CONVERTER */}
      {activeTab === 'fx_calc' && (
        <div className="card max-w-2xl mx-auto space-y-6">
          <h2 className="text-base font-semibold text-slate-900">Multi-Currency FX Converter</h2>
          <div className="grid grid-cols-3 gap-4 items-end">
            <div>
              <label className="label">Amount</label>
              <input
                type="number"
                className="input"
                value={fxAmount}
                onChange={(e) => setFxAmount(e.target.value)}
              />
            </div>
            <div>
              <label className="label">From Currency</label>
              <select className="input" value={fxFrom} onChange={(e) => setFxFrom(e.target.value)}>
                {currencies.map(c => <option key={c.code} value={c.code}>{c.code} - {c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">To Currency</label>
              <select className="input" value={fxTo} onChange={(e) => setFxTo(e.target.value)}>
                {currencies.map(c => <option key={c.code} value={c.code}>{c.code} - {c.name}</option>)}
              </select>
            </div>
          </div>

          <button onClick={handleCalculateFX} className="btn-primary w-full flex items-center justify-center gap-2">
            <ArrowRightLeft className="w-4 h-4" />
            Convert Currency
          </button>

          {fxResult && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between">
              <div>
                <p className="text-xs text-blue-700 font-medium">Exchange Rate: 1 {fxResult.from_currency} = {fxResult.fx_rate} {fxResult.to_currency}</p>
                <p className="text-xl font-bold text-blue-950 mt-1">{fxResult.formatted}</p>
              </div>
              <span className="badge badge-info">Decimal Safe Ledger</span>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: TRANSACTION LEDGER */}
      {activeTab === 'history' && (
        <div className="card overflow-hidden">
          <h2 className="text-base font-semibold text-slate-900 mb-4">Real-Time Transactions Ledger</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
                <tr>
                  <th className="p-3">Reference</th>
                  <th className="p-3">Amount</th>
                  <th className="p-3">Rail</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Risk</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {transactions.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50">
                    <td className="p-3 font-mono font-medium text-slate-900">{t.reference}</td>
                    <td className="p-3 font-semibold text-slate-800">{t.currency} {t.amount.toLocaleString()}</td>
                    <td className="p-3"><span className="badge badge-info">{t.payment_rail}</span></td>
                    <td className="p-3 text-slate-600">{t.description}</td>
                    <td className="p-3">
                      <span className={`badge ${t.fraud_score > 0.6 ? 'badge-danger' : t.fraud_score > 0.3 ? 'badge-warning' : 'badge-success'}`}>
                        {(t.fraud_score * 100).toFixed(0)}% Risk
                      </span>
                    </td>
                    <td className="p-3">
                      <span className="badge badge-success">{t.status}</span>
                    </td>
                    <td className="p-3 text-slate-400">{t.created_at ? new Date(t.created_at).toLocaleString() : '-'}</td>
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
