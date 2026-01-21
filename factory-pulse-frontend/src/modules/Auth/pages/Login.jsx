import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../../shared/contexts/AuthContext';
import { useApp } from '../../../shared/contexts/AppContext'; 
import { Activity, Lock, User } from 'lucide-react';
import LanguageThemeControl from '../../../shared/components/LanguageThemeControl';

/**
 * Login Page Component.
 * Handles user authentication via the AuthContext.
 * Provides access to password recovery and account registration.
 */
export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  const { login } = useAuth();
  const { t } = useApp();
  const navigate = useNavigate();

  /**
   * Handles the form submission.
   * Calls the login function and redirects to the dashboard on success.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await login(username, password);
    if (result.success) {
      navigate('/');
    } else {
      setError(t('credential_error'));
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white relative overflow-hidden transition-colors duration-300">
      
      {/* Shared Theme & Language Controls */}
      <LanguageThemeControl />

      {/* Decorative Background Effect */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-blue-600/20 blur-[120px] rounded-full hidden dark:block pointer-events-none"></div>
      
      {/* Main Login Card */}
      <div className="bg-white dark:bg-slate-800/60 p-8 rounded-2xl border border-slate-200 dark:border-white/10 w-full max-w-md backdrop-blur-xl shadow-2xl relative z-10 mx-4">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-600/20 rounded-xl text-blue-600 dark:text-blue-500">
              <Activity size={40} />
            </div>
          </div>
          <h1 className="text-2xl font-bold">FactoryPulse</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">{t('welcome')}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && <div className="p-3 bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 text-sm rounded-lg text-center border border-red-200 dark:border-red-500/20">{error}</div>}
          
          <div>
            <label className="block text-sm font-medium text-slate-600 dark:text-slate-400 mb-2">{t('user_label')}</label>
            <div className="relative">
              <User className="absolute left-3 top-3 text-slate-400" size={20} />
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} 
                className="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700 rounded-lg py-2.5 pl-10 text-slate-900 dark:text-white" required />
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-2">
              <label className="block text-sm font-medium text-slate-600 dark:text-slate-400">{t('password_label')}</label>
              <Link to="/forgot-password" className="text-xs text-blue-600 dark:text-blue-400 hover:underline">
                {t('forgot_password') || 'Esqueceu a senha?'}
              </Link>
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-3 text-slate-400" size={20} />
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700 rounded-lg py-2.5 pl-10 text-slate-900 dark:text-white" required />
            </div>
          </div>

          <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition-all shadow-lg shadow-blue-600/20">{t('enter_btn')}</button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
          {t('no_account') || 'Não tem uma conta?'} <Link to="/register" className="text-blue-600 dark:text-blue-400 font-bold hover:underline">{t('create_account') || 'Criar agora'}</Link>
        </div>
      </div>
    </div>
  );
}