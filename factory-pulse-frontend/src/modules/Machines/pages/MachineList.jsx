import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, Zap, Server, ImageOff } from 'lucide-react';
import { useApp } from '../../../shared/contexts/AppContext';
import api from '../../../shared/services/api';

/**
 * Machine List Page.
 * Fetches and displays a grid of all available machines.
 * Calculates and shows the Real-time OEE for each machine.
 */
export default function MachineList() {
  const { t } = useApp();
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);

  /**
   * Fetches machine list from the API on mount.
   */
  useEffect(() => {
    api.get('machines/')
      .then(response => {
        setMachines(response.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("API Error:", err);
        setLoading(false);
      });
  }, []);

  /**
   * Helper to construct absolute image URLs.
   * Ensures the URL points to the correct Django backend server.
   * @param {string} path - The relative image path.
   */
  const getImageUrl = (path) => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `http://127.0.0.1:8000${cleanPath}`;
  };

  /**
   * Calculates the Global OEE (Overall Equipment Effectiveness).
   * If the backend provides a pre-calculated 'global' value, it uses that.
   * Otherwise, it computes the average of Availability, Performance, and Quality.
   * * @param {Object} oeeData - Object containing OEE metrics.
   * @returns {number} - The rounded OEE percentage.
   */
  const calculateOEE = (oeeData) => {
    if (!oeeData) return 0;
    
    // Use pre-calculated global value if available
    if (oeeData.global && oeeData.global > 0) return oeeData.global;
    
    // Fallback: Calculate arithmetic mean of the 3 metrics
    const avg = (
      (oeeData.availability || 0) + 
      (oeeData.performance || 0) + 
      (oeeData.quality || 0)
    ) / 3;
    
    return Math.round(avg);
  };

  if (loading) return <div className="p-10 text-center text-slate-500 animate-pulse">Loading...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto animate-fade-in">
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{t('machine_list')}</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">{t('machine_desc')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {machines.map((machine) => (
          <Link 
            key={machine.id} 
            to={`/machine/${machine.device_id}`}
            className="group bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-white/10 overflow-hidden hover:shadow-xl hover:border-blue-500/50 dark:hover:border-blue-500/50 transition-all duration-300"
          >
            <div className="h-48 overflow-hidden relative bg-slate-200 dark:bg-slate-800 flex items-center justify-center">
              {machine.image ? (
                <img 
                  src={getImageUrl(machine.image)} 
                  alt={machine.name}
                  // Fallback to placeholder if image load fails
                  onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
              ) : null}
              
              <div className="hidden absolute inset-0 items-center justify-center bg-slate-200 dark:bg-slate-800 text-slate-400 flex-col" style={{ display: machine.image ? 'none' : 'flex' }}>
                <ImageOff size={32} className="mb-2 opacity-50" />
                <span className="text-xs font-bold">No Image</span>
              </div>
              
              <div className={`absolute top-3 right-3 text-white text-xs font-bold px-2 py-1 rounded shadow-sm z-10 ${machine.status === 'OFFLINE' ? 'bg-red-500' : 'bg-green-500'}`}>
                {t(machine.status) || machine.status}
              </div>
            </div>

            <div className="p-6">
              <span className="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                {t(machine.machine_type) || machine.machine_type}
              </span>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-1 group-hover:text-blue-500 transition-colors">
                {machine.name}
              </h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm mb-6 line-clamp-2 h-10 mt-2">
                {t(machine.description) || machine.description}
              </p>

              <div className="grid grid-cols-2 gap-4 border-t border-slate-100 dark:border-white/5 pt-4">
                <div className="text-center">
                  <div className="text-xs text-slate-400 mb-1 flex justify-center items-center gap-1"><Activity size={12}/> OEE</div>
                  
                  <div className="font-bold text-slate-700 dark:text-slate-200">
                    {calculateOEE(machine.oee)}%
                  </div>
                
                </div>
                <div className="text-center border-l border-slate-100 dark:border-white/5">
                  <div className="text-xs text-slate-400 mb-1 flex justify-center items-center gap-1"><Server size={12}/> {t('id')}</div>
                  <div className="font-mono text-xs font-bold text-slate-700 dark:text-slate-200 pt-0.5">{machine.device_id}</div>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}