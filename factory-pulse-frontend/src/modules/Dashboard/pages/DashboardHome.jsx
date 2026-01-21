import React from 'react';
import { Activity, Zap, AlertTriangle, CheckCircle, BarChart3 } from 'lucide-react';
import { Bar } from 'react-chartjs-2';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  BarElement, 
  Title, 
  Tooltip, 
  Legend 
} from 'chart.js';
import { useApp } from '../../../shared/contexts/AppContext';

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

/**
 * Dashboard Home Page.
 * Displays high-level factory statistics (KPIs), a production chart, and recent events.
 */
export default function DashboardHome() {
  const { t, theme } = useApp();

  // Mock Data for Factory Summary (KPIs)
  const stats = [
    { label: t('total_oee'), value: '87%', icon: Activity, color: 'blue', trend: '+2.4%' },
    { label: t('active_machines'), value: '3/3', icon: CheckCircle, color: 'green', trend: '100%' },
    { label: t('total_consumption'), value: '450 kWh', icon: Zap, color: 'yellow', trend: '-1.2%' },
    { label: t('active_alerts'), value: '0', icon: AlertTriangle, color: 'purple', trend: t('stable') },
  ];

  // Mock Data for Recent Events
  const events = [
    { machine: 'Dobradeira', msg: t('evt_start'), time: '10:30', type: 'info' },
    { machine: 'Robô', msg: `${t('evt_cycle')} #402`, time: '10:15', type: 'success' },
    { machine: 'Sistema', msg: t('evt_peak'), time: '09:45', type: 'warning' },
  ];

  /**
   * Chart Configuration.
   * Compares daily production against a target (Meta).
   */
  const chartData = {
    labels: ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'],
    datasets: [
      {
        label: t('production_daily') || 'Produção',
        data: [120, 145, 135, 160, 85, 120, 155, 170, 140, 180], // Simulated data
        backgroundColor: '#3b82f6', // Blue
        borderRadius: 4,
      },
      {
        label: 'Meta', // Target line for comparison
        data: [140, 140, 140, 140, 140, 140, 140, 140, 140, 140],
        backgroundColor: theme === 'dark' ? '#334155' : '#e2e8f0', // Dark/Light gray
        borderRadius: 4,
        barPercentage: 0.5, // Thinner bars for the target
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: theme === 'dark' ? '#cbd5e1' : '#475569' }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: theme === 'dark' ? '#1e293b' : '#fff',
        titleColor: theme === 'dark' ? '#fff' : '#0f172a',
        bodyColor: theme === 'dark' ? '#cbd5e1' : '#334155',
        borderColor: theme === 'dark' ? '#334155' : '#e2e8f0',
        borderWidth: 1
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: theme === 'dark' ? '#64748b' : '#94a3b8' }
      },
      y: {
        grid: { color: theme === 'dark' ? '#1e293b' : '#f1f5f9' },
        ticks: { color: theme === 'dark' ? '#64748b' : '#94a3b8' },
        border: { display: false }
      }
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{t('dashboard')}</h1>
        <p className="text-slate-500 dark:text-slate-400">{t('machine_desc')}</p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, idx) => (
          <div key={idx} className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-white/5 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div className={`p-3 rounded-xl bg-${stat.color}-100 text-${stat.color}-600 dark:bg-${stat.color}-500/10 dark:text-${stat.color}-400`}>
                <stat.icon size={24} />
              </div>
              <span className="text-xs font-bold text-green-500 bg-green-100 dark:bg-green-500/10 px-2 py-1 rounded-full">{stat.trend}</span>
            </div>
            <h3 className="text-3xl font-bold text-slate-900 dark:text-white">{stat.value}</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Production Chart */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-white/5 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-lg text-slate-900 dark:text-white flex gap-2 items-center">
              <BarChart3 size={20} /> {t('production_daily')}
            </h3>
          </div>
          
          {/* Chart Container */}
          <div className="h-80 w-full">
            <Bar data={chartData} options={chartOptions} />
          </div>
        </div>

        {/* Event List */}
        <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-white/5 shadow-sm">
          <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-6">{t('latest_events')}</h3>
          <div className="space-y-4">
            {events.map((ev, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                <div className={`w-2 h-2 rounded-full ${ev.type === 'warning' ? 'bg-yellow-500' : ev.type === 'success' ? 'bg-green-500' : 'bg-blue-500'}`}></div>
                <div>
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{ev.machine}: {ev.msg}</p>
                  <p className="text-xs text-slate-500">{ev.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}