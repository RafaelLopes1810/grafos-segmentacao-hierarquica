const METRICS = [
  ["load", "Carregamento"],
  ["build_graph", "Construção do grafo"],
  ["segmentation", "Segmentação"],
  ["hierarchy", "Hierarquia"],
  ["total", "Tempo total"],
];

export default function Statistics({
  graphStats,
  timings,
  regionCount,
  regions = [],
  homogeneidadeMse,
}) {
  let menor = null;
  let maior = null;
  let totalPixels = 0;

  // Calcula estatísticas das regiões.
  for (const regiao of regions) {
    const area = regiao.area;

    menor = menor === null ? area : Math.min(menor, area);

    maior = maior === null ? area : Math.max(maior, area);

    totalPixels += area;
  }

  const media = regions.length ? totalPixels / regions.length : null;

  // Formatação numérica para português brasileiro.
  const formatar = (valor, casas = 0) =>
    valor == null
      ? "—"
      : valor.toLocaleString("pt-BR", {
          minimumFractionDigits: casas,
          maximumFractionDigits: casas,
        });

  return (
    <section className="panel stats-panel">
      <div className="results-heading">
        <div>
          <span className="eyebrow">RESUMO DO PROCESSAMENTO</span>
          <h2>Estatísticas</h2>
        </div>
      </div>

      <div className="stat-cards">
        <div className="stat-card">
          <span>Vértices</span>
          <strong>{formatar(graphStats.num_vertices)}</strong>
          <small>pixels no grafo</small>
        </div>

        <div className="stat-card">
          <span>Arestas</span>
          <strong>{formatar(graphStats.num_edges)}</strong>
          <small>conectividade {graphStats.connectivity}</small>
        </div>

        <div className="stat-card accent-card">
          <span>Regiões neste nível</span>
          <strong>{formatar(regionCount)}</strong>
          <small>partição selecionada</small>
        </div>

        <div className="stat-card">
          <span>Menor região</span>
          <strong>{formatar(menor)}</strong>
          <small>pixels</small>
        </div>

        <div className="stat-card">
          <span>Maior região</span>
          <strong>{formatar(maior)}</strong>
          <small>pixels</small>
        </div>

        <div className="stat-card">
          <span>Tamanho médio</span>
          <strong>{formatar(media, 2)}</strong>
          <small>pixels por região</small>
        </div>
      </div>

      {/* Avaliação da homogeneidade */}
      <div className="timings-list">
        <div className="timing-row">
          <span>Homogeneidade das cores (MSE)</span>

          <strong>{formatar(homogeneidadeMse, 4)}</strong>
        </div>

        {METRICS.map(([key, label]) => (
          <div className="timing-row" key={key}>
            <span>{label}</span>

            <strong>
              {timings[key] != null ? `${formatar(timings[key], 1)} ms` : "—"}
            </strong>
          </div>
        ))}
      </div>
    </section>
  );
}
