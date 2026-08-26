import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';
import { GraphView } from './components/GraphView';
import { MetricsGrid } from './components/MetricsGrid';
import { FileUpload } from './components/FileUpload';
import { QueryPanel } from './components/QueryPanel';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler);

const API_BASE = import.meta.env.VITE_API_URL || '';

export default function App() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [tier, setTier] = useState(null);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState({ savings_percentage: 0, total_queries: 0, total_tokens_used: 0 });
  const [codebase, setCodebase] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');
  const [error, setError] = useState('');
  const [graphData, setGraphData] = useState(null);
  const [activeTab, setActiveTab] = useState('DASHBOARD');
  const [systemStatus, setSystemStatus] = useState('INITIALIZING');
  const [evalData, setEvalData] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/evaluation`)
      .then(res => res.json())
      .then(data => setEvalData(data))
      .catch(err => console.error(err));
  }, []);

  useEffect(() => {
    setTimeout(() => setSystemStatus('ONLINE'), 800);
    fetchGraph();
    fetchMetrics();
    const interval = setInterval(() => { fetchGraph(); fetchMetrics(); }, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchGraph = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/graph`);
      const data = await res.json();
      if (data.elements?.length) setGraphData(data);
    } catch (e) {}
  };

  const fetchMetrics = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/metrics`);
      const data = await res.json();
      setMetrics(data);
    } catch (e) {}
  };

  const handleQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    setActiveTab('DASHBOARD');
    try {
      const res = await fetch(`${API_BASE}/api/query`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error?.message || 'Query failed');
      setAnswer(data.answer || 'No response');
      setTier(data.tier);
      await fetchGraph();
      await fetchMetrics();
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const handleUpload = async (file) => {
    setUploadStatus('Uploading...');
    setError('');
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.message || 'Upload failed');
      setUploadStatus(`Loaded ${data.file_count} files`);
      setCodebase(data.repo_name || file.name);
      await fetchGraph();
    } catch (e) { setError(e.message); setUploadStatus(''); }
  };

  const handleClone = async (url) => {
    if (!url.trim()) return;
    setUploadStatus('Cloning...');
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/clone`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.message || 'Clone failed');
      setUploadStatus(`Cloned ${data.file_count} files`);
      setCodebase(data.repo_name || url.split('/').pop());
      await fetchGraph();
    } catch (e) { setError(e.message); setUploadStatus(''); }
  };

  const handleReset = () => {
    setQuery(''); setAnswer(''); setTier(null); setCodebase('');
    setUploadStatus(''); setGraphData(null);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{
        padding: '24px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        background: 'rgba(11, 14, 20, 0.8)', backdropFilter: 'blur(20px)', borderBottom: '1px solid var(--border-glass)',
        position: 'sticky', top: 0, zIndex: 100
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 12, background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 20px rgba(0, 240, 255, 0.3)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0B0E14" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z"></path>
            </svg>
          </div>
          <div>
            <h1 className="hero-number" style={{ fontSize: 24, margin: 0, letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #fff, var(--text-secondary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              GraphMind
            </h1>
            <div className="label-caps" style={{ marginTop: 4, opacity: 0.7 }}>Agentic Reasoning Engine</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 8, height: 8, borderRadius: '50%',
              background: systemStatus === 'ONLINE' ? 'var(--color-primary)' : 'var(--color-secondary)',
              boxShadow: `0 0 10px ${systemStatus === 'ONLINE' ? 'var(--color-primary)' : 'var(--color-secondary)'}`
            }}/>
            <span className="label-caps">{systemStatus}</span>
          </div>
          {codebase && (
            <div className="glass-panel" style={{ padding: '8px 16px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: 'var(--text-secondary)' }}>Codebase:</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{codebase}</span>
            </div>
          )}
        </div>
      </header>

      <div style={{ display: 'flex', gap: 24, padding: '0 32px', marginTop: 24, maxWidth: 1600, margin: '24px auto 0' }}>
        <button
          onClick={() => setActiveTab('DASHBOARD')}
          style={{
            background: 'none', border: 'none', borderBottom: `2px solid ${activeTab === 'DASHBOARD' ? 'var(--color-primary)' : 'transparent'}`,
            color: activeTab === 'DASHBOARD' ? 'var(--text-primary)' : 'var(--text-secondary)', padding: '12px 0', fontSize: 14, fontWeight: 600,
            cursor: 'pointer', transition: 'all 0.2s', textTransform: 'uppercase', letterSpacing: '0.05em', fontFamily: 'var(--font-body)'
          }}
        >
          Intelligence Stream
        </button>
        <button
          onClick={() => setActiveTab('EVALUATION')}
          style={{
            background: 'none', border: 'none', borderBottom: `2px solid ${activeTab === 'EVALUATION' ? 'var(--color-primary)' : 'transparent'}`,
            color: activeTab === 'EVALUATION' ? 'var(--text-primary)' : 'var(--text-secondary)', padding: '12px 0', fontSize: 14, fontWeight: 600,
            cursor: 'pointer', transition: 'all 0.2s', textTransform: 'uppercase', letterSpacing: '0.05em', fontFamily: 'var(--font-body)'
          }}
        >
          Evaluation Metrics
        </button>
      </div>

      {activeTab === 'DASHBOARD' ? (
        <main style={{ flex: 1, padding: 32, maxWidth: 1600, margin: '0 auto', width: '100%', display: 'flex', gap: 32, height: 'calc(100vh - 180px)' }}>
          <div style={{ flex: '0 0 420px', display: 'flex', flexDirection: 'column', gap: 32, overflowY: 'auto', paddingRight: 8 }}>
            <FileUpload uploadStatus={uploadStatus} handleUpload={handleUpload} handleClone={handleClone} />
            <MetricsGrid metrics={metrics} />
            <QueryPanel query={query} setQuery={setQuery} handleQuery={handleQuery} loading={loading} answer={answer} tier={tier} />
            
            <div className="glass-panel" style={{ padding: 20 }}>
              <div style={{ display: 'flex', gap: 12 }}>
                <button onClick={handleReset} style={{ flex: 1, padding: '12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: 'var(--text-primary)', cursor: 'pointer', transition: 'all 0.2s', fontFamily: 'var(--font-body)' }} onMouseEnter={e => e.target.style.background = 'rgba(255,0,0,0.1)'} onMouseLeave={e => e.target.style.background = 'transparent'}>Reset System</button>
                <button onClick={() => { fetchGraph(); fetchMetrics(); }} style={{ flex: 1, padding: '12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: 'var(--text-primary)', cursor: 'pointer', transition: 'all 0.2s', fontFamily: 'var(--font-body)' }} onMouseEnter={e => e.target.style.background = 'rgba(255,255,255,0.05)'} onMouseLeave={e => e.target.style.background = 'transparent'}>Refresh</button>
              </div>
            </div>
          </div>
          
          <div style={{ flex: 1, borderRadius: 16, overflow: 'hidden', position: 'relative' }}>
            <GraphView data={graphData} />
          </div>
        </main>
      ) : (
        <main style={{ padding: 32, maxWidth: 1600, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24, width: '100%' }}>
          {/* Evaluation tab implementation remains similar but updated with glass panels */}
          {evalData ? (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                <div className="glass-panel" style={{ padding: 24 }}>
                  <div className="label-caps" style={{ marginBottom: 16 }}>Pass Rates by Pipeline</div>
                  <div style={{ height: 300 }}>
                    <Bar 
                      data={{
                        labels: ['GRAPH_ONLY', 'GRAPH_RAG', 'LLM_FULL'],
                        datasets: [{
                          label: 'Pass Rate (%)',
                          data: [
                            (evalData.summary.GRAPH_ONLY?.pass_rate || 0) * 100,
                            (evalData.summary.GRAPH_RAG?.pass_rate || 0) * 100,
                            (evalData.summary.LLM_FULL?.pass_rate || 0) * 100
                          ],
                          backgroundColor: ['#00F0FF', '#e3b5ff', '#A020F0'],
                          borderWidth: 0, borderRadius: 4
                        }]
                      }}
                      options={{
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                          y: { beginAtZero: true, max: 100, ticks: { color: '#b9cacb' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                          x: { ticks: { color: '#b9cacb' }, grid: { display: false } }
                        }
                      }}
                    />
                  </div>
                </div>
                <div className="glass-panel" style={{ padding: 24 }}>
                  <div className="label-caps" style={{ marginBottom: 16 }}>Metrics Over Time</div>
                  <div style={{ height: 300 }}>
                    <Line 
                      data={{
                        labels: evalData.time_series?.map(d => d.date) || [],
                        datasets: [
                          { label: 'Accuracy', data: evalData.time_series?.map(d => d.accuracy) || [], borderColor: '#00F0FF', backgroundColor: '#00F0FF', tension: 0.4 },
                          { label: 'Completeness', data: evalData.time_series?.map(d => d.completeness) || [], borderColor: '#e3b5ff', backgroundColor: '#e3b5ff', tension: 0.4 },
                          { label: 'Relevance', data: evalData.time_series?.map(d => d.relevance) || [], borderColor: '#dbfcff', backgroundColor: '#dbfcff', tension: 0.4 },
                          { label: 'Conciseness', data: evalData.time_series?.map(d => d.conciseness) || [], borderColor: '#A020F0', backgroundColor: '#A020F0', tension: 0.4 }
                        ]
                      }}
                      options={{
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { labels: { color: '#dce4e5' } } },
                        scales: {
                          y: { beginAtZero: true, max: 5, ticks: { color: '#b9cacb' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                          x: { ticks: { color: '#b9cacb' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                        }
                      }}
                    />
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: 40, fontFamily: 'var(--font-hero)', textTransform: 'uppercase', letterSpacing: 2 }}>Loading Evaluation Data...</div>
          )}
        </main>
      )}

      {error && (
        <div style={{
          position: 'fixed', bottom: 24, right: 24, padding: '16px 24px',
          background: 'rgba(255, 0, 0, 0.2)', backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 0, 0, 0.3)', borderRadius: 12, color: '#fff',
          boxShadow: '0 0 30px rgba(255, 0, 0, 0.2)', zIndex: 1000, maxWidth: 400
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ color: '#ffb4ab' }}>⚠</span>
            <span style={{ flex: 1, fontSize: 14 }}>{error}</span>
            <button onClick={() => setError('')} style={{
              background: 'none', border: 'none', color: '#ffb4ab', cursor: 'pointer', fontSize: 18
            }}>×</button>
          </div>
        </div>
      )}
    </div>
  );
}