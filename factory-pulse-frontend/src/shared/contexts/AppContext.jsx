import React, { createContext, useState, useContext, useEffect } from 'react';

const AppContext = createContext();

/**
 * Global translation dictionary.
 * Organized by language code (pt, en, es).
 * Used by the t() function to retrieve strings dynamically.
 */
const translations = {
  pt: {
    // General UI
    login_title: 'Acesso Industrial', user_label: 'Usuário', password_label: 'Senha', enter_btn: 'ENTRAR NO SISTEMA',
    welcome: 'Bem-vindo ao FactoryPulse', credential_error: 'Credenciais inválidas! Tente: admin / admin',
    
    // Authentication & Navigation
    forgot_password: 'Esqueceu a senha?',
    no_account: 'Não tem uma conta?',
    create_account: 'Criar agora',
    register_title: 'Criar Conta',
    email_label: 'Email',
    register_btn: 'CADASTRAR',
    already_account: 'Já tem conta?',
    do_login: 'Fazer Login',
    recover_title: 'Recuperar Senha',
    recover_desc: 'Digite seu e-mail para receber as instruções.',
    send_link_btn: 'ENVIAR LINK',
    back_login: 'Voltar para Login',

    // Main System Layout
    dashboard: 'Visão Geral', machines: 'Máquinas', reports: 'Relatórios', alerts: 'Alertas', settings: 'Configurações',
    search: 'Buscar no sistema...', logout: 'Sair',

    // AI Assistant Chat
    assistant_title: 'Assistente FactoryPulse', assistant_subtitle: 'Pergunte sobre OEE e paradas das máquinas',
    assistant_placeholder: 'Pergunte algo, ex: Qual a OEE da DB-01 hoje?',
    assistant_welcome: 'Olá! Posso responder perguntas sobre a OEE e as paradas das suas máquinas. O que você quer saber?',
    assistant_thinking: 'Consultando os dados da fábrica...',
    assistant_error: 'Não consegui falar com o assistente agora. Tente novamente em instantes.',
    machine_list: 'Parque Fabril', machine_desc: 'Monitoramento em tempo real das linhas de produção.',
    energy: 'Energia', availability: 'Disponibilidade', performance: 'Performance', quality: 'Qualidade',
    id: 'ID', unit_energy: 'Corrente (A)',
    
    // Reports & Charts
    realtime_analysis: 'Análise Temporal',
    reports_title: 'Relatórios de Produção',
    report_name: 'Relatório de Eficiência - Turno',
    generated_on: 'Gerado em',

    //Alert Status
    stable: 'Estável',

    // KPIs & Dashboard Events
    total_oee: 'Eficiência Global (OEE)', active_machines: 'Máquinas Ativas', total_consumption: 'Consumo Total',
    active_alerts: 'Alertas Ativos', production_daily: 'Produção Diária', latest_events: 'Últimos Eventos',
    evt_start: 'iniciou operação', evt_cycle: 'finalizou ciclo', evt_peak: 'Pico de energia',
    
    // Database Data Mapping (Dynamic Content)
    'ONLINE': 'ONLINE', 'OFFLINE': 'OFFLINE', 'OPERANDO': 'OPERANDO', 'PARADA': 'PARADA',
    'Prensa': 'Prensa', 'Automação': 'Automação', 'CNC': 'CNC', 'Genérica': 'Genérica',
    'Prensa de alta tonelagem para conformação de chapas metálicas.': 'Prensa de alta tonelagem para conformação de chapas metálicas.',
    'Braço robótico colaborativo de 6 eixos para soldagem MIG/MAG.': 'Braço robótico colaborativo de 6 eixos para soldagem MIG/MAG.',
    'Centro de usinagem vertical 3 eixos de alta precisão.': 'Centro de usinagem vertical 3 eixos de alta precisão.'
  },
  en: {
    // General UI
    login_title: 'Industrial Access', user_label: 'Username', password_label: 'Password', enter_btn: 'LOGIN TO SYSTEM',
    welcome: 'Welcome to FactoryPulse', credential_error: 'Invalid credentials! Try: admin / admin',
    
    // Authentication & Navigation
    forgot_password: 'Forgot password?',
    no_account: "Don't have an account?",
    create_account: 'Create one',
    register_title: 'Create Account',
    email_label: 'Email',
    register_btn: 'REGISTER',
    already_account: 'Already have an account?',
    do_login: 'Login',
    recover_title: 'Recover Password',
    recover_desc: 'Enter your email to receive instructions.',
    send_link_btn: 'SEND LINK',
    back_login: 'Back to Login',

    // Main System Layout
    dashboard: 'Overview', machines: 'Machines', reports: 'Reports', alerts: 'Alerts', settings: 'Settings',
    search: 'Search system...', logout: 'Logout',

    // AI Assistant Chat
    assistant_title: 'FactoryPulse Assistant', assistant_subtitle: 'Ask about machine OEE and downtime',
    assistant_placeholder: 'Ask something, e.g. What is DB-01 OEE today?',
    assistant_welcome: "Hi! I can answer questions about your machines' OEE and downtime. What would you like to know?",
    assistant_thinking: 'Looking up the shop floor data...',
    assistant_error: "Couldn't reach the assistant right now. Please try again shortly.",
    machine_list: 'Factory Floor', machine_desc: 'Real-time monitoring of production lines.',
    energy: 'Energy', availability: 'Availability', performance: 'Performance', quality: 'Quality',
    id: 'ID', unit_energy: 'Current (A)',
    
    // Reports & Charts
    realtime_analysis: 'Time Analysis',
    reports_title: 'Production Reports',
    report_name: 'Efficiency Report - Shift',
    generated_on: 'Generated on',

    //Alert Status
    stable: 'Stable',

    // KPIs & Dashboard Events
    total_oee: 'Global Efficiency (OEE)', active_machines: 'Active Machines', total_consumption: 'Total Consumption',
    active_alerts: 'Active Alerts', production_daily: 'Daily Production', latest_events: 'Latest Events',
    evt_start: 'started operation', evt_cycle: 'finished cycle', evt_peak: 'Energy peak detected',
    
    // Database Data Mapping (Dynamic Content)
    'ONLINE': 'ONLINE', 'OFFLINE': 'OFFLINE', 'OPERANDO': 'OPERATING', 'PARADA': 'STOPPED',
    'Prensa': 'Press', 'Automação': 'Automation', 'CNC': 'CNC', 'Genérica': 'Genérica',
    'Prensa de alta tonelagem para conformação de chapas metálicas.': 'High tonnage press for sheet metal forming.',
    'Braço robótico colaborativo de 6 eixos para soldagem MIG/MAG.': '6-axis collaborative robotic arm for MIG/MAG welding.',
    'Centro de usinagem vertical 3 eixos de alta precisão.': 'High precision 3-axis vertical machining center.'
  },
  es: {
    // General UI
    login_title: 'Acceso Industrial', user_label: 'Usuario', password_label: 'Contraseña', enter_btn: 'INGRESAR AL SISTEMA',
    welcome: 'Bienvenido a FactoryPulse', credential_error: '¡Credenciales inválidas! Pruebe: admin / admin',
    
    // Authentication & Navigation
    forgot_password: '¿Olvidaste tu contraseña?',
    no_account: '¿No tienes cuenta?',
    create_account: 'Crear ahora',
    register_title: 'Crear Cuenta',
    email_label: 'Correo',
    register_btn: 'REGISTRARSE',
    already_account: '¿Ya tienes cuenta?',
    do_login: 'Ingresar',
    recover_title: 'Recuperar Contraseña',
    recover_desc: 'Ingresa tu correo para recibir instrucciones.',
    send_link_btn: 'ENVIAR ENLACE',
    back_login: 'Volver al Login',

    // Main System Layout
    dashboard: 'Visión General', machines: 'Máquinas', reports: 'Reportes', alerts: 'Alertas', settings: 'Ajustes',
    search: 'Buscar en sistema...', logout: 'Salir',

    // AI Assistant Chat
    assistant_title: 'Asistente FactoryPulse', assistant_subtitle: 'Pregunta sobre la OEE y las paradas de las máquinas',
    assistant_placeholder: 'Pregunta algo, ej: ¿Cuál es la OEE de DB-01 hoy?',
    assistant_welcome: '¡Hola! Puedo responder preguntas sobre la OEE y las paradas de tus máquinas. ¿Qué te gustaría saber?',
    assistant_thinking: 'Consultando los datos de la planta...',
    assistant_error: 'No pude comunicarme con el asistente ahora. Intenta de nuevo en unos instantes.',
    machine_list: 'Planta de Producción', machine_desc: 'Monitoreo en tiempo real de las líneas.',
    energy: 'Energía', availability: 'Disponibilidad', performance: 'Rendimiento', quality: 'Calidad',
    id: 'ID', unit_energy: 'Corriente (A)',

    // Reports & Charts
    realtime_analysis: 'Análisis Temporal',
    reports_title: 'Reportes de Producción',
    report_name: 'Reporte de Eficiencia - Turno',
    generated_on: 'Generado el',

    //Alert Status
    stable: 'Estable',

    // KPIs & Dashboard Events
    total_oee: 'Eficiencia Global (OEE)', active_machines: 'Máquinas Activas', total_consumption: 'Consumo Total',
    active_alerts: 'Alertas Activas', production_daily: 'Producción Diaria', latest_events: 'Últimos Eventos',
    evt_start: 'inició operación', evt_cycle: 'finalizó ciclo', evt_peak: 'Pico de energía',

    // Database Data Mapping (Dynamic Content)
    'ONLINE': 'EN LÍNEA', 'OFFLINE': 'DESCONECTADO', 'OPERANDO': 'OPERANDO', 'PARADA': 'DETENIDA',
    'Prensa': 'Prensa', 'Automação': 'Automatización', 'CNC': 'CNC', 'Genérica': 'Genérica',
    'Prensa de alta tonelagem para conformação de chapas metálicas.': 'Prensa de alto tonelaje para conformado de chapa.',
    'Braço robótico colaborativo de 6 eixos para soldagem MIG/MAG.': 'Brazo robótico colaborativo de 6 ejes para soldadura MIG/MAG.',
    'Centro de usinagem vertical 3 eixos de alta precisão.': 'Centro de mecanizado vertical de 3 ejes de alta precisión.'
  }
};

/**
 * AppContext Provider.
 * Manages global application state:
 * - Theme (Dark/Light)
 * - Language (i18n)
 * - Translation Helper (t)
 */
export const AppProvider = ({ children }) => {
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');
  const [lang, setLang] = useState(localStorage.getItem('lang') || 'pt');

  // Persist Theme changes to DOM and LocalStorage
  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') root.classList.add('dark');
    else root.classList.remove('dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Persist Language changes to LocalStorage
  useEffect(() => {
    localStorage.setItem('lang', lang);
  }, [lang]);

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  
  /**
   * Translation helper function.
   * Returns the translated string for the current language.
   * If the key is missing, returns the key itself.
   * @param {string} key - The translation key.
   */
  const t = (key) => {
    if (!key) return '';
    if (!translations[lang]) return key;
    return translations[lang][key] || key;
  };

  return (
    <AppContext.Provider value={{ theme, toggleTheme, lang, setLang, t }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);