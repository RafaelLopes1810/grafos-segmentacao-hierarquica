const METRICS = [
  ['load', 'Carregamento'], ['build_graph', 'Construção do grafo'],
  ['segmentation', 'Segmentação'], ['hierarchy', 'Hierarquia'], ['total', 'Tempo total'],
];

export default function Statistics({ graphStats, timings, regionCount }) {
  return (
    <section className="panel stats-panel">
      <div className="results-heading"><div><span className="eyebrow">RESUMO DO PROCESSAMENTO</span><h2>Estatísticas</h2></div></div>
      <div className="stat-cards"><div className="stat-card"><span>Vértices</span><strong>{graphStats.num_vertices.toLocaleString('pt-BR')}</strong><small>pixels no grafo</small></div><div className="stat-card"><span>Arestas</span><strong>{graphStats.num_edges.toLocaleString('pt-BR')}</strong><small>conectividade {graphStats.connectivity}</small></div><div className="stat-card accent-card"><span>Regiões neste nível</span><strong>{regionCount.toLocaleString('pt-BR')}</strong><small>partição selecionada</small></div></div>
      <div className="timings-list">{METRICS.map(([key, label]) => <div className="timing-row" key={key}><span>{label}</span><strong>{timings[key] != null ? `${timings[key].toLocaleString('pt-BR', { maximumFractionDigits: 1 })} ms` : '—'}</strong></div>)}</div>
    </section>
  );
}
