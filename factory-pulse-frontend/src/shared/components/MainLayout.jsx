import React from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Activity, Bell, Search, Monitor, FileText, LogOut, AlertTriangle } from 'lucide-react';
import { useApp } from '../contexts/AppContext';
import { useAuth } from '../contexts/AuthContext';
import LanguageThemeControl from './LanguageThemeControl';
import AssistantChat from './AssistantChat';

/**
 * Main Application Layout.
 * Contains the Sidebar, Top Navigation Bar, and the Content Area (Outlet).
 * Handles responsive layout structure and global navigation.
 */
export default function MainLayout() {
  const { t } = useApp();
  const { logout, user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  /**
   * Checks if the current path matches the link to apply active styling.
   * Special case for 'machines' to keep the tab active when viewing details.
   */
  const isActive = (path) => location.pathname === path || (path === '/machines' && location.pathname.startsWith('/machine/'));

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white transition-colors duration-300 font-sans">
      
      {/* Sidebar Navigation */}
      <aside className="w-64 hidden md:flex flex-col border-r border-slate-200 dark:border-white/5 bg-white dark:bg-slate-900 z-50">
        <div className="h-20 flex items-center px-6 border-b border-slate-200 dark:border-white/5">
          <Activity className="text-blue-600 dark:text-blue-500" size={28} />
          <div className="ml-3">
            <h1 className="font-bold text-lg leading-none text-slate-800 dark:text-white">FactoryPulse</h1>
            <span className="text-xs text-slate-500">Industry 4.0</span>
          </div>
        </div>

        <nav className="flex-1 py-6 px-3 space-y-1">
          <Link to="/" className={`flex items-center p-3 rounded-xl transition-all ${isActive('/') ? 'bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 font-bold' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5'}`}>
            <LayoutDashboard size={20} />
            <span className="ml-3">{t('dashboard')}</span>
          </Link>
          
          <Link to="/machines" className={`flex items-center p-3 rounded-xl transition-all ${isActive('/machines') ? 'bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 font-bold' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5'}`}>
            <Monitor size={20} />
            <span className="ml-3">{t('machines')}</span>
          </Link>

          <Link to="/reports" className={`flex items-center p-3 rounded-xl transition-all ${isActive('/reports') ? 'bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 font-bold' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5'}`}>
            <FileText size={20} />
            <span className="ml-3">{t('reports')}</span>
          </Link>

          <Link to="/alerts" className={`flex items-center p-3 rounded-xl transition-all ${isActive('/alerts') ? 'bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 font-bold' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5'}`}>
            <AlertTriangle size={20} />
            <span className="ml-3">{t('alerts')}</span>
          </Link>

          <div className="pt-4 mt-4 border-t border-slate-200 dark:border-white/5">
            <button onClick={handleLogout} className="w-full flex items-center p-3 rounded-xl text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors">
              <LogOut size={20} />
              <span className="ml-3">{t('logout')}</span>
            </button>
          </div>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden relative">
        <header className="h-20 border-b border-slate-200 dark:border-white/5 flex items-center justify-between px-8 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md z-40 sticky top-0">
          <div className="flex items-center text-slate-400 bg-slate-100 dark:bg-slate-800 px-4 py-2 rounded-full border border-slate-200 dark:border-white/5 w-96">
            <Search size={18} />
            <input type="text" placeholder={t('search')} className="bg-transparent border-none outline-none ml-3 text-sm w-full text-slate-700 dark:text-white placeholder-slate-400" />
          </div>
          
          <div className="flex items-center gap-6">
            
            {/* Reusable Control Component (Inline positioning) */}
            <LanguageThemeControl className="flex items-center gap-4" />

            <div className="h-6 w-px bg-slate-200 dark:bg-white/10"></div>
            
            <div className="relative">
              <Bell size={22} className="text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white transition-colors" />
              <span className="absolute top-0 right-0 w-2.5 h-2.5 bg-red-500 border-2 border-white dark:border-slate-900 rounded-full"></span>
            </div>

            <div className="text-right hidden lg:block border-l border-slate-200 dark:border-white/10 pl-4">
               <p className="text-sm font-bold text-slate-700 dark:text-white">{user?.username || 'User'}</p>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto relative z-10 p-0">
          <Outlet />
        </div>
      </main>

      {/* AI Assistant — floating chat available across every protected page */}
      <AssistantChat />
    </div>
  );
}