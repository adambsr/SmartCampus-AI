import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import CandidateLandingPage from './pages/CandidateLandingPage'
import ResponsibleDashboard from './pages/ResponsibleDashboard'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CandidateLandingPage />} />
        <Route path="/staff" element={<ResponsibleDashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
