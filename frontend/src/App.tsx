import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Licenses from './pages/Licenses'
import LicenseDetail from './pages/LicenseDetail'
import Devices from './pages/Devices'
import Layout from './components/Layout'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="licenses" element={<Licenses />} />
          <Route path="licenses/:id" element={<LicenseDetail />} />
          <Route path="devices" element={<Devices />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default App
