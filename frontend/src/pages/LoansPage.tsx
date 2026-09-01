import { useState, useEffect } from 'react'
import {
  Calculator, PieChart, Landmark, CheckCircle2, ChevronRight,
  TrendingUp, AlertCircle, FileSpreadsheet, RefreshCw
} from 'lucide-react'
import api from '../services/api'
import { useToastStore } from '../store/toastStore'

export default function LoansPage() {
  const [loans, setLoans] = useState<any[]>([])
  const [selectedLoan, setSelectedLoan] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  // EMI Calculator State
  const [calcPrincipal, setCalcPrincipal] = useState(1000000)
  const [calcRate, setCalcRate] = useState(10.5)
  const [calcTenure, setCalcTenure] = useState(36)
  const [emiData, setEmiData] = useState<any>(null)

  const { addToast } = useToastStore()

  useEffect(() => {
    fetchLoans()
    calculateEMI()
  }, [])

  useEffect(() => {
    calculateEMI()
  }, [calcPrincipal, calcRate, calcTenure])

  const fetchLoans = async () => {
    try {
      setLoading(true)
      const res = await api.get('/loans?page_size=50')
      const items = res.data.data.items || []
      setLoans(items)
      if (items.length > 0 && !selectedLoan) {
        viewLoanDetail(items[0].id)
      }
    } catch (err) {
      addToast('error', 'Failed to load loans')
    } finally {
      setLoading(false)
    }
  }

  const viewLoanDetail = async (loanId: string) => {
    try {
      const res = await api.get(`/loans/${loanId}`)
      setSelectedLoan(res.data.data)
    } catch (err) {
      addToast('error', 'Failed to load loan detail')
    }
  }

  const calculateEMI = async () => {
    try {
      const res = await api.post('/loans/calculate-emi', {
        principal_amount: calcPrincipal,
        interest_rate_annual: calcRate,
        tenure_months: calcTenure,
      })
      setEmiData(res.data.data)
    } catch (err) {
      // ignore
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            🏦 <span>Loans, Credit Portfolio & Amortization</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Standard mathematical EMI formulas E = P * r * (1+r)^n / ((1+r)^n - 1), amortization schedules, and risk grades.
          </p>
        </div>
        <button onClick={fetchLoans} className="btn-secondary flex items-center gap-2 text-xs">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Interactive EMI Calculator Card */}
      <div className="card bg-gradient-to-br from-slate-900 to-blue-950 text-white p-6 shadow-xl">
        <div className="flex items-center gap-2 pb-4 border-b border-slate-800">
          <Calculator className="w-5 h-5 text-blue-400" />
          <h2 className="text-base font-bold">Interactive EMI & Amortization Calculator</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-6">
          {/* Sliders */}
          <div className="lg:col-span-2 space-y-5">
            {/* Principal */}
            <div>
              <div className="flex justify-between text-xs font-semibold mb-2">
                <span className="text-slate-300">Loan Principal</span>
                <span className="text-blue-400 font-mono text-sm">₹{calcPrincipal.toLocaleString()}</span>
              </div>
              <input
                type="range"
                min="50000"
                max="10000000"
                step="50000"
                value={calcPrincipal}
                onChange={(e) => setCalcPrincipal(Number(e.target.value))}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                <span>₹50K</span>
                <span>₹50L</span>
                <span>₹1 Cr</span>
              </div>
            </div>

            {/* Interest Rate */}
            <div>
              <div className="flex justify-between text-xs font-semibold mb-2">
                <span className="text-slate-300">Interest Rate (Annual %)</span>
                <span className="text-blue-400 font-mono text-sm">{calcRate.toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min="5.0"
                max="24.0"
                step="0.1"
                value={calcRate}
                onChange={(e) => setCalcRate(Number(e.target.value))}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                <span>5.0%</span>
                <span>12.0%</span>
                <span>24.0%</span>
              </div>
            </div>

            {/* Tenure */}
            <div>
              <div className="flex justify-between text-xs font-semibold mb-2">
                <span className="text-slate-300">Loan Tenure (Months)</span>
                <span className="text-blue-400 font-mono text-sm">{calcTenure} Months ({(calcTenure / 12).toFixed(1)} Yrs)</span>
              </div>
              <input
                type="range"
                min="6"
                max="360"
                step="6"
                value={calcTenure}
                onChange={(e) => setCalcTenure(Number(e.target.value))}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                <span>6 Months</span>
                <span>15 Years</span>
                <span>30 Years</span>
              </div>
            </div>
          </div>

          {/* Results Display */}
          {emiData && (
            <div className="bg-slate-800/80 rounded-xl p-5 border border-slate-700/60 flex flex-col justify-between">
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Monthly Installment (EMI)</p>
                <h3 className="text-3xl font-extrabold text-emerald-400 mt-1">
                  ₹{emiData.monthly_emi.toLocaleString()}
                </h3>
              </div>

              <div className="space-y-3 my-4 text-xs border-y border-slate-700 py-3">
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Interest Payable:</span>
                  <span className="font-semibold text-white">₹{emiData.total_interest.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Principal + Interest:</span>
                  <span className="font-bold text-white">₹{emiData.total_payable.toLocaleString()}</span>
                </div>
              </div>

              <div className="text-[11px] text-slate-400">
                Formula applied: <span className="font-mono text-blue-300">E = P * r * (1+r)^n / ((1+r)^n - 1)</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Loans Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Active Loans */}
        <div className="card lg:col-span-1 space-y-3 max-h-[600px] overflow-y-auto">
          <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Disbursed Loans</h2>
          <div className="space-y-2">
            {loans.map((l) => (
              <div
                key={l.id}
                onClick={() => viewLoanDetail(l.id)}
                className={`p-3 rounded-xl border cursor-pointer transition-all ${
                  selectedLoan?.id === l.id
                    ? 'border-blue-600 bg-blue-50/50 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300 bg-white'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-slate-900">{l.loan_number}</span>
                  <span className="badge badge-success text-[10px]">{l.status}</span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs">
                  <span className="text-slate-600 font-medium">{l.customer_name}</span>
                  <span className="font-bold text-slate-900">₹{l.principal_amount.toLocaleString()}</span>
                </div>
                <div className="mt-1 flex items-center justify-between text-[11px] text-slate-400">
                  <span>{l.loan_type} • {l.interest_rate_annual}%</span>
                  <span className="badge badge-info text-[10px]">Grade {l.risk_grade}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Full Amortization Schedule */}
        <div className="card lg:col-span-2 space-y-4">
          {selectedLoan ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-base text-slate-900">{selectedLoan.loan_number} — Amortization Schedule</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Borrower: {selectedLoan.customer_name} • EMI: <span className="font-semibold text-slate-800">₹{selectedLoan.emi_amount.toLocaleString()}</span>
                  </p>
                </div>
                <span className="badge badge-info">{selectedLoan.tenure_months} Installments</span>
              </div>

              <div className="border border-slate-200 rounded-xl overflow-hidden max-h-[450px] overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 sticky top-0">
                    <tr>
                      <th className="p-2.5">#</th>
                      <th className="p-2.5">Due Date</th>
                      <th className="p-2.5">EMI</th>
                      <th className="p-2.5">Principal</th>
                      <th className="p-2.5">Interest</th>
                      <th className="p-2.5">Remaining Balance</th>
                      <th className="p-2.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {selectedLoan.amortization_schedule?.map((row: any) => (
                      <tr key={row.id} className="hover:bg-slate-50">
                        <td className="p-2.5 font-medium text-slate-900">{row.installment_number}</td>
                        <td className="p-2.5 text-slate-600">{row.due_date}</td>
                        <td className="p-2.5 font-semibold text-slate-900">₹{row.emi_amount.toLocaleString()}</td>
                        <td className="p-2.5 text-emerald-600">₹{row.principal_component.toLocaleString()}</td>
                        <td className="p-2.5 text-amber-600">₹{row.interest_component.toLocaleString()}</td>
                        <td className="p-2.5 font-mono text-slate-800">₹{row.remaining_balance.toLocaleString()}</td>
                        <td className="p-2.5"><span className="badge badge-info text-[10px]">{row.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="text-center py-20 text-slate-400 text-sm">
              <Landmark className="w-12 h-12 mx-auto mb-3 opacity-40" />
              Select a loan to inspect month-by-month principal and interest breakdown.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
