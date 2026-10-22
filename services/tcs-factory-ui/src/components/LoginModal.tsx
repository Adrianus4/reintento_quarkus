// src/components/LoginModal.tsx
import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const LoginModal: React.FC = () => {
  const { login, register } = useAuth();
  const [activeTab, setActiveTab] = useState<'register' | 'login'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (activeTab === 'register') {
        if (!fullName.trim() || !email.trim() || !password) {
          throw new Error('Todos los campos son obligatorios');
        }
        if (password.length < 4) {
          throw new Error('La contraseña debe tener al menos 4 caracteres');
        }
        await register(email, password, fullName, 'ADMIN');
      } else {
        if (!email.trim() || !password) {
          throw new Error('Ingrese email y contraseña');
        }
        await login(email, password);
      }
    } catch (err: any) {
      setError(err.message || 'Error en autenticación');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLogin = async (demoEmail: string, demoPass: string) => {
    setError(null);
    setIsSubmitting(true);
    try {
      await login(demoEmail, demoPass);
    } catch (err: any) {
      // If login fails, auto-register this demo account
      try {
        await register(demoEmail, demoPass, demoEmail.includes('admin') ? 'Administrador BCP' : 'Desarrollador BCP', 'ADMIN');
      } catch (regErr: any) {
        setError(regErr.message || 'Error en acceso rápido');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <div className="w-full max-w-md bg-tcs-navy border border-tcs-border rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="p-6 bg-gradient-to-r from-tcs-navy via-tcs-card to-tcs-dark border-b border-tcs-border flex items-center space-x-3">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-tcs-blue to-tcs-cyan flex items-center justify-center shadow-lg flex-shrink-0">
            <span className="text-white font-extrabold text-xl tracking-tight">TCS</span>
          </div>
          <div>
            <h2 className="text-base font-extrabold text-white tracking-tight">
              TCS Intelligent Microservice Factory
            </h2>
            <p className="text-xs text-tcs-muted">
              Quarkus 3.15 • Control de Acceso & Gobernanza BCP
            </p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="grid grid-cols-2 bg-tcs-dark p-1.5 border-b border-tcs-border text-xs font-bold">
          <button
            type="button"
            onClick={() => {
              setError(null);
              setActiveTab('login');
            }}
            className={`py-2.5 px-3 rounded-xl transition-all flex items-center justify-center space-x-1.5 ${
              activeTab === 'login'
                ? 'bg-tcs-blue text-white shadow-lg'
                : 'text-tcs-muted hover:text-white'
            }`}
          >
            <span>🔑</span>
            <span>Iniciar Sesión</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setError(null);
              setActiveTab('register');
            }}
            className={`py-2.5 px-3 rounded-xl transition-all flex items-center justify-center space-x-1.5 ${
              activeTab === 'register'
                ? 'bg-tcs-blue text-white shadow-lg'
                : 'text-tcs-muted hover:text-white'
            }`}
          >
            <span>✨</span>
            <span>Registrarse</span>
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 text-xs rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 flex items-start space-x-2 animate-fadeIn">
              <span className="text-base leading-none">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {activeTab === 'register' && (
            <div>
              <label className="block text-xs font-bold text-white mb-1.5">Nombre Completo</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ej. Juan Pérez"
                className="w-full px-3.5 py-2.5 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:outline-none focus:border-tcs-cyan focus:ring-1 focus:ring-tcs-cyan placeholder-tcs-muted/50"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-white mb-1.5">Correo Electrónico</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="usuario@bcp.com.pe"
              className="w-full px-3.5 py-2.5 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:outline-none focus:border-tcs-cyan focus:ring-1 focus:ring-tcs-cyan placeholder-tcs-muted/50"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-white mb-1.5">Contraseña</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-3.5 py-2.5 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:outline-none focus:border-tcs-cyan focus:ring-1 focus:ring-tcs-cyan placeholder-tcs-muted/50"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-tcs-blue to-tcs-cyan hover:from-blue-600 hover:to-cyan-500 text-white font-extrabold text-xs rounded-xl shadow-lg transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {isSubmitting ? (
              <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            ) : activeTab === 'register' ? (
              <span>Crear Cuenta & Entrar al Workspace</span>
            ) : (
              <span>Entrar al Workspace</span>
            )}
          </button>

          {/* Quick Access Demo Buttons */}
          <div className="pt-3 border-t border-tcs-border/60 space-y-2">
            <span className="text-[11px] text-tcs-muted block text-center font-mono">
              Acceso Rápido con 1 Clic (Entornos de Prueba):
            </span>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                disabled={isSubmitting}
                onClick={() => handleQuickLogin('admin@bcp.com.pe', 'Admin123!')}
                className="py-2 px-2.5 bg-tcs-dark hover:bg-tcs-surface border border-tcs-border hover:border-emerald-500/50 rounded-xl text-[11px] font-bold text-emerald-300 transition-all flex items-center justify-center space-x-1"
              >
                <span>🛡️</span>
                <span>Admin Demo</span>
              </button>
              <button
                type="button"
                disabled={isSubmitting}
                onClick={() => handleQuickLogin('dev@bcp.com.pe', 'Dev123!')}
                className="py-2 px-2.5 bg-tcs-dark hover:bg-tcs-surface border border-tcs-border hover:border-blue-500/50 rounded-xl text-[11px] font-bold text-blue-300 transition-all flex items-center justify-center space-x-1"
              >
                <span>💻</span>
                <span>Dev Demo</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
