import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import LandingPage from './pages/LandingPage'
import CatalogPage from './pages/CatalogPage'
import ProgramDetailPage from './pages/ProgramDetailPage'
import CandidateDashboardPage from './pages/CandidateDashboardPage'
import CandidateConversationPage from './pages/CandidateConversationPage'
import AuthPage from './pages/AuthPage'
import GuestChatPage from './pages/GuestChatPage'
import StaffDashboardPage from './pages/StaffDashboardPage'
import StaffDossierPage from './pages/StaffDossierPage'
import AdminUsersPage from './pages/AdminUsersPage'
import { AuthProvider } from './components/shared/AuthProvider'
import { useAuth } from './components/shared/AuthContext'

function ProtectedRoute({ role = 'candidate', children }: { role?: 'candidate' | 'staff' | 'admin' | 'dossier'; children: React.ReactNode }) {
  const { account, loading } = useAuth()
  if (loading) return <div className="auth-loading">Vérification de la session…</div>
  if (!account) return <Navigate to={`/login?next=${role === 'candidate' ? '/candidate' : '/staff'}`} replace />
  if (!['candidate', 'interviewer', 'admin'].includes(account.role)) return <Navigate to="/login" replace />
  if (role === 'candidate' && account.role !== 'candidate') return <Navigate to="/staff" replace />
  if (role !== 'candidate' && !['interviewer', 'admin'].includes(account.role)) return <Navigate to="/candidate" replace />
  if (role === 'admin' && account.role !== 'admin') return <Navigate to="/staff" replace />
  if (role === 'dossier' && !['interviewer', 'admin'].includes(account.role)) return <Navigate to="/staff" replace />
  return children
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/programs/:code" element={<ProgramDetailPage />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/register" element={<AuthPage mode="register" />} />
          <Route path="/activate" element={<AuthPage mode="activate" />} />
          <Route path="/chat" element={<GuestChatPage />} />
          <Route path="/candidate" element={<ProtectedRoute><CandidateDashboardPage /></ProtectedRoute>} />
          <Route path="/candidate/conversations/:id" element={<ProtectedRoute><CandidateConversationPage /></ProtectedRoute>} />
          <Route path="/staff" element={<ProtectedRoute role="staff"><StaffDashboardPage /></ProtectedRoute>} />
          <Route path="/staff/dossiers" element={<ProtectedRoute role="dossier"><StaffDossierPage /></ProtectedRoute>} />
          <Route path="/staff/dossiers/:id" element={<ProtectedRoute role="dossier"><StaffDossierPage /></ProtectedRoute>} />
          <Route path="/staff/users" element={<ProtectedRoute role="admin"><AdminUsersPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
