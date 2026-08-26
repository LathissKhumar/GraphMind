import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

const CYtoscapeStyles = [
  { selector: 'node', style: { 'background-color': '#00F0FF', 'label': 'data(label)', 'color': '#dce4e5', 'font-size': '10px', 'text-valign': 'bottom', 'text-margin-y': 6, 'font-family': 'Inter' }},
  { selector: 'node[class="function"]', style: { 'background-color': '#A020F0', 'width': 20, 'height': 20 }},
  { selector: 'node[class="class"]', style: { 'background-color': '#00F0FF', 'width': 26, 'height': 26 }},
  { selector: 'node[class="module"]', style: { 'background-color': '#dce4e5', 'width': 16, 'height': 16 }},
  { selector: 'node[class="import"]', style: { 'background-color': '#3b494b', 'width': 12, 'height': 12 }},
  { selector: 'edge', style: { 'width': 1.5, 'line-color': 'rgba(0, 240, 255, 0.4)', 'curve-style': 'bezier' }},
  { selector: 'edge[class="calls"]', style: { 'line-color': 'rgba(160, 32, 240, 0.6)', 'target-arrow-color': 'rgba(160, 32, 240, 0.6)', 'target-arrow-shape': 'triangle' }},
  { selector: 'edge[class="imports"]', style: { 'line-color': 'rgba(0, 240, 255, 0.3)', 'target-arrow-shape': 'none', 'line-style': 'dashed' }},
  { selector: 'edge[class="depends"]', style: { 'line-color': 'rgba(255, 255, 255, 0.2)', 'target-arrow-shape': 'triangle', 'line-style': 'dotted' }},
  { selector: 'node:selected', style: { 'border-width': 2, 'border-color': '#fff', 'background-color': '#fff', 'box-shadow': '0 0 20px rgba(0, 240, 255, 0.8)' }},
];

export function GraphView({ data }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !data?.elements?.length) return;
    
    if (cyRef.current) cyRef.current.destroy();

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: data.elements,
      style: CYtoscapeStyles,
      layout: { name: 'cose', animate: true, animationDuration: 1000, randomize: false, padding: 40 },
      minZoom: 0.2,
      maxZoom: 3,
      wheelSensitivity: 0.1,
    });

    return () => { if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null; } }
  }, [data]);

  return (
    <div className="glass-panel" style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}>
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0,
        background: 'radial-gradient(ellipse at center, rgba(0, 240, 255, 0.03) 0%, transparent 70%)'
      }}/>
      <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'relative', zIndex: 1 }} />
      {!data?.elements?.length && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-secondary)', fontSize: 14, fontFamily: 'var(--font-hero)', textTransform: 'uppercase',
          letterSpacing: 2, zIndex: 2
        }}>
          Awaiting Data Ingestion...
        </div>
      )}
    </div>
  );
}
