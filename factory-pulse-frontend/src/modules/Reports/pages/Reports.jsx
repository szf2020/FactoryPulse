import React from 'react';
import { FileText, Download } from 'lucide-react';
import { useApp } from '../../../shared/contexts/AppContext';

/**
 * Reports Page Component.
 * * @note THIS MODULE IS A STATIC DEMO (MOCK).
 * It currently displays placeholder data for visual demonstration purposes.
 * Future implementation required: Connect to the backend Reporting API to fetch real generated reports.
 */
export default function Reports() {
  const { t } = useApp();

  return (
    <div className="p-8 max-w-7xl mx-auto animate-fade-in">
      <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-6">{t('reports_title')}</h1>
      
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-white/5 overflow-hidden">
        {/* Mock Data Mapping - Simulating a list of recent reports */}
        {[1, 2, 3].map(i => (
          <div key={i} className="flex items-center justify-between p-4 border-b border-slate-100 dark:border-white/5 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
            <div className="flex items-center gap-4">
              <div className="p-2 bg-blue-100 dark:bg-blue-500/20 text-blue-600 rounded-lg">
                <FileText size={20} />
              </div>
              <div>
                <p className="font-bold text-slate-800 dark:text-white">{t('report_name')} {i}</p>
                <p className="text-xs text-slate-500">{t('generated_on')} 21/01/2026</p>
              </div>
            </div>
            <button className="p-2 text-slate-400 hover:text-blue-500" title="Download (Demo)">
                <Download size={20}/>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}