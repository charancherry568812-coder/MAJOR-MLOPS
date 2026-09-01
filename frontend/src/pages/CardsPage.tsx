import { useState, useEffect } from 'react'
import {
  CreditCard, Shield, Lock, Unlock, Plus, RefreshCw, CheckCircle2,
  Sliders, Eye, EyeOff, Sparkles
} from 'lucide-react'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'

export default function CardsPage() {
  const [cards, setCards] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [showIssueModal, setShowIssueModal] = useState(false)
  const [accounts, setAccounts] = useState<any[]>([])
  const [customers, setCustomers] = useState<any[]>([])

  // Form State
  const [selectedAccId, setSelectedAccId] = useState('')
  const [cardType, setCardType] = useState('DEBIT')
  const [cardNetwork, setCardNetwork] = useState('RUPAY')
  const [cardholderName, setCardholderName] = useState('RAJESH KUMAR')
  const [creditLimit, setCreditLimit] = useState('100000')

  const { addToast } = useToastStore()

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [cardsRes, accRes, custRes] = await Promise.all([
        api.get('/cards'),
        api.get('/accounts'),
        api.get('/customers'),
      ])
      setCards(cardsRes.data.data || [])
      const accList = accRes.data.data.items || []
      setAccounts(accList)
      if (accList.length > 0) setSelectedAccId(accList[0].id)
      setCustomers(custRes.data.data.items || [])
    } catch (err) {
      addToast('error', 'Failed to load cards')
    } finally {
      setLoading(false)
    }
  }

  const handleIssueCard = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const acc = accounts.find(a => a.id === selectedAccId)
      if (!acc) return

      await api.post('/cards/issue', {
        customer_id: acc.customer_id,
        account_id: acc.id,
        bank_id: acc.bank_id,
        card_type: cardType,
        card_network: cardNetwork,
        cardholder_name: cardholderName,
        credit_limit: parseFloat(creditLimit),
      })
      addToast('success', `${cardNetwork} ${cardType} card issued with tokenized vault key!`)
      setShowIssueModal(false)
      fetchData()
    } catch (err: any) {
      addToast('error', err.response?.data?.detail || 'Failed to issue card')
    }
  }

  const handleToggleFreeze = async (cardId: string) => {
    try {
      const res = await api.post(`/cards/${cardId}/toggle-freeze`)
      addToast('success', `Card status updated to ${res.data.data.status}`)
      fetchData()
    } catch (err) {
      addToast('error', 'Failed to toggle card freeze')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            💳 <span>Card Management & Tokenization Security</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Issue RuPay, Visa & Mastercard debit/credit cards with zero-plain-text tokenized storage and instant freeze controls.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setShowIssueModal(true)} className="btn-primary flex items-center gap-2 text-xs">
            <Plus className="w-4 h-4" />
            Issue New Card
          </button>
          <button onClick={fetchData} className="btn-secondary flex items-center gap-2 text-xs">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Cards Display Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map((card) => (
          <div key={card.id} className="card p-5 space-y-4 hover:shadow-lg transition-all">
            {/* Visual Card Representation */}
            <div
              className={`p-5 rounded-2xl text-white shadow-lg relative overflow-hidden flex flex-col justify-between h-44 ${
                card.status === 'FROZEN'
                  ? 'bg-slate-700 opacity-75'
                  : card.card_network === 'RUPAY'
                  ? 'bg-gradient-to-r from-orange-600 to-amber-700'
                  : card.card_network === 'VISA'
                  ? 'bg-gradient-to-r from-blue-700 to-indigo-900'
                  : 'bg-gradient-to-r from-rose-700 to-purple-900'
              }`}
            >
              <div className="flex justify-between items-start">
                <span className="text-xs font-bold uppercase tracking-wider">{card.card_type} CARD</span>
                <span className="font-extrabold tracking-wider text-sm">{card.card_network}</span>
              </div>

              <div>
                <p className="font-mono text-base font-semibold tracking-widest">{card.card_number_masked}</p>
                <div className="flex justify-between items-end mt-3 text-xs">
                  <div>
                    <span className="text-[9px] text-white/70 uppercase">Cardholder</span>
                    <p className="font-medium tracking-wide">{card.cardholder_name}</p>
                  </div>
                  <div>
                    <span className="text-[9px] text-white/70 uppercase">Expires</span>
                    <p className="font-mono">{card.expiry_month}/{card.expiry_year}</p>
                  </div>
                </div>
              </div>

              {card.status === 'FROZEN' && (
                <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-xs flex items-center justify-center gap-2 text-rose-300 font-bold text-sm">
                  <Lock className="w-4 h-4" />
                  CARD FROZEN
                </div>
              )}
            </div>

            {/* Actions & Settings */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Security Vault:</span>
                <span className="badge badge-info text-[10px]">PCI-DSS Tokenized</span>
              </div>

              {card.card_type === 'CREDIT' && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Credit Limit:</span>
                  <span className="font-bold text-slate-800">₹{card.credit_limit?.toLocaleString()}</span>
                </div>
              )}

              <button
                onClick={() => handleToggleFreeze(card.id)}
                className={`w-full py-2 px-3 rounded-lg text-xs font-medium flex items-center justify-center gap-2 transition-colors ${
                  card.status === 'ACTIVE'
                    ? 'bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200'
                    : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                }`}
              >
                {card.status === 'ACTIVE' ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                {card.status === 'ACTIVE' ? 'Freeze Card Temporarily' : 'Unfreeze Card'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* ISSUE CARD MODAL */}
      {showIssueModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900">Issue Tokenized Bank Card</h3>
            <form onSubmit={handleIssueCard} className="space-y-4">
              <div>
                <label className="label">Linked Account</label>
                <select className="input" value={selectedAccId} onChange={(e) => setSelectedAccId(e.target.value)}>
                  {accounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.account_number} ({a.currency} {a.balance.toLocaleString()})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Card Type</label>
                  <select className="input" value={cardType} onChange={(e) => setCardType(e.target.value)}>
                    <option value="DEBIT">DEBIT</option>
                    <option value="CREDIT">CREDIT</option>
                    <option value="VIRTUAL">VIRTUAL</option>
                  </select>
                </div>
                <div>
                  <label className="label">Card Network</label>
                  <select className="input" value={cardNetwork} onChange={(e) => setCardNetwork(e.target.value)}>
                    <option value="RUPAY">RuPay (India Domestic / NPCI)</option>
                    <option value="VISA">Visa International</option>
                    <option value="MASTERCARD">Mastercard</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="label">Embossed Cardholder Name</label>
                <input
                  type="text"
                  className="input"
                  value={cardholderName}
                  onChange={(e) => setCardholderName(e.target.value.toUpperCase())}
                  required
                />
              </div>

              {cardType === 'CREDIT' && (
                <div>
                  <label className="label">Approved Credit Limit (INR)</label>
                  <input
                    type="number"
                    className="input"
                    value={creditLimit}
                    onChange={(e) => setCreditLimit(e.target.value)}
                    required
                  />
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowIssueModal(false)} className="btn-secondary flex-1">
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1">
                  Issue & Tokenize
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
