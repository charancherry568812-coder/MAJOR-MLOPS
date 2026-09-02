/** API client with JWT interceptors and comprehensive offline / Netlify mock fallback. */
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({ baseURL: `${API_BASE}/api/v1`, timeout: 10000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Comprehensive Mock Data for Static / Netlify Previews
const getMockResponse = (url: string, method: string = 'get', body: any = null) => {
  const cleanUrl = url.replace('/api/v1', '').split('?')[0]

  // Dashboard
  if (cleanUrl.startsWith('/dashboard')) {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          total_banks: 4,
          active_clients: 4,
          global_model_accuracy: 91.8,
          total_predictions: 18450,
          pending_alerts: 3,
          data_drift_status: 'STABLE',
          models_in_production: 2,
          accuracy_by_fl_round: [
            { round: 1, accuracy: 0.74, loss: 0.62 },
            { round: 2, accuracy: 0.81, loss: 0.48 },
            { round: 3, accuracy: 0.86, loss: 0.39 },
            { round: 4, accuracy: 0.89, loss: 0.32 },
            { round: 5, accuracy: 0.918, loss: 0.27 },
          ],
          loss_by_fl_round: [
            { round: 1, loss: 0.62 },
            { round: 2, loss: 0.48 },
            { round: 3, loss: 0.39 },
            { round: 4, loss: 0.32 },
            { round: 5, loss: 0.27 },
          ],
          client_performance: [
            { bank: 'Alpha National', samples: 4500, accuracy: 0.92, status: 'CONNECTED' },
            { bank: 'Beta Federal', samples: 3800, accuracy: 0.90, status: 'CONNECTED' },
            { bank: 'Gamma Trust', samples: 5200, accuracy: 0.93, status: 'CONNECTED' },
            { bank: 'Delta Savings', samples: 2900, accuracy: 0.89, status: 'CONNECTED' },
          ],
          roc_curve: [
            { fpr: 0.0, tpr: 0.0 }, { fpr: 0.05, tpr: 0.65 }, { fpr: 0.1, tpr: 0.82 },
            { fpr: 0.2, tpr: 0.91 }, { fpr: 0.5, tpr: 0.97 }, { fpr: 1.0, tpr: 1.0 },
          ],
          confusion_matrix: [
            [1420, 80],
            [95, 805],
          ],
          data_drift: [
            { feature: 'income', psi: 0.042, status: 'STABLE' },
            { feature: 'credit_score', psi: 0.061, status: 'STABLE' },
            { feature: 'debt_to_income', psi: 0.083, status: 'STABLE' },
          ],
        },
      },
    }
  }

  // Banks
  if (cleanUrl === '/banks') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          items: [
            { id: 'b-1', code: 'BANK-001', name: 'Alpha National Bank', country: 'India', status: 'ACTIVE', client_count: 3, dataset_count: 4, accuracy: 0.92 },
            { id: 'b-2', code: 'BANK-002', name: 'Beta Federal Bank', country: 'United States', status: 'ACTIVE', client_count: 2, dataset_count: 3, accuracy: 0.90 },
            { id: 'b-3', code: 'BANK-003', name: 'Gamma Trust Bank', country: 'United Kingdom', status: 'ACTIVE', client_count: 2, dataset_count: 3, accuracy: 0.93 },
            { id: 'b-4', code: 'BANK-004', name: 'Delta Savings Bank', country: 'Singapore', status: 'ACTIVE', client_count: 1, dataset_count: 2, accuracy: 0.89 },
          ],
          total: 4,
        },
      },
    }
  }

  // Accounts
  if (cleanUrl === '/accounts') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          items: [
            { id: 'acc-1', account_number: 'FED-IND-778291', account_type: 'SAVINGS', currency: 'INR', balance: 450000.0, available_balance: 450000.0, status: 'ACTIVE', ifsc_code: 'FEDB0001001', bank_name: 'Alpha National Bank', upi_vpa: 'rajesh@fedbank', customer: { customer_name: 'Rajesh Kumar' } },
            { id: 'acc-2', account_number: 'FED-IND-883102', account_type: 'CURRENT', currency: 'INR', balance: 1250000.0, available_balance: 1250000.0, status: 'ACTIVE', ifsc_code: 'FEDB0001001', bank_name: 'Alpha National Bank', upi_vpa: 'priya@fedbank', customer: { customer_name: 'Priya Sundaram' } },
            { id: 'acc-3', account_number: 'FED-USD-109283', account_type: 'CURRENT', currency: 'USD', balance: 75000.0, available_balance: 75000.0, status: 'ACTIVE', ifsc_code: 'FEDBUS33', bank_name: 'Beta Federal Bank', upi_vpa: 'marcus@fedbank', customer: { customer_name: 'Marcus Chen' } },
          ],
          total: 3,
        },
      },
    }
  }

  // Payment Rails
  if (cleanUrl === '/payment-rails') {
    return {
      status: 200,
      data: {
        success: true,
        data: [
          { rail_code: 'UPI', rail_name: 'Unified Payments Interface', country_code: 'IN', is_instant: true, max_limit_per_tx: 100000.0, is_active: true },
          { rail_code: 'IMPS', rail_name: 'Immediate Payment Service', country_code: 'IN', is_instant: true, max_limit_per_tx: 500000.0, is_active: true },
          { rail_code: 'NEFT', rail_name: 'National Electronic Funds Transfer', country_code: 'IN', is_instant: false, max_limit_per_tx: 10000000.0, is_active: true },
          { rail_code: 'RTGS', rail_name: 'Real Time Gross Settlement', country_code: 'IN', is_instant: true, max_limit_per_tx: 50000000.0, is_active: true },
          { rail_code: 'SWIFT', rail_name: 'SWIFT Cross-Border Wire', country_code: 'GLOBAL', is_instant: false, max_limit_per_tx: 100000000.0, is_active: true },
          { rail_code: 'SEPA', rail_name: 'Single Euro Payments Area', country_code: 'EU', is_instant: true, max_limit_per_tx: 100000.0, is_active: true },
        ],
      },
    }
  }

  // Currencies
  if (cleanUrl === '/currencies') {
    return {
      status: 200,
      data: {
        success: true,
        data: [
          { code: 'INR', name: 'Indian Rupee', symbol: '₹', exchange_rate_to_usd: 0.0115 },
          { code: 'USD', name: 'US Dollar', symbol: '$', exchange_rate_to_usd: 1.0 },
          { code: 'EUR', name: 'Euro', symbol: '€', exchange_rate_to_usd: 1.08 },
          { code: 'GBP', name: 'British Pound', symbol: '£', exchange_rate_to_usd: 1.27 },
          { code: 'AED', name: 'UAE Dirham', symbol: 'د.إ', exchange_rate_to_usd: 0.272 },
        ],
      },
    }
  }

  // Currency Converter
  if (cleanUrl === '/currencies/convert') {
    const amt = body?.amount || 100
    return {
      status: 200,
      data: {
        success: true,
        data: {
          from_currency: body?.from_currency || 'USD',
          to_currency: body?.to_currency || 'INR',
          original_amount: amt,
          converted_amount: body?.from_currency === 'USD' ? amt * 86.85 : amt / 86.85,
          fx_rate: 86.85,
          formatted: `₹${(amt * 86.85).toLocaleString()}`,
        },
      },
    }
  }

  // Payment Transfer
  if (cleanUrl === '/payments/transfer') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          transaction_reference: `TXN-${Date.now()}`,
          provider_reference: `UPI-${Math.floor(100000000000 + Math.random() * 900000000000)}`,
          status: 'COMPLETED',
          amount: body?.amount || 1000,
          currency: 'INR',
          payment_rail: body?.payment_rail || 'UPI',
          provider_name: 'NPCI UPI Sandbox Simulator',
          clearing_time_ms: 142,
        },
      },
    }
  }

  // UPI Intent QR
  if (cleanUrl === '/payments/upi/create-intent') {
    const amt = body?.amount || 500
    const vpa = body?.payee_vpa || 'store@fedbank'
    return {
      status: 200,
      data: {
        success: true,
        data: {
          qr_payload: `upi://pay?pa=${vpa}&pn=${encodeURIComponent(body?.payee_name || 'FedBank Merchant')}&am=${amt}&cu=INR&tn=${encodeURIComponent(body?.note || 'Payment')}`,
          amount: amt,
          payee_vpa: vpa,
          status: 'INTENT_CREATED',
        },
      },
    }
  }

  // Transactions
  if (cleanUrl === '/transactions') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          items: [
            { id: 'tx-1', reference: 'TXN-882910', amount: 2500.0, currency: 'INR', payment_rail: 'UPI', description: 'Retail Supermarket Payment', fraud_score: 0.05, status: 'COMPLETED', created_at: new Date().toISOString() },
            { id: 'tx-2', reference: 'TXN-882911', amount: 48500.0, currency: 'INR', payment_rail: 'IMPS', description: 'Consulting Advisory Transfer', fraud_score: 0.35, status: 'COMPLETED', created_at: new Date().toISOString() },
            { id: 'tx-3', reference: 'TXN-882912', amount: 150000.0, currency: 'INR', payment_rail: 'NEFT', description: 'Vendor Invoice Settlement', fraud_score: 0.12, status: 'COMPLETED', created_at: new Date().toISOString() },
          ],
          total: 3,
        },
      },
    }
  }

  // Loans
  if (cleanUrl === '/loans') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          items: [
            { id: 'loan-1', loan_number: 'LN-IND-90214', customer_name: 'Rajesh Kumar', principal_amount: 1000000.0, loan_type: 'HOME_LOAN', interest_rate_annual: 8.5, tenure_months: 120, emi_amount: 12398.57, risk_grade: 'A', status: 'ACTIVE' },
            { id: 'loan-2', loan_number: 'LN-IND-90215', customer_name: 'Priya Sundaram', principal_amount: 500000.0, loan_type: 'PERSONAL_LOAN', interest_rate_annual: 11.5, tenure_months: 36, emi_amount: 16492.35, risk_grade: 'BBB', status: 'ACTIVE' },
          ],
          total: 2,
        },
      },
    }
  }

  // Calculate EMI
  if (cleanUrl === '/loans/calculate-emi') {
    const P = body?.principal_amount || 1000000
    const r = (body?.interest_rate_annual || 10.5) / (12 * 100)
    const n = body?.tenure_months || 36
    const emi = (P * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1)
    const totalPayable = emi * n
    return {
      status: 200,
      data: {
        success: true,
        data: {
          monthly_emi: Math.round(emi * 100) / 100,
          total_interest: Math.round((totalPayable - P) * 100) / 100,
          total_payable: Math.round(totalPayable * 100) / 100,
          tenure_months: n,
        },
      },
    }
  }

  // Cards
  if (cleanUrl === '/cards') {
    return {
      status: 200,
      data: {
        success: true,
        data: [
          { id: 'c-1', card_type: 'DEBIT', card_network: 'RUPAY', cardholder_name: 'RAJESH KUMAR', card_number_masked: '•••• •••• •••• 4892', expiry_month: '08', expiry_year: '28', status: 'ACTIVE', credit_limit: null },
          { id: 'c-2', card_type: 'CREDIT', card_network: 'VISA', cardholder_name: 'PRIYA SUNDARAM', card_number_masked: '•••• •••• •••• 9912', expiry_month: '11', expiry_year: '29', status: 'ACTIVE', credit_limit: 250000.0 },
          { id: 'c-3', card_type: 'VIRTUAL', card_network: 'MASTERCARD', cardholder_name: 'MARCUS CHEN', card_number_masked: '•••• •••• •••• 3341', expiry_month: '04', expiry_year: '27', status: 'ACTIVE', credit_limit: 100000.0 },
        ],
      },
    }
  }

  // KYC Verification
  if (cleanUrl === '/kyc/verify-pan') {
    const pan = body?.pan_number || ''
    const isValid = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(pan.toUpperCase())
    return {
      status: 200,
      data: {
        success: true,
        data: {
          pan_number: pan,
          status: isValid ? 'VALID' : 'INVALID_FORMAT',
          is_sandbox: true,
          name_match_score: isValid ? 96.5 : 0.0,
          provider: 'NSDL / Income Tax Department Sandbox Adapter',
        },
      },
    }
  }

  if (cleanUrl === '/kyc/verify-aadhaar') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          aadhaar_masked: 'XXXX-XXXX-1099',
          status: 'VERIFIED',
          vault_token: `VAULT-TOKEN-${Date.now()}`,
          is_sandbox: true,
          provider: 'UIDAI Gateway Demographic Sandbox Adapter',
        },
      },
    }
  }

  if (cleanUrl === '/kyc/cases') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          items: [
            { id: 'k-1', case_number: 'KYC-2026-001', customer_name: 'Rajesh Kumar', verification_score: 95.0, pan_verified: true, aadhaar_verified: true, status: 'APPROVED' },
            { id: 'k-2', case_number: 'KYC-2026-002', customer_name: 'Vikram Malhotra', verification_score: 92.0, pan_verified: true, aadhaar_verified: true, status: 'APPROVED' },
          ],
          total: 2,
        },
      },
    }
  }

  // AML Alerts
  if (cleanUrl === '/aml/alerts') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          items: [
            { id: 'aml-1', alert_code: 'AML-STR-091', customer_name: 'Rajesh Kumar', alert_type: 'STRUCTURING', severity: 'HIGH', status: 'OPEN', resolution_notes: 'Transaction ₹48,500 just below ₹50,000 reporting limit' },
            { id: 'aml-2', alert_code: 'AML-VEL-092', customer_name: 'Unknown Payee', alert_type: 'VELOCITY', severity: 'MEDIUM', status: 'RESOLVED', resolution_notes: '4 transactions within 8 minutes' },
          ],
          total: 2,
        },
      },
    }
  }

  // Sanctions
  if (cleanUrl === '/sanctions/watchlist') {
    return {
      status: 200,
      data: {
        success: true,
        data: [
          { id: 'w-1', entity_name: 'Viktor Anatoly Chernov', entity_type: 'INDIVIDUAL', country_code: 'RU', list_source: 'OFAC_SYNTHETIC' },
          { id: 'w-2', entity_name: 'Al-Sham Trading Enterprises', entity_type: 'ENTITY', country_code: 'SY', list_source: 'UN_SANCTIONS_SYNTHETIC' },
          { id: 'w-3', entity_name: 'Pyongyang Heavy Marine Ltd', entity_type: 'ENTITY', country_code: 'KP', list_source: 'OFAC_SYNTHETIC' },
          { id: 'w-4', entity_name: 'Rajesh Kumar Defaulter Group', entity_type: 'ENTITY', country_code: 'IN', list_source: 'RBI_DEFAULTER_SYNTHETIC' },
        ],
      },
    }
  }

  if (cleanUrl === '/sanctions/screen') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          query_name: 'Viktor Chernov',
          is_flagged: true,
          total_matches: 1,
          matches: [
            { id: 'm-1', match_type: 'FUZZY', match_score: 88.0, notes: 'Fuzzy match score: 88% with watchlist entity Viktor Anatoly Chernov (OFAC_SYNTHETIC).' },
          ],
        },
      },
    }
  }

  // Data Drift
  if (cleanUrl.startsWith('/data-drift')) {
    return {
      status: 200,
      data: {
        success: true,
        data: [
          { id: 'd-1', feature_name: 'income', drift_method: 'POPULATION_STABILITY_INDEX', drift_score: 0.042, ks_statistic: 0.035, p_value: 0.88, threshold: 0.10, status: 'NO_DRIFT' },
          { id: 'd-2', feature_name: 'credit_score', drift_method: 'POPULATION_STABILITY_INDEX', drift_score: 0.061, ks_statistic: 0.048, p_value: 0.65, threshold: 0.10, status: 'NO_DRIFT' },
          { id: 'd-3', feature_name: 'debt_to_income', drift_method: 'POPULATION_STABILITY_INDEX', drift_score: 0.083, ks_statistic: 0.062, p_value: 0.42, threshold: 0.10, status: 'NO_DRIFT' },
          { id: 'd-4', feature_name: 'loan_amount', drift_method: 'POPULATION_STABILITY_INDEX', drift_score: 0.142, ks_statistic: 0.115, p_value: 0.04, threshold: 0.10, status: 'WARNING' },
        ],
      },
    }
  }

  // Datasets
  if (cleanUrl === '/datasets') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          items: [
            { id: 'ds-1', name: 'Alpha Bank Credit Risk v1', bank_name: 'Alpha National Bank', records_count: 50000, quality_score: 98.5, status: 'VERIFIED', created_at: new Date().toISOString() },
            { id: 'ds-2', name: 'Beta Bank SME Portfolio', bank_name: 'Beta Federal Bank', records_count: 35000, quality_score: 96.2, status: 'VERIFIED', created_at: new Date().toISOString() },
            { id: 'ds-3', name: 'Gamma Trust Mortgages', bank_name: 'Gamma Trust Bank', records_count: 42000, quality_score: 97.8, status: 'VERIFIED', created_at: new Date().toISOString() },
          ],
          total: 3,
        },
      },
    }
  }

  // Models
  if (cleanUrl === '/models') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          items: [
            { id: 'm-1', name: 'fedbank_credit_risk_global', version: 'v2.4', algorithm: 'RandomForestClassifier', stage: 'Production', accuracy: 0.918, auc_roc: 0.942, f1_score: 0.884, created_at: new Date().toISOString() },
            { id: 'm-2', name: 'fedbank_fraud_detector', version: 'v1.8', algorithm: 'GradientBoostingClassifier', stage: 'Staging', accuracy: 0.945, auc_roc: 0.961, f1_score: 0.912, created_at: new Date().toISOString() },
          ],
          total: 2,
        },
      },
    }
  }

  // Jobs
  if (cleanUrl === '/jobs') {
    return {
      status: 200,
      data: {
        success: true,
        data: {
          items: [
            { id: 'job-01', title: 'Federated Global Round #5 Aggregation', job_type: 'FEDERATED_AGGREGATION', progress_percent: 100, current_step: 'Completed Flower FedAvg weights merge', status: 'COMPLETED', created_at: new Date().toISOString() },
            { id: 'job-02', title: 'Dataset Drift PSI Batch Analysis', job_type: 'DRIFT_EVALUATION', progress_percent: 65, current_step: 'Computing 2-sample Kolmogorov-Smirnov test', status: 'RUNNING', created_at: new Date().toISOString() },
          ],
          total: 2,
        },
      },
    }
  }

  // Default Generic List
  return {
    status: 200,
    data: {
      success: true,
      data: {
        items: [],
        total: 0,
      },
    },
  }
}

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    // 401 Token Refresh
    if (err.response?.status === 401) {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh && !err.config._retry) {
        err.config._retry = true
        try {
          const { data } = await axios.post(`${API_BASE}/api/v1/auth/refresh`, { refresh_token: refresh })
          localStorage.setItem('access_token', data.access_token)
          err.config.headers.Authorization = `Bearer ${data.access_token}`
          return api(err.config)
        } catch {
          // If refresh fails on demo preview, don't force logout
        }
      }
    }

    // Static Hosting / Netlify Offline Fallback Handler
    if (!err.response || err.response?.status === 404 || err.code === 'ERR_NETWORK') {
      const mock = getMockResponse(err.config.url, err.config.method, err.config.data ? JSON.parse(err.config.data) : null)
      if (mock) {
        return Promise.resolve(mock as any)
      }
    }

    return Promise.reject(err)
  },
)

export default api
