import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../shared/contexts/AuthContext';
import { useApp } from '../../../shared/contexts/AppContext'; 
import { Mail, Lock, User } from 'lucide-react';
import LanguageThemeControl from '../../../shared/components/LanguageThemeControl';

/**
 * Registration Page Component.
 * Allows new users to sign up for an account.
 * Integrates with AuthContext for backend communication and AppContext for localization.
 */
export default function Register() {
  const [formData, setFormData] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { register } = useAuth();
  const { t } = useApp();
  const navigate = useNavigate();

  /**
   * Handles user registration form submission.
   * Calls the auth provider's register method and handles redirection or error states.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const result = await register(formData.username, formData.email, formData.password);
    if (result.success) {
      navigate('/');
    } else { 
      setError(result.message); 
      setLoading(false); 
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white relative transition-colors duration-300">
      
      {/* Shared Theme & Language Controls */}
      <LanguageThemeControl />

      <div className="bg-white dark:bg-slate-800/60 p-8 rounded-2xl border border-slate-200 dark:border-white/10 w-full max-w-md backdrop-blur-xl relative z-10 shadow-2xl mx-4">
        <h1 className="text-2xl font-bold text-center mb-6">{t('register_title')}</h1>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <div className="p-3 bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 text-sm rounded-lg border border-red-200 dark:border-red-500/20">{error}</div>}
          
          <div className="relative">
            <User className="absolute left-3 top-3 text-slate-400" size={20} />
            <input type="text" placeholder={t('user_label')} value={formData.username} onChange={(e) => setFormData({...formData, username: e.target.value})}
              className="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700 rounded-lg py-2.5 pl-10 text-slate-900 dark:text-white" required />
          </div>
          
          <div className="relative">
            <Mail className="absolute left-3 top-3 text-slate-400" size={20} />
            <input type="email" placeholder={t('email_label')} value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700 rounded-lg py-2.5 pl-10 text-slate-900 dark:text-white" required />
          </div>

          <div className="relative">
            <Lock className="absolute left-3 top-3 text-slate-400" size={20} />
            <input type="password" placeholder={t('password_label')} value={formData.password} onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700 rounded-lg py-2.5 pl-10 text-slate-900 dark:text-white" required />
          </div>

          <button type="submit" disabled={loading} className="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-lg transition-all shadow-lg shadow-green-600/20">
            {loading ? '...' : t('register_btn')}
          </button>
        </form>
        <div className="mt-4 text-center text-sm text-slate-500 dark:text-slate-400">
          {t('already_account')} <Link to="/login" className="text-blue-600 dark:text-blue-400 font-bold hover:underline">{t('do_login')}</Link>
        </div>
      </div>
    </div>
  );
}