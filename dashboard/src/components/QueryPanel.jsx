import React, { useState, useEffect } from 'react';

function TypingText({ text, speed = 10 }) {
  const [display, setDisplay] = useState('');
  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      if (i <= text.length) { setDisplay(text.slice(0, i)); i++; }
      else clearInterval(interval);
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);
  return <span>{display}</span>;
}

export function QueryPanel({ query, setQuery, handleQuery, loading, answer, tier }) {
  const getTierColor = (t) => {
    switch(t) {
      case 'GRAPH_ONLY': return 'var(--color-primary)';
      case 'GRAPH_RAG': return '#e3b5ff';
      case 'LLM_FULL': return 'var(--color-secondary)';
      default: return 'var(--text-secondary)';
    }
  };

  return (
    <div className="glass-panel" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="label-caps">Agentic Interface</div>
      
      <div style={{ display: 'flex', gap: 12 }}>
        <input
          value={query} onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !loading && handleQuery()}
          placeholder="Ask a question about the codebase..."
          style={{
            flex: 1, padding: '16px', borderRadius: 12, border: '1px solid var(--border-glass)',
            background: 'rgba(0,0,0,0.4)', color: 'var(--text-primary)', fontSize: 16,
            outline: 'none', transition: 'all 0.2s', fontFamily: 'var(--font-body)',
            boxShadow: 'inset 0 2px 10px rgba(0,0,0,0.5)'
          }}
          onFocus={e => { e.target.style.borderColor = 'var(--color-primary)'; e.target.style.boxShadow = 'inset 0 2px 10px rgba(0,0,0,0.5), 0 0 15px rgba(0,240,255,0.2)'; }}
          onBlur={e => { e.target.style.borderColor = 'var(--border-glass)'; e.target.style.boxShadow = 'inset 0 2px 10px rgba(0,0,0,0.5)'; }}
        />
        <button 
          onClick={handleQuery} disabled={loading || !query.trim()}
          style={{
            padding: '0 32px', borderRadius: 12, border: 'none', cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
            background: loading ? 'var(--bg-surface-elevated)' : 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
            color: loading ? 'var(--text-secondary)' : '#000', fontWeight: 600, fontSize: 15,
            transition: 'all 0.2s', fontFamily: 'var(--font-body)', opacity: loading || !query.trim() ? 0.6 : 1
          }}
        >
          {loading ? 'Thinking...' : 'Execute'}
        </button>
      </div>

      {answer && (
        <div style={{
          background: 'rgba(0,0,0,0.3)', borderRadius: 12, padding: 20, 
          borderLeft: `3px solid ${getTierColor(tier)}`,
          marginTop: 8, position: 'relative'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            {tier && (
              <span style={{
                padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                background: `rgba(${tier === 'GRAPH_ONLY' ? '0,240,255' : tier === 'LLM_FULL' ? '160,32,240' : '227,181,255'}, 0.1)`,
                color: getTierColor(tier), fontFamily: 'var(--font-hero)', textTransform: 'uppercase',
                border: `1px solid rgba(${tier === 'GRAPH_ONLY' ? '0,240,255' : tier === 'LLM_FULL' ? '160,32,240' : '227,181,255'}, 0.3)`
              }}>
                {tier}
              </span>
            )}
            <span style={{ fontSize: 11, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 1 }}>
              Response
            </span>
          </div>
          <div style={{ fontSize: 15, lineHeight: 1.6, whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>
            <TypingText text={answer} speed={5} />
          </div>
        </div>
      )}
    </div>
  );
}
