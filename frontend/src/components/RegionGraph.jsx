import { useMemo, useState } from 'react';

const PALETTE = ['#f18b62', '#67b7a5', '#e2bd60', '#8c91d2', '#d77b9c', '#75a9d9', '#b3a16a', '#68a878'];

export default function RegionGraph({ level, width, height }) {
  const [enabled, setEnabled] = useState(true);
  const [showLabels, setShowLabels] = useState(false);
  const regions = level?.regions || [];
  const adjacency = level?.adjacency || [];
  const dense = regions.length > 180;
  const view = useMemo(() => {
    const pad = 24;
    const scaleX = (width - pad * 2) / Math.max(width, 1);
    const scaleY = (height - pad * 2) / Math.max(height, 1);
    const nodes = new Map(regions.map((region, index) => {
      const [x, y] = region.centroid || [width / 2, height / 2];
      return [region.id, { ...region, x: pad + x * scaleX, y: pad + y * scaleY, color: PALETTE[index % PALETTE.length] }];
    }));
    const edges = adjacency.filter(([a, b]) => nodes.has(a) && nodes.has(b)).map(([a, b, weight]) => ({ a: nodes.get(a), b: nodes.get(b), weight }));
    const maxWeight = edges.reduce((maximum, edge) => Math.max(maximum, edge.weight), 1);
    return { nodes: [...nodes.values()], edges, maxWeight, pad };
  }, [regions, adjacency, width, height]);

  return (
    <section className="panel rag-panel">
      <div className="results-heading"><div><span className="eyebrow">GRAFO DE ADJACÊNCIA</span><h2>RAG das regiões</h2></div><label className="toggle"><input type="checkbox" checked={enabled} onChange={(event) => setEnabled(event.target.checked)} /><span className="toggle-track" /><span>{enabled ? 'Visível' : 'Oculto'}</span></label></div>
      {enabled && <>
        <div className="rag-meta"><span><i className="legend-dot" /> {regions.length} vértices</span><span><i className="legend-line" /> {view.edges.length} arestas</span><label className="label-toggle"><input type="checkbox" checked={showLabels} onChange={(event) => setShowLabels(event.target.checked)} disabled={dense} /> IDs {dense && <small>(ocultos para legibilidade)</small>}</label></div>
        {regions.length === 0 ? <div className="empty-graph">Este nível não contém metadados de regiões.</div> : <div className="graph-canvas">
          <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Grafo com ${regions.length} regiões e ${view.edges.length} adjacências`}>
            {view.edges.map((edge, index) => <line key={`${edge.a.id}-${edge.b.id}-${index}`} x1={edge.a.x} y1={edge.a.y} x2={edge.b.x} y2={edge.b.y} stroke="#a7aea6" strokeOpacity={dense ? 0.18 : 0.46} strokeWidth={dense ? 0.7 : 0.8 + (1 - edge.weight / view.maxWeight) * 1.6} />)}
            {view.nodes.map((node) => { const radius = dense ? Math.max(1.8, Math.min(4.5, 2 + Math.sqrt(node.area) / 18)) : Math.max(5, Math.min(15, 5 + Math.sqrt(node.area) / 9)); return <g key={node.id}><circle cx={node.x} cy={node.y} r={radius + 2} fill={node.color} opacity=".16" /><circle cx={node.x} cy={node.y} r={radius} fill={node.color} stroke="#fffdf8" strokeWidth="1.5"><title>{`Região ${node.id} · ${node.area} pixels`}</title></circle>{showLabels && <text x={node.x} y={node.y - radius - 5} textAnchor="middle">{node.id}</text>}</g>; })}
          </svg>
        </div>}
        <div className="rag-footer"><span>Posição dos vértices baseada nos centroides das regiões</span><span>As arestas representam adjacências</span></div>
      </>}
    </section>
  );
}
