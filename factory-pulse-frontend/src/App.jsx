import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './shared/contexts/AppContext';
import { AuthProvider, useAuth } from './shared/contexts/AuthContext';

// Layouts and Pages
import MainLayout from './shared/components/MainLayout';
import Login from './modules/Auth/pages/Login';
import Register from './modules/Auth/pages/Register';
import ForgotPassword from './modules/Auth/pages/ForgotPassword';
import DashboardHome from './modules/Dashboard/pages/DashboardHome';
import MachineList from './modules/Machines/pages/MachineList';
import MachineDashboard from './modules/Machines/pages/MachineDashboard';
import Reports from './modules/Reports/pages/Reports';

/**
 * Protected Route Wrapper.
 * Checks if the user is authenticated via AuthContext.
 * If authenticated, renders the child component; otherwise, redirects to Login.
 */
const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return null; // Wait for session check
  return user ? children : <Navigate to="/login" />;
};

// Placeholder Component for future Alerts Module
const AlertsPlaceholder = () => (
  <div className="p-10 text-slate-500 dark:text-slate-400">
    Alerts Module (Under Construction)
  </div>
);

/**
 * Root Application Component.
 * Initializes Global Providers (App & Auth) and defines the Application Routing.
 */
export default function App() {
  return (
    <AppProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Authentication Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />

            {/* Protected Routes (Require Authentication) */}
            <Route element={<PrivateRoute><MainLayout /></PrivateRoute>}>
              <Route path="/" element={<DashboardHome />} />
              <Route path="/machines" element={<MachineList />} />
              <Route path="/machine/:id" element={<MachineDashboard />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/alerts" element={<AlertsPlaceholder />} />
            </Route>

            {/* Fallback Route */}
            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </AppProvider>
  );
}