import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Line } from 'react-chartjs-2';
import { Zap, Clock, Activity, CheckCircle, ArrowLeft } from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { useApp } from '../../../shared/contexts/AppContext';
import api from '../../../shared/services/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

/**
 * Machine Dashboard Page.
 * Displays detailed telemetry and KPI data for a specific machine.
 * Includes a real-time line chart and metric selectors.
 */
export default function MachineDashboard() {
  const { id } = useParams();
  const { t, theme } = useApp();
  const [machine, setMachine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeMetric, setActiveMetric] = useState('energy'); 
  const [timeRange, setTimeRange] = useState('24H'); 

  /**
   * Data Polling Effect.
   * Fetches machine data every 5 seconds to update UI in near real-time.
   */
  useEffect(() => {
    const fetchMachine = () => {
        api.get(`machines/${id}/`).then(res => {
            setMachine(res.data);
            setLoading(false);
        }).catch(err => console.error(err));
    };
    fetchMachine();
    const interval = setInterval(fetchMachine, 5000);
    return () => clearInterval(interval);
  }, [id]);

  /**
   * Chart Configuration Memo.
   * Generates dynamic labels based on selected Time Range (1H, 24H, 7D).
   * Formats data points based on the selected Active Metric (Energy vs OEE).
   */
  const chartConfig = useMemo(() => {
    if (!machine) return { labels: [], datasets: [] };
    
    let labels = [], data = [], color = '#3b82f6';
    const pointsCount = timeRange === '1H' ? 12 : (timeRange === '24H' ? 24 : 7);
    const now = new Date();
    
    // Label Generation (Days/Hours)
    for (let i = pointsCount - 1; i >= 0; i--) {
        const d = new Date(now);
        if (timeRange === '1H') d.setMinutes(d.getMinutes() - (i * 5));
        else if (timeRange === '24H') d.setHours(d.getHours() - i);
        else d.setDate(d.getDate() - i);

        let label = '';
        if (timeRange === '7D') {
            // Format: Weekday (Mon, Tue...)
            label = d.toLocaleDateString(theme === 'dark' ? 'pt-BR' : 'pt-BR', { weekday: 'short' });
        } else {
            // Format: HH:MM
            label = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        }
        labels.push(label);
    }
    
    if (activeMetric === 'energy') {
        // Retrieve real history or fallback to zeros
        const history = machine.energy_history || [];
        
        if (history.length > 0) {
            // Slice the last N points matching the range
            data = history.slice(-pointsCount).map(h => h.current_amps);
            // Pad with zeros if history is insufficient
            while(data.length < pointsCount) data.unshift(0); 
        } else {
            data = Array(pointsCount).fill(0);
        }
    } else {
        // Static OEE data (Visual Mock for demonstration)
        data = Array(pointsCount).fill(machine.oee?.[activeMetric] || 0);
        if (activeMetric === 'availability') color = '#10b981';
        if (activeMetric === 'performance') color = '#f59e0b';
        if (activeMetric === 'quality') color = '#8b5cf6';
    }

    return {
      labels,
      datasets: [{
        label: t(activeMetric),
        data,
        borderColor: color,
        backgroundColor: (ctx) => {
          const g = ctx.chart.ctx.createLinearGradient(0,0,0,300);
          g.addColorStop(0, color+'40'); g.addColorStop(1, color+'00');
          return g;
        },
        fill: true, tension: 0.4,
        pointRadius: 3, 
        pointHoverRadius: 6
      }]
    };
  }, [machine, activeMetric, timeRange, t, theme]);

  /**
   * Helper to construct absolute image URLs for Django Media files.
   */
  const getImageUrl = (path) => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `http://127.0.0.1:8000${cleanPath}`;
  };

  // ChartJS Options Configuration
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: { 
        display: true, // Display X-Axis labels
        grid: { display: false },
        ticks: { 
            color: theme === 'dark' ? '#64748b' : '#94a3b8',
            maxTicksLimit: timeRange === '1H' ? 6 : 8, // Prevent label overlapping
            font: { size: 10 }
        }
      },
      y: { 
        display: true, 
        grid: { color: theme === 'dark' ? '#1e293b' : '#f1f5f9' },
        border: { display: false },
        ticks: { color: theme === 'dark' ? '#64748b' : '#94a3b8', font: { size: 10 } } 
      }
    },
    plugins: { 
        legend: { display: false },
        tooltip: {
            mode: 'index', intersect: false,
            backgroundColor: theme === 'dark' ? '#1e293b' : '#fff',
            titleColor: theme === 'dark' ? '#fff' : '#0f172a',
            bodyColor: theme === 'dark' ? '#cbd5e1' : '#334155',
            borderColor: theme === 'dark' ? '#334155' : '#e2e8f0',
            borderWidth: 1
        }
    },
    interaction: { mode: 'nearest', axis: 'x', intersect: false }
  };

  if (loading || !machine) return <div className="p-10 text-center animate-pulse">Loading data...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in pb-20">
      <div className="flex items-center gap-4">
        <Link to="/machines" className="p-2 bg-white dark:bg-slate-800 rounded-full border border-slate-200 dark:border-white/10 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
          <ArrowLeft size={20} className="text-slate-600 dark:text-slate-300" />
        </Link>
        <div className="flex items-center gap-4">
            {machine.image && <img src={getImageUrl(machine.image)} className="w-16 h-16 rounded-lg object-cover border-2 border-slate-200 dark:border-slate-700"/>}
            <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{machine.name}</h1>
                <p className="text-slate-500 dark:text-slate-400 font-mono text-sm">{t('id')}: {machine.device_id}</p>
            </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <KpiCard title={t('energy')} value={machine.energy_history?.length ? machine.energy_history[machine.energy_history.length-1].current_amps.toFixed(1) : 0} unit="A" icon={Zap} color="blue" active={activeMetric === 'energy'} onClick={() => setActiveMetric('energy')} />
        <KpiCard title={t('availability')} value={machine.oee?.availability} unit="%" icon={Clock} color="green" active={activeMetric === 'availability'} onClick={() => setActiveMetric('availability')} />
        <KpiCard title={t('performance')} value={machine.oee?.performance} unit="%" icon={Activity} color="orange" active={activeMetric === 'performance'} onClick={() => setActiveMetric('performance')} />
        <KpiCard title={t('quality')} value={machine.oee?.quality} unit="%" icon={CheckCircle} color="purple" active={activeMetric === 'quality'} onClick={() => setActiveMetric('quality')} />
      </div>

      {/* Main Chart Section */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-white/5 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
          <h3 className="font-bold text-lg text-slate-800 dark:text-white flex items-center gap-2">
            {t('realtime_analysis')} | {t(activeMetric)}
          </h3>
          
          <div className="flex bg-slate-100 dark:bg-slate-900 rounded-lg p-1">
            {['1H', '24H', '7D'].map(range => (
              <button 
                key={range} 
                onClick={() => setTimeRange(range)}
                className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all ${
                  timeRange === range 
                    ? 'bg-white dark:bg-slate-700 shadow text-slate-900 dark:text-white' 
                    : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>
        
        <div className="h-80 w-full">
          <Line data={chartConfig} options={chartOptions} />
        </div>
      </div>
    </div>
  );
}

/**
 * Reusable KPI Card Component.
 * Displays a single metric with icon, value, and unit.
 * Supports active state styling.
 */
const KpiCard = ({ title, value, unit, icon: Icon, color, active, onClick }) => (
  <div onClick={onClick} className={`p-5 rounded-2xl border cursor-pointer transition-all ${active ? `bg-${color}-50 dark:bg-${color}-500/10 border-${color}-500` : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-white/10 hover:border-slate-300'}`}>
    <div className={`p-2 w-fit rounded-lg mb-4 ${active ? `text-${color}-600 bg-${color}-200 dark:bg-${color}-500/20` : 'text-slate-400 bg-slate-100 dark:bg-slate-700'}`}><Icon size={20}/></div>
    <p className="text-xs uppercase font-bold text-slate-500">{title}</p>
    <h3 className="text-2xl font-bold text-slate-800 dark:text-white">{value}<small className="text-sm ml-1 text-slate-400">{unit}</small></h3>
  </div>
);