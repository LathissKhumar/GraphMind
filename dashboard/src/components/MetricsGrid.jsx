import React from 'react';

function MetricCard({ label, value, unit = '', highlight = 'primary' }) {
  return (
    <div className="glass-panel" style={{ padding: '24px 20px', position: 'relative', overflow: 'hidden' }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '1px',
        background: `linear-gradient(90deg, transparent, var(--color-${highlight}), transparent)`,
        opacity: 0.5
      }} />
      <div className="label-caps" style={{ marginBottom: 12 }}>{label}</div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
        <h2 className="hero-number plasma-text" style={{ 
          background: highlight === 'secondary' ? 'linear-gradient(90deg, #A020F0, #ffb5ff)' : 'linear-gradient(90deg, #00F0FF, #A020F0)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
        }}>
          {value}
        </h2>
        {unit && <span style={{ fontSize: 16, color: 'var(--text-secondary)', fontWeight: 500 }}>{unit}</span>}
      </div>
    </div>
  );
}

export function MetricsGrid({ metrics }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
      <MetricCard label="Token Savings" value={metrics.savings_percentage || 0} unit="%" highlight="primary" />
      <MetricCard label="Queries Executed" value={metrics.total_queries || 0} highlight="secondary" />
      <MetricCard label="Tokens Used" value={(metrics.total_tokens_used || 0).toLocaleString()} highlight="primary" />
    </div>
  );
}
