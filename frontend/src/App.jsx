import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'

import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import LeadPipeline from './pages/LeadPipeline'
import Organizations from './pages/Organizations'
import Contacts from './pages/Contacts'
import Opportunities from './pages/Opportunities'
import EnrichmentQueue from './pages/EnrichmentQueue'
import CampaignManager from './pages/CampaignManager'
import SuppressionManager from './pages/SuppressionManager'
import ErrorCenter from './pages/ErrorCenter'
import HealthDashboard from './pages/HealthDashboard'

function ProtectedRoute({ children, roles = [] }) {
  const { user, hasRole } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (roles.length > 0 && !roles.some(r => hasRole(r))) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-center">
        <h2 className="text-xl font-bold text-gray-900 mb-2">Access Denied</h2>
        <p className="text-gray-500 text-sm">You don't have permission to view this page.</p>
      </div>
    )
  }
  return children
}

function AppRoutes() {
  const { user } = useAuth()

  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <LoginPage />}
      />

      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/pipeline" element={<LeadPipeline />} />
                <Route path="/organizations" element={<Organizations />} />
                <Route path="/contacts" element={<Contacts />} />
                <Route path="/opportunities" element={<Opportunities />} />
                <Route
                  path="/enrichment"
                  element={
                    <ProtectedRoute roles={['researcher', 'admin']}>
                      <EnrichmentQueue />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/campaigns"
                  element={
                    <ProtectedRoute roles={['campaign_manager', 'admin']}>
                      <CampaignManager />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/suppression"
                  element={
                    <ProtectedRoute roles={['campaign_manager', 'admin']}>
                      <SuppressionManager />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/errors"
                  element={
                    <ProtectedRoute roles={['admin']}>
                      <ErrorCenter />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/health"
                  element={
                    <ProtectedRoute roles={['admin']}>
                      <HealthDashboard />
                    </ProtectedRoute>
                  }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
