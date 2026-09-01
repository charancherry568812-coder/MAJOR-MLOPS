import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import ToastContainer from './components/ToastContainer'
import LoginPage from './pages/LoginPage'

const Dashboard = lazy(() => import('./pages/DashboardPage'))
const Banks = lazy(() => import('./pages/BanksPage'))
const BankDetail = lazy(() => import('./pages/BankDetailPage'))
const Clients = lazy(() => import('./pages/ClientsPage'))
const Datasets = lazy(() => import('./pages/DatasetsPage'))
const DatasetDetail = lazy(() => import('./pages/DatasetDetailPage'))
const FederatedTraining = lazy(() => import('./pages/FederatedTrainingPage'))
const FederatedRounds = lazy(() => import('./pages/FederatedRoundsPage'))
const Pipeline = lazy(() => import('./pages/PipelinePage'))
const Experiments = lazy(() => import('./pages/ExperimentsPage'))
const TrainingRuns = lazy(() => import('./pages/TrainingRunsPage'))
const Models = lazy(() => import('./pages/ModelsPage'))
const ModelDetail = lazy(() => import('./pages/ModelDetailPage'))
const ModelCompare = lazy(() => import('./pages/ModelComparePage'))
const Deployments = lazy(() => import('./pages/DeploymentsPage'))
const SinglePrediction = lazy(() => import('./pages/SinglePredictionPage'))
const BatchPrediction = lazy(() => import('./pages/BatchPredictionPage'))
const PredictionHistory = lazy(() => import('./pages/PredictionHistoryPage'))
const Explainability = lazy(() => import('./pages/ExplainabilityPage'))
const Fraud = lazy(() => import('./pages/FraudPage'))
const ModelMonitoring = lazy(() => import('./pages/ModelMonitoringPage'))
const DataDrift = lazy(() => import('./pages/DataDriftPage'))
const SystemHealth = lazy(() => import('./pages/SystemHealthPage'))
const Alerts = lazy(() => import('./pages/AlertsPage'))
const AuditLogs = lazy(() => import('./pages/AuditLogsPage'))
const Users = lazy(() => import('./pages/UsersPage'))
const Security = lazy(() => import('./pages/SecurityPage'))
const Reports = lazy(() => import('./pages/ReportsPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))

// Banking & Enterprise Portals
const PaymentsHub = lazy(() => import('./pages/PaymentsHubPage'))
const Accounts = lazy(() => import('./pages/AccountsPage'))
const Loans = lazy(() => import('./pages/LoansPage'))
const Cards = lazy(() => import('./pages/CardsPage'))
const ComplianceHub = lazy(() => import('./pages/ComplianceHubPage'))
const Jobs = lazy(() => import('./pages/JobsPage'))

function Loading() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
    </div>
  )
}

export default function App() {
  return (
    <>
      <ToastContainer />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<Loading />}>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    
                    {/* Banking & Rails */}
                    <Route path="/banking/payments" element={<PaymentsHub />} />
                    <Route path="/banking/accounts" element={<Accounts />} />
                    <Route path="/banking/loans" element={<Loans />} />
                    <Route path="/banking/cards" element={<Cards />} />
                    <Route path="/banks" element={<Banks />} />
                    <Route path="/banks/:id" element={<BankDetail />} />

                    {/* Risk & Compliance */}
                    <Route path="/compliance" element={<ComplianceHub />} />
                    <Route path="/fraud" element={<Fraud />} />
                    <Route path="/reports" element={<Reports />} />

                    {/* Data Management */}
                    <Route path="/datasets" element={<Datasets />} />
                    <Route path="/datasets/:id" element={<DatasetDetail />} />

                    {/* Federated Learning */}
                    <Route path="/federated-training" element={<FederatedTraining />} />
                    <Route path="/federated-training/:id" element={<FederatedTraining />} />
                    <Route path="/federated/training" element={<FederatedTraining />} />
                    <Route path="/federated/clients" element={<Clients />} />
                    <Route path="/federated/rounds" element={<FederatedRounds />} />

                    {/* MLOps Pipeline */}
                    <Route path="/pipeline" element={<Pipeline />} />

                    {/* Machine Learning & Models */}
                    <Route path="/experiments" element={<Experiments />} />
                    <Route path="/training-runs" element={<TrainingRuns />} />
                    <Route path="/models" element={<Models />} />
                    <Route path="/models/compare" element={<ModelCompare />} />
                    <Route path="/models/:id" element={<ModelDetail />} />
                    <Route path="/deployments" element={<Deployments />} />

                    {/* Predictions */}
                    <Route path="/predictions" element={<SinglePrediction />} />
                    <Route path="/predictions/single" element={<SinglePrediction />} />
                    <Route path="/predictions/batch" element={<BatchPrediction />} />
                    <Route path="/predictions/history" element={<PredictionHistory />} />
                    <Route path="/explainability" element={<Explainability />} />

                    {/* Monitoring */}
                    <Route path="/monitoring" element={<ModelMonitoring />} />
                    <Route path="/monitoring/model" element={<ModelMonitoring />} />
                    <Route path="/monitoring/drift" element={<DataDrift />} />
                    <Route path="/monitoring/system" element={<SystemHealth />} />

                    {/* Governance & Operations */}
                    <Route path="/jobs" element={<Jobs />} />
                    <Route path="/alerts" element={<Alerts />} />
                    <Route path="/audit-logs" element={<AuditLogs />} />
                    <Route path="/users" element={<Users />} />
                    <Route path="/security" element={<Security />} />
                    <Route path="/settings" element={<SettingsPage />} />

                    {/* Fallback */}
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  )
}
