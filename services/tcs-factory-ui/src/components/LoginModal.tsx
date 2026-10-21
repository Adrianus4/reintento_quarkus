// src/components/LoginModal.tsx
import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const LoginModal: React.FC = () => {
  const { login, setupInitialAdmin } = useAuth();
  // Default to setup tab so new users immediately see how to register the first admin
  const [activeTab, setActiveTab] = useState<'setup' | 'login'>('setup');
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
      if (activeTab === 'setup') {
        if (!fullName.trim() || !email.trim() || !password) {
          throw new Error('Todos los campos son obligatorios');
        }
        if (password.length < 8) {
          throw new Error('La contraseña debe tener al menos 8 caracteres (requisito de seguridad)');
        }
        await setupInitialAdmin(email, password, fullName);
      } else {
        if (!email.trim() || !password) {
          throw new Error('Ingrese email y contraseña');
        }
        await login(email, password);
      }
    } catch (err: any) {
      // If setup fails because admin already exists, switch to login tab
      if (err.message && err.message.includes('already exists')) {
        setError('El Administrador ya fue inicializado previamente. Ingrese con sus credenciales en la pestaña "Iniciar Sesión".');
        setActiveTab('login');
      } else {
        setError(err.message || 'Error en autenticación');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-tcs-dark/85 backdrop-blur-md p-4">
      <div className="w-full max-w-md bg-tcs-navy border border-tcs-border rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="p-6 bg-gradient-to-r from-tcs-navy to-tcs-dark border-b border-tcs-border flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-tcs-blue to-tcs-cyan flex items-center justify-center shadow-md flex-shrink-0">
            <span className="text-white font-extrabold text-lg">TCS</span>
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">
              TCS Intelligent Microservice Factory
            </h2>
            <p className="text-xs text-tcs-muted">
              Workspace Studio • Plataforma de Ingeniería Quarkus
            </p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="grid grid-cols-2 bg-tcs-dark p-1 border-b border-tcs-border text-xs font-semibold">
          <button
            type="button"
            onClick={() => {
              setError(null);
              setActiveTab('setup');
            }}
            className={`py-2 px-3 rounded-lg transition-all flex flex-col items-center justify-center ${
              activeTab === 'setup'
                ? 'bg-tcs-blue text-white shadow'
                : 'text-tcs-muted hover:text-white'
            }`}
          >
            <span>1. Registrar Admin</span>
            <span className="text-[10px] opacity-75 font-normal">Primer uso (Zero-State)</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setError(null);
              setActiveTab('login');
            }}
            className={`py-2 px-3 rounded-lg transition-all flex flex-col items-center justify-center ${
              activeTab === 'login'
                ? 'bg-tcs-blue text-white shadow'
                : 'text-tcs-muted hover:text-white'
            }`}
          >
            <span>2. Iniciar Sesión</span>
            <span className="text-[10px] opacity-75 font-normal">Usuarios existentes</span>
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Informative Guidance */}
          {activeTab === 'setup' ? (
            <div className="p-3 rounded-lg bg-tcs-surface/60 border border-tcs-border text-xs text-tcs-light">
              <strong className="text-tcs-cyan block mb-1">Paso 1: Configurar SuperAdmin</strong>
              La plataforma inicia con base de datos limpia (Zero Preloaded Data). Registre aquí el primer Administrador para acceder a la gobernanza y crear clientes y desarrolladores.
            </div>
          ) : (
            <div className="p-3 rounded-lg bg-tcs-surface/60 border border-tcs-border text-xs text-tcs-light">
              <strong className="text-white block mb-1">Acceso con Credenciales</strong>
              Ingrese con el correo y contraseña del Administrador o de un Desarrollador creado previamente.
            </div>
          )}

          {error && (
            <div className="p-3 text-xs rounded-lg bg-rose-950/70 border border-rose-800 text-rose-300 flex items-start space-x-2">
              <svg className="w-4 h-4 mt-0.5 flex-shrink-0 text-rose-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {activeTab === 'setup' && (
            <div>
              <label className="block text-xs font-medium text-tcs-muted mb-1">Nombre Completo del Administrador</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ej. Adrian Lozano"
                className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-sm text-white focus:outline-none focus:border-tcs-blue focus:ring-1 focus:ring-tcs-blue placeholder-tcs-muted/50"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-tcs-muted mb-1">Correo Electrónico Corporativo</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@tcs.com"
              className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-sm text-white focus:outline-none focus:border-tcs-blue focus:ring-1 focus:ring-tcs-blue placeholder-tcs-muted/50"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="block text-xs font-medium text-tcs-muted">Contraseña</label>
              {activeTab === 'setup' && (
                <span className="text-[10px] text-tcs-cyan">Mínimo 8 caracteres</span>
              )}
            </div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-3 py-2 bg-tcs-dark border border-tcs-border rounded-lg text-sm text-white focus:outline-none focus:border-tcs-blue focus:ring-1 focus:ring-tcs-blue placeholder-tcs-muted/50"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-2 py-2.5 px-4 bg-tcs-blue hover:bg-tcs-accent text-white font-medium text-sm rounded-lg transition-colors flex items-center justify-center space-x-2 disabled:opacity-50 shadow-md"
          >
            {isSubmitting ? (
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            ) : activeTab === 'setup' ? (
              <span>Crear SuperAdmin & Entrar Automáticamente</span>
            ) : (
              <span>Iniciar Sesión en la Plataforma</span>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
