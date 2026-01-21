import React from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft } from 'lucide-react';
import { useApp } from '../../../shared/contexts/AppContext';
import LanguageThemeControl from '../../../shared/components/LanguageThemeControl';

/**
 * Password Recovery Page.
 * Allows users to request a password reset link via email.
 * Includes a mock form submission for demonstration purposes.
 */
export default function ForgotPassword() {
  const { t } = useApp();

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white relative transition-colors duration-300">
      
      {/* Shared Theme & Language Controls */}
      <LanguageThemeControl />

      <div className="bg-white dark:bg-slate-800/60 p-8 rounded-2xl border border-slate-200 dark:border-white/10 w-full max-w-md backdrop-blur-xl shadow-2xl mx-4 relative z-10">
        <Link to="/login" className="flex items-center text-slate-500 dark:text-slate-400 text-sm mb-6 hover:text-blue-600 dark:hover:text-white transition-colors">
            <ArrowLeft size={16} className="mr-2"/> {t('back_login')}
        </Link>
        <h1 className="text-2xl font-bold mb-2">{t('recover_title')}</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">{t('recover_desc')}</p>
        
        {/* Mock Form Submission */}
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); alert('Link enviado (Simulação)'); }}>
          <div className="relative">
            <Mail className="absolute left-3 top-3 text-slate-400" size={20} />
            <input type="email" placeholder="seu@email.com" className="w-full bg-slate-50 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-700 rounded-lg py-2.5 pl-10 text-slate-900 dark:text-white" required />
          </div>
          <button className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg shadow-lg shadow-blue-600/20">
            {t('send_link_btn')}
          </button>
        </form>
      </div>
    </div>
  );
}