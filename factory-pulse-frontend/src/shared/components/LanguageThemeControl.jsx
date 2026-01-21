import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useApp } from '../contexts/AppContext';

// Internal SVG Flag Components
// Defined locally to avoid external asset dependencies for this specific control.
const FlagBR = () => <svg viewBox="0 0 640 480" className="w-6 h-4 rounded-sm shadow-sm cursor-pointer hover:scale-110 transition-transform"><path fill="#009c3b" d="M0 0h640v480H0z"/><path fill="#ffdf00" d="m320 86 266 154-266 154L54 240z"/><circle cx="320" cy="240" r="88" fill="#002776"/><path fill="#fff" fillRule="evenodd" d="m320 240 88-32c0 20-30 50-88 32z"/></svg>;
const FlagUS = () => <svg viewBox="0 0 640 480" className="w-6 h-4 rounded-sm shadow-sm cursor-pointer hover:scale-110 transition-transform"><path fill="#bd3d44" d="M0 0h640v480H0"/><path stroke="#fff" strokeWidth="37" d="M0 55h640M0 129h640M0 203h640M0 277h640M0 351h640M0 425h640"/><path fill="#192f5d" d="M0 0h296v259H0"/><path fill="#fff" d="M14 22h15v15H14zm58 0h15v15H72zm58 0h15v15h-15zm58 0h15v15h-15zM40 48h15v15H40zm58 0h15v15H98zm58 0h15v15h-15zm58 0h15v15h-15z"/></svg>;
const FlagES = () => <svg viewBox="0 0 640 480" className="w-6 h-4 rounded-sm shadow-sm cursor-pointer hover:scale-110 transition-transform"><path fill="#aa151b" d="M0 0h640v480H0z"/><path fill="#f1bf00" d="M0 120h640v240H0z"/></svg>;

/**
 * Reusable Control Component for Language and Theme.
 * * Provides a UI to switch between available languages (PT, EN, ES) 
 * and toggle the visual theme (Dark/Light).
 * * @param {object} props
 * @param {string} [props.className] - Optional custom CSS class. If not provided, defaults to fixed positioning (top-right), useful for Auth pages.
 */
export default function LanguageThemeControl({ className }) {
  const { theme, toggleTheme, setLang, lang } = useApp();

  // Determine container style: use prop if provided, otherwise fallback to fixed positioning.
  const containerClass = className || "fixed top-6 right-6 flex items-center gap-4 z-[9999]";

  return (
    <div className={containerClass}>
      <div className="flex items-center gap-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm px-3 py-1.5 rounded-full border border-slate-200 dark:border-white/10 shadow-sm transition-colors">
        <div onClick={() => setLang('pt')} className={`opacity-${lang === 'pt' ? '100' : '40'} transition-opacity`} title="Português"><FlagBR /></div>
        <div onClick={() => setLang('en')} className={`opacity-${lang === 'en' ? '100' : '40'} transition-opacity`} title="English"><FlagUS /></div>
        <div onClick={() => setLang('es')} className={`opacity-${lang === 'es' ? '100' : '40'} transition-opacity`} title="Español"><FlagES /></div>
      </div>

      <button onClick={toggleTheme} className="p-2 rounded-full bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border border-slate-200 dark:border-white/10 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors shadow-sm">
         {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
      </button>
    </div>
  );
}