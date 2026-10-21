// src/components/CodeViewer.tsx
import React, { useState, useEffect } from 'react';
import { GeneratedFile } from '../types';

interface CodeViewerProps {
  files: GeneratedFile[];
  onSaveFiles?: (updatedFiles: GeneratedFile[]) => Promise<void>;
  onVerifySandbox?: () => void;
  isSaving?: boolean;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  files,
  onSaveFiles,
  onVerifySandbox,
  isSaving = false,
}) => {
  const [selectedPath, setSelectedPath] = useState<string>(files[0]?.path || '');
  const [editableFiles, setEditableFiles] = useState<GeneratedFile[]>(files);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState<boolean>(false);

  useEffect(() => {
    setEditableFiles(files);
    if (!selectedPath && files.length > 0) {
      setSelectedPath(files[0].path);
    }
  }, [files]);

  const currentFile = editableFiles.find((f) => f.path === selectedPath) || editableFiles[0];

  const handleContentChange = (newContent: string) => {
    if (!currentFile) return;
    const updated = editableFiles.map((f) =>
      f.path === currentFile.path ? { ...f, content: newContent } : f
    );
    setEditableFiles(updated);
    setHasUnsavedChanges(true);
  };

  const handleSave = async () => {
    if (onSaveFiles) {
      await onSaveFiles(editableFiles);
      setHasUnsavedChanges(false);
    }
  };

  if (!files || files.length === 0) {
    return (
      <div className="p-8 text-center bg-tcs-card border border-tcs-border rounded-xl text-tcs-muted text-xs">
        No hay archivos generados aún para visualizar.
      </div>
    );
  }

  return (
    <div className="bg-tcs-card border border-tcs-border rounded-xl shadow-xl overflow-hidden flex flex-col h-[650px]">
      {/* Top Bar */}
      <div className="p-3 bg-tcs-navy border-b border-tcs-border flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500/80"></span>
            <span className="w-3 h-3 rounded-full bg-amber-500/80"></span>
            <span className="w-3 h-3 rounded-full bg-emerald-500/80"></span>
          </div>
          <span className="text-xs font-mono font-bold text-white flex items-center space-x-2">
            <span>{currentFile?.path || 'workspace'}</span>
            {hasUnsavedChanges && (
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-950/70 border border-amber-700 text-amber-300">
                Modificado (HITL)
              </span>
            )}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {onSaveFiles && (
            <button
              onClick={handleSave}
              disabled={!hasUnsavedChanges || isSaving}
              className="px-3 py-1 bg-tcs-surface hover:bg-tcs-blue text-xs font-medium rounded border border-tcs-border text-white transition-colors disabled:opacity-40"
            >
              {isSaving ? 'Guardando...' : 'Guardar Cambios (HITL)'}
            </button>
          )}

          {onVerifySandbox && (
            <button
              onClick={onVerifySandbox}
              className="px-3 py-1 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-xs font-bold rounded text-white shadow transition-all flex items-center space-x-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Verificar en Sandbox & Descargar</span>
            </button>
          )}
        </div>
      </div>

      {/* Editor & Explorer Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* File Explorer Tree */}
        <div className="w-64 bg-tcs-dark border-r border-tcs-border overflow-y-auto p-2 text-xs font-mono">
          <div className="text-[10px] text-tcs-muted uppercase tracking-wider font-bold px-2 py-1 mb-1">
            Explorador de Archivos ({editableFiles.length})
          </div>
          <div className="space-y-0.5">
            {editableFiles.map((file) => {
              const isSelected = file.path === currentFile?.path;
              const fileName = file.path.split('/').pop() || file.path;
              const isJava = file.path.endsWith('.java');
              const isXml = file.path.endsWith('.xml');
              const isProperties = file.path.endsWith('.properties');
              const isYaml = file.path.endsWith('.yml') || file.path.endsWith('.yaml');

              return (
                <button
                  key={file.path}
                  onClick={() => setSelectedPath(file.path)}
                  className={`w-full text-left px-2 py-1.5 rounded flex items-center space-x-2 transition-colors ${
                    isSelected
                      ? 'bg-tcs-blue/20 text-white font-bold border-l-2 border-tcs-blue'
                      : 'text-tcs-muted hover:text-white hover:bg-tcs-surface/50'
                  }`}
                >
                  <span className="text-[10px]">
                    {isJava ? '☕' : isXml ? '📄' : isProperties ? '⚙️' : isYaml ? '🐙' : '📝'}
                  </span>
                  <span className="truncate flex-1" title={file.path}>
                    {fileName}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Code Editor Area */}
        <div className="flex-1 flex flex-col bg-[#050b14] overflow-hidden">
          <div className="flex-1 relative overflow-auto">
            <textarea
              value={currentFile?.content || ''}
              onChange={(e) => handleContentChange(e.target.value)}
              spellCheck={false}
              className="w-full h-full p-4 bg-transparent text-emerald-300 font-mono text-xs leading-relaxed resize-none focus:outline-none selection:bg-tcs-blue selection:text-white"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

