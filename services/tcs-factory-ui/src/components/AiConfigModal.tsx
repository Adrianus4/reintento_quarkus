// src/components/AiConfigModal.tsx
import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

interface AiConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeConfig: { provider: string; model_name: string };
  onConfigUpdated: (config: { provider: string; model_name: string }) => void;
}

const PROVIDER_PRESETS: Record<string, { label: string; defaultModel: string; models: string[]; docs: string }> = {
  OPENAI: {
    label: 'OpenAI (GPT-4o, o1, o3)',
    defaultModel: 'gpt-4o',
    models: ['gpt-4o', 'gpt-4o-mini', 'o1-preview', 'o3-mini', 'gpt-4-turbo'],
    docs: 'https://platform.openai.com/api-keys',
  },
  GEMINI: {
    label: 'Google Gemini (1.5 Pro, Flash)',
    defaultModel: 'gemini-1.5-pro',
    models: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-2.5-flash'],
    docs: 'https://aistudio.google.com/app/apikey',
  },
  ANTHROPIC: {
    label: 'Anthropic Claude (Sonnet 3.5, Haiku)',
    defaultModel: 'claude-3-5-sonnet-20241022',
    models: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-haiku-20240307'],
    docs: 'https://console.anthropic.com/settings/keys',
  },
  DEEPSEEK: {
    label: 'DeepSeek (Chat, Coder, R1)',
    defaultModel: 'deepseek-chat',
    models: ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner'],
    docs: 'https://platform.deepseek.com/api_keys',
  },
  GROK: {
    label: 'xAI Grok (Grok-2)',
    defaultModel: 'grok-2',
    models: ['grok-2', 'grok-beta'],
    docs: 'https://console.x.ai/',
  },
  GROQ: {
    label: 'Groq (Ultra-Fast Inference)',
    defaultModel: 'llama-3.3-70b-versatile',
    models: ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768', 'qwen-2.5-32b'],
    docs: 'https://console.groq.com/keys',
  },
  OPENROUTER: {
    label: 'OpenRouter (Multi-Model Gateway)',
    defaultModel: 'anthropic/claude-3.5-sonnet',
    models: ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o', 'meta-llama/llama-3.1-70b-instruct'],
    docs: 'https://openrouter.ai/keys',
  },
  OLLAMA: {
    label: 'Ollama (Local / On-Premise)',
    defaultModel: 'qwen2.5-coder:latest',
    models: ['qwen2.5-coder:latest', 'llama3.1:latest', 'deepseek-r1:latest'],
    docs: 'http://localhost:11434',
  },
};

export const AiConfigModal: React.FC<AiConfigModalProps> = ({
  isOpen,
  onClose,
  activeConfig,
  onConfigUpdated,
}) => {
  const [selectedProvider, setSelectedProvider] = useState<string>('OPENAI');
  const [apiKey, setApiKey] = useState<string>('');
  const [showKey, setShowKey] = useState<boolean>(false);
  const [modelName, setModelName] = useState<string>('gpt-4o');
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    if (activeConfig && activeConfig.provider && activeConfig.provider !== 'MOCK') {
      const p = activeConfig.provider.toUpperCase();
      setSelectedProvider(PROVIDER_PRESETS[p] ? p : 'OPENAI');
      setModelName(activeConfig.model_name || PROVIDER_PRESETS[p]?.defaultModel || 'gpt-4o');
    }
  }, [activeConfig, isOpen]);

  const handleProviderChange = (newProvider: string) => {
    setSelectedProvider(newProvider);
    const preset = PROVIDER_PRESETS[newProvider];
    if (preset) {
      setModelName(preset.defaultModel);
    }
    setFeedback(null);
  };

  const handleTestConnection = async () => {
    if (!apiKey && selectedProvider !== 'OLLAMA') {
      setFeedback({ success: false, message: 'Por favor ingrese su API Key para probar la conexión en vivo.' });
      return;
    }
    setIsTesting(true);
    setFeedback(null);
    try {
      const res = await api.orchestrator.testVaultKey(selectedProvider, apiKey, modelName);
      if (res.status === 'OK') {
        setFeedback({
          success: true,
          message: `Conexión verificada exitosamente con ${selectedProvider} (${modelName}).`,
        });
      } else {
        setFeedback({
          success: false,
          message: res.message || `Fallo de autenticación con ${selectedProvider}. Revise su API Key.`,
        });
      }
    } catch (err: any) {
      setFeedback({ success: false, message: err.message || 'Error al conectar con la API de IA.' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveAndActivate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey && selectedProvider !== 'OLLAMA') {
      setFeedback({ success: false, message: 'Debe ingresar una API Key válida para activar el motor.' });
      return;
    }
    setIsSaving(true);
    setFeedback(null);
    try {
      if (apiKey) {
        await api.orchestrator.setVaultKey({
          provider: selectedProvider,
          api_key: apiKey,
        });
      }
      await api.orchestrator.updateGatewayConfig({
        active_provider: selectedProvider,
        model_name: modelName,
      });

      onConfigUpdated({
        provider: selectedProvider.toUpperCase(),
        model_name: modelName,
      });
      setApiKey('');
      onClose();
    } catch (err: any) {
      setFeedback({ success: false, message: err.message || 'Error al guardar la configuración de IA.' });
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  const currentPreset = PROVIDER_PRESETS[selectedProvider] || PROVIDER_PRESETS.OPENAI;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="bg-tcs-card border border-tcs-border rounded-2xl max-w-xl w-full p-6 shadow-2xl relative text-left">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-tcs-muted hover:text-white text-lg transition-colors"
        >
          ✕
        </button>

        {/* Modal Header */}
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-tcs-blue/20 border border-tcs-blue/40 flex items-center justify-center text-xl">
            ⚡
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">
              Ingesta de API & Conmutador de Modelo IA
            </h3>
            <p className="text-xs text-tcs-muted">
              Conexión directa en vivo con LLM (OpenAI, Gemini, Anthropic, DeepSeek). Sin modo Mock.
            </p>
          </div>
        </div>

        {/* Feedback message */}
        {feedback && (
          <div
            className={`p-3 mb-4 rounded-xl text-xs font-mono border flex items-center justify-between ${
              feedback.success
                ? 'bg-emerald-950/60 border-emerald-500/50 text-emerald-300'
                : 'bg-rose-950/60 border-rose-500/50 text-rose-300'
            }`}
          >
            <span>{feedback.message}</span>
            <button onClick={() => setFeedback(null)} className="ml-2 text-xs font-bold opacity-70 hover:opacity-100">
              ✕
            </button>
          </div>
        )}

        <form onSubmit={handleSaveAndActivate} className="space-y-4">
          {/* Provider Selector */}
          <div>
            <label className="block text-xs font-bold text-gray-300 mb-1.5">
              1. Selecciona Proveedor de IA
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {Object.keys(PROVIDER_PRESETS).map((key) => {
                const isSelected = selectedProvider === key;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => handleProviderChange(key)}
                    className={`py-2 px-2.5 rounded-xl border text-xs font-semibold transition-all text-left ${
                      isSelected
                        ? 'bg-tcs-blue text-white border-blue-400 shadow-md shadow-blue-900/30 font-bold'
                        : 'bg-tcs-dark/70 text-tcs-muted border-tcs-border hover:border-gray-500 hover:text-white'
                    }`}
                  >
                    <div>{key}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Model Name & Presets */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold text-gray-300">
                2. Modelo LLM ({selectedProvider})
              </label>
              <span className="text-[10px] text-tcs-cyan font-mono">Totalmente personalizable</span>
            </div>

            {/* Quick Preset Buttons */}
            <div className="flex flex-wrap gap-1.5 mb-2">
              {currentPreset.models.map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setModelName(m)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-mono transition-all ${
                    modelName === m
                      ? 'bg-tcs-cyan/20 border border-tcs-cyan text-tcs-cyan font-bold'
                      : 'bg-tcs-surface border border-tcs-border/60 text-tcs-muted hover:text-white'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>

            <input
              type="text"
              required
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="Escribe o selecciona el nombre exacto del modelo"
              className="w-full px-3.5 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:outline-none focus:border-tcs-cyan font-mono"
            />
          </div>

          {/* API Key Input */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold text-gray-300">
                3. Clave de API ({selectedProvider} API Key)
              </label>
              {currentPreset.docs && (
                <a
                  href={currentPreset.docs}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] text-tcs-cyan underline hover:text-white flex items-center space-x-1"
                >
                  <span>Obtener llave</span>
                  <span>↗</span>
                </a>
              )}
            </div>

            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={selectedProvider === 'OLLAMA' ? 'No requerida para Ollama local' : `Pega tu API Key de ${selectedProvider} aquí`}
                className="w-full pr-10 pl-3.5 py-2 bg-tcs-dark border border-tcs-border rounded-xl text-xs text-white focus:outline-none focus:border-tcs-cyan font-mono"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-2.5 text-xs text-tcs-muted hover:text-white"
              >
                {showKey ? '🙈' : '👁️'}
              </button>
            </div>
            <p className="text-[11px] text-tcs-muted mt-1.5">
              🔒 Tu llave se cifra en reposo en la bóveda backend (Fernet AES-128). Nunca se expone en logs ni en plano.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="pt-3 border-t border-tcs-border flex items-center justify-between gap-3">
            <button
              type="button"
              disabled={isTesting || (!apiKey && selectedProvider !== 'OLLAMA')}
              onClick={handleTestConnection}
              className="px-4 py-2 bg-tcs-dark hover:bg-tcs-surface border border-tcs-border hover:border-tcs-cyan text-xs font-semibold text-tcs-cyan rounded-xl transition-all disabled:opacity-40 flex items-center space-x-1.5"
            >
              <span>{isTesting ? '⌛ Conectando...' : '🔌 Probar Conexión en Vivo'}</span>
            </button>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-tcs-dark hover:bg-tcs-surface border border-tcs-border text-xs font-semibold text-tcs-muted hover:text-white rounded-xl transition-all"
              >
                Cancelar
              </button>

              <button
                type="submit"
                disabled={isSaving}
                className="px-5 py-2 bg-gradient-to-r from-tcs-blue to-tcs-accent hover:from-blue-600 hover:to-indigo-600 text-white text-xs font-extrabold rounded-xl shadow-lg shadow-blue-900/40 transition-all disabled:opacity-50 flex items-center space-x-1.5"
              >
                <span>{isSaving ? 'Guardando...' : '💾 Guardar y Activar Modelo'}</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
