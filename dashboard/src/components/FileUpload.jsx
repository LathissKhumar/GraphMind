import React, { useState, useCallback } from 'react';

export function FileUpload({ uploadStatus, handleUpload, handleClone }) {
  const [dragActive, setDragActive] = useState(false);
  const [repoUrl, setRepoUrl] = useState('');

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file?.name?.endsWith('.zip')) {
      handleUpload(file);
    }
  }, [handleUpload]);

  return (
    <div className="glass-panel" style={{ padding: 24, marginBottom: 20 }}>
      <div className="label-caps" style={{ marginBottom: 16 }}>Codebase Ingestion</div>
      
      <div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={onDrop}
        style={{
          border: `1px dashed ${dragActive ? 'var(--color-primary)' : 'rgba(255,255,255,0.1)'}`,
          borderRadius: 8, padding: '32px 20px', textAlign: 'center',
          background: dragActive ? 'rgba(0, 240, 255, 0.05)' : 'transparent',
          transition: 'all 0.3s ease', cursor: 'pointer', marginBottom: 16
        }}
      >
        <div style={{ color: dragActive ? 'var(--color-primary)' : 'var(--text-secondary)', fontSize: 14 }}>
          {uploadStatus || 'Drag & Drop .ZIP file here'}
        </div>
      </div>
      
      <div style={{ display: 'flex', gap: 12 }}>
        <input
          value={repoUrl}
          onChange={e => setRepoUrl(e.target.value)}
          placeholder="https://github.com/owner/repo"
          onKeyDown={e => e.key === 'Enter' && handleClone(repoUrl)}
          style={{
            flex: 1, padding: '12px 16px', borderRadius: 8, border: '1px solid var(--border-glass)',
            background: 'rgba(0,0,0,0.3)', color: 'var(--text-primary)', fontSize: 14,
            outline: 'none', transition: 'border-color 0.2s', fontFamily: 'var(--font-body)'
          }}
          onFocus={e => e.target.style.borderColor = 'var(--color-primary)'}
          onBlur={e => e.target.style.borderColor = 'var(--border-glass)'}
        />
        <button 
          onClick={() => handleClone(repoUrl)}
          style={{
            padding: '12px 24px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: 'var(--bg-surface-elevated)', color: 'var(--text-primary)',
            fontWeight: 500, fontSize: 14, transition: 'background 0.2s', fontFamily: 'var(--font-body)'
          }}
          onMouseEnter={e => e.target.style.background = 'rgba(255,255,255,0.1)'}
          onMouseLeave={e => e.target.style.background = 'var(--bg-surface-elevated)'}
        >
          Clone
        </button>
      </div>
    </div>
  );
}
