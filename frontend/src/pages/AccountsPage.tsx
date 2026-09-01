import { useState, useEffect } from 'react'
import {
  Wallet, Plus, Download, Lock, Unlock, Eye, ArrowUpRight, ArrowDownLeft,
  UserCheck, Building, RefreshCw
} from 'lucide-react'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<any[]>([])
  const [selectedAccount, setSelectedAccount] = useState<any>(null)
  const [accountTxns, setAccountTxns] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [showOpenModal, setShowOpenModal] = useState(false)
  const [customers, setCustomers] = useState<any[]>([])
  const [banks, setBanks] = useState<any[]>([])

  // Open Account Form
  const [newCustId, setNewCustId] = useState('')
  const [newBankId, setNewBankId] = useState('')
  const [newType, setNewType] = useState('SAVINGS')
  const [newCurrency, setNewCurrency] = useState('INR')
  const [newDeposit, setNewDeposit] = useState('25000')

  const { addToast } = useToastStore()

  useEffect(() => {
    fetchAccounts()
  }, [])

  const fetchAccounts = async () => {
    try {
      setLoading(true)
      const [accRes, custRes, banksRes] = await Promise.all([
        api.get('/accounts?page_size=50'),
        api.get('/customers?page_size=50'),
        api.get('/banks'),
      ])
      const accList = accRes.data.data.items || []
      setAccounts(accList)
      const custList = custRes.data.data.items || []
      setCustomers(custList)
      if (custList.length > 0) setNewCustId(custList[0].id)
      const bankList = banksRes.data.data.items || []
      setBanks(bankList)
      if (bankList.length > 0) setNewBankId(bankList[0].id)

      if (accList.length > 0 && !selectedAccount) {
        viewAccountDetail(accList[0].id)
      }
    } catch (err: any) {
      addToast('error', 'Failed to load accounts')
    } finally {
      setLoading(false)
    }
  }

  const viewAccountDetail = async (accId: string) => {
    try {
      const [detailRes, txnRes] = await Promise.all([
        api.get(`/accounts/${accId}`),
        api.get(`/accounts/${accId}/transactions`),
      ])
      setSelectedAccount(detailRes.data.data)
      setAccountTxns(txnRes.data.data.items || [])
    } catch (err) {
      addToast('error', 'Failed to load account details')
    }
  }

  const handleOpenAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/accounts', {
        customer_id: newCustId,
        bank_id: newBankId,
        account_type: newType,
        currency: newCurrency,
        initial_deposit: parseFloat(newDeposit),
      })
      addToast('success', 'New account opened successfully!')
      setShowOpenModal(false)
      fetchAccounts()
    } catch (err: any) {
      addToast('error', err.response?.data?.detail || 'Failed to open account')
    }
  }

  const handleToggleFreeze = async (accId: string) => {
    try {
      const res = await api.post(`/accounts/${accId}/toggle-freeze`)
      addToast('success', `Account status updated to ${res.data.data.status}`)
      viewAccountDetail(accId)
      fetchAccounts()
    } catch (err) {
      addToast('error', 'Failed to update freeze status')
    }
  }

  const handleDownloadStatement = async (accId: string, accNum: string) => {
    try {
      const res = await api.get(`/accounts/${accId}/statement`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `statement_${accNum}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      addToast('success', 'Account statement downloaded')
    } catch (err) {
      addToast('error', 'Failed to download statement')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            💳 <span>Customer Accounts & Ledger Management</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time balance inquiries, multi-currency accounts, freeze controls, and statement exports.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setShowOpenModal(true)} className="btn-primary flex items-center gap-2 text-xs">
            <Plus className="w-4 h-4" />
            Open New Account
          </button>
          <button onClick={fetchAccounts} className="btn-secondary flex items-center gap-2 text-xs">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Accounts List */}
        <div className="card lg:col-span-1 space-y-3 max-h-[750px] overflow-y-auto">
          <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">All Active Accounts</h2>
          <div className="space-y-2">
            {accounts.map((acc) => (
              <div
                key={acc.id}
                onClick={() => viewAccountDetail(acc.id)}
                className={`p-3 rounded-xl border cursor-pointer transition-all ${
                  selectedAccount?.id === acc.id
                    ? 'border-blue-600 bg-blue-50/50 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300 bg-white'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-slate-900">{acc.account_number}</span>
                  <span className={`badge ${acc.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'} text-[10px]`}>
                    {acc.status}
                  </span>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">{acc.account_type}</span>
                  <span className="text-sm font-bold text-slate-900">
                    {acc.currency} {acc.balance.toLocaleString()}
                  </span>
                </div>
                <div className="mt-1 text-[11px] text-slate-400">UPI: {acc.upi_vpa}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Selected Account Ledger & Statement */}
        <div className="card lg:col-span-2 space-y-6">
          {selectedAccount ? (
            <>
              {/* Summary Banner */}
              <div className="p-5 bg-slate-900 rounded-xl text-white flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="badge badge-info text-[10px]">{selectedAccount.account_type}</span>
                    <span className="font-mono text-xs text-slate-400">{selectedAccount.bank_name}</span>
                  </div>
                  <h3 className="text-2xl font-bold mt-1">
                    {selectedAccount.currency} {selectedAccount.balance.toLocaleString()}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Holder: <span className="text-white font-medium">{selectedAccount.customer?.customer_name}</span> | IFSC: <span className="text-slate-200 font-mono">{selectedAccount.ifsc_code}</span>
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDownloadStatement(selectedAccount.id, selectedAccount.account_number)}
                    className="btn-secondary text-xs flex items-center gap-1.5 py-1.5"
                  >
                    <Download className="w-3.5 h-3.5" />
                    CSV Statement
                  </button>
                  <button
                    onClick={() => handleToggleFreeze(selectedAccount.id)}
                    className={`text-xs flex items-center gap-1.5 py-1.5 px-3 rounded-lg font-medium transition-colors ${
                      selectedAccount.status === 'ACTIVE'
                        ? 'bg-rose-600 hover:bg-rose-700 text-white'
                        : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                    }`}
                  >
                    {selectedAccount.status === 'ACTIVE' ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                    {selectedAccount.status === 'ACTIVE' ? 'Freeze Account' : 'Unfreeze'}
                  </button>
                </div>
              </div>

              {/* Transactions in Account */}
              <div>
                <h3 className="text-sm font-semibold text-slate-900 mb-3">Transaction History</h3>
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                      <tr>
                        <th className="p-3">Reference</th>
                        <th className="p-3">Type</th>
                        <th className="p-3">Amount</th>
                        <th className="p-3">Rail</th>
                        <th className="p-3">Status</th>
                        <th className="p-3">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {accountTxns.map((t) => (
                        <tr key={t.id} className="hover:bg-slate-50">
                          <td className="p-3 font-mono font-medium text-slate-800">{t.reference}</td>
                          <td className="p-3">
                            <span className={`inline-flex items-center gap-1 font-semibold ${t.type === 'CREDIT' ? 'text-emerald-600' : 'text-rose-600'}`}>
                              {t.type === 'CREDIT' ? <ArrowDownLeft className="w-3.5 h-3.5" /> : <ArrowUpRight className="w-3.5 h-3.5" />}
                              {t.type}
                            </span>
                          </td>
                          <td className="p-3 font-bold text-slate-900">
                            {t.type === 'CREDIT' ? '+' : '-'}{t.currency} {t.amount.toLocaleString()}
                          </td>
                          <td className="p-3"><span className="badge badge-info">{t.rail}</span></td>
                          <td className="p-3"><span className="badge badge-success">{t.status}</span></td>
                          <td className="p-3 text-slate-400">{t.created_at ? new Date(t.created_at).toLocaleDateString() : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-20 text-slate-400 text-sm">
              <Wallet className="w-12 h-12 mx-auto mb-3 opacity-40" />
              Select an account from the list to view balances and transaction history.
            </div>
          )}
        </div>
      </div>

      {/* OPEN ACCOUNT MODAL */}
      {showOpenModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900">Open New Bank Account</h3>
            <form onSubmit={handleOpenAccount} className="space-y-4">
              <div>
                <label className="label">Select Customer</label>
                <select className="input" value={newCustId} onChange={(e) => setNewCustId(e.target.value)}>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.first_name} {c.last_name} ({c.customer_number})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Bank Entity</label>
                <select className="input" value={newBankId} onChange={(e) => setNewBankId(e.target.value)}>
                  {banks.map((b) => (
                    <option key={b.id} value={b.id}>{b.name} ({b.code})</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Account Type</label>
                  <select className="input" value={newType} onChange={(e) => setNewType(e.target.value)}>
                    <option value="SAVINGS">SAVINGS</option>
                    <option value="CURRENT">CURRENT</option>
                    <option value="SALARY">SALARY</option>
                    <option value="FIXED_DEPOSIT">FIXED DEPOSIT</option>
                  </select>
                </div>
                <div>
                  <label className="label">Currency</label>
                  <select className="input" value={newCurrency} onChange={(e) => setNewCurrency(e.target.value)}>
                    <option value="INR">INR (₹)</option>
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="label">Opening Deposit Amount</label>
                <input
                  type="number"
                  className="input"
                  value={newDeposit}
                  onChange={(e) => setNewDeposit(e.target.value)}
                  required
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowOpenModal(false)} className="btn-secondary flex-1">
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1">
                  Create Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
