import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import CandidateLandingPage from './pages/CandidateLandingPage'
import CandidateAccountPage from './pages/CandidateAccountPage'
import AuthPage from './pages/AuthPage'
import ResponsibleDashboard from './pages/ResponsibleDashboard'
import { AuthProvider } from './components/shared/AuthProvider'
import { useAuth } from './components/shared/AuthContext'

function ProtectedRoute({ staff = false, children }: { staff?: boolean; children: React.ReactNode }) {
  const { account, loading } = useAuth()
  if (loading) return <div className="auth-loading">Vérification de la session…</div>
  if (!account) return <Navigate to={`/login?next=${staff ? '/staff' : '/candidate'}`} replace />
  if (staff && account.role === 'candidate') return <Navigate to="/candidate" replace />
  if (!staff && account.role !== 'candidate') return <Navigate to="/staff" replace />
  return children
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<CandidateLandingPage />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/register" element={<AuthPage mode="register" />} />
          <Route path="/activate" element={<AuthPage mode="activate" />} />
          <Route path="/candidate" element={<ProtectedRoute><CandidateAccountPage /></ProtectedRoute>} />
          <Route path="/staff" element={<ProtectedRoute staff><ResponsibleDashboard /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
