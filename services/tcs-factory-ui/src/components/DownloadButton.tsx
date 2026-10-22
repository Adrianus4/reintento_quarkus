import React, { useState } from 'react';
import { downloadZip } from '../services/api';

export const DownloadButton: React.FC<{
  url: string; className?: string; title?: string; disabled?: boolean; children: React.ReactNode;
}> = ({ url, className, title, disabled, children }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  return <span className="inline-flex flex-col">
    <button type="button" className={className} title={title} disabled={disabled || loading}
      onClick={async (event) => {
        event.stopPropagation();
        setError(''); setLoading(true);
        try { await downloadZip(url); }
        catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo descargar el ZIP.'); }
        finally { setLoading(false); }
      }}>
      {loading ? 'Descargando…' : children}
    </button>
    {error && <span role="alert" className="text-xs text-rose-300 mt-1">{error}</span>}
  </span>;
};
