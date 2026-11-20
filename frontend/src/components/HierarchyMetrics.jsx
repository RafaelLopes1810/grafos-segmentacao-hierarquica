import "./HierarchyMetrics.css";

const CHART = {
  width: 620,
  height: 184,
  left: 64,
  right: 22,
  top: 16,
  bottom: 34,
};

const numberFormat = (value, decimals = 0) =>
  new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);

function TrendChart({ title, description, values, selectedIndex, color, decimals }) {
  const selectedValue = values[selectedIndex];
  const count = values.length;
  const validValues = values.filter((value) => Number.isFinite(value));
  const maxValue = Math.max(1, ...validValues);
  const plotWidth = CHART.width - CHART.left - CHART.right;
  const plotHeight = CHART.height - CHART.top - CHART.bottom;
  const x = (index) => CHART.left + (count === 1 ? plotWidth / 2 : (index * plotWidth) / (count - 1));
  const y = (value) => CHART.top + (1 - value / maxValue) * plotHeight;

  // A API retorna um valor numérico para cada nível. Segmentos inválidos
  // não são unidos artificialmente pela linha do gráfico.
  const segments = [];
  let current = [];
  values.forEach((value, index) => {
    if (Number.isFinite(value)) {
      current.push(`${x(index)},${y(value)}`);
    } else if (current.length) {
      segments.push(current);
      current = [];
    }
  });
  if (current.length) segments.push(current);

  return (
    <div className="hm-chart-card">
      <div className="hm-chart-heading">
        <div>
          <strong>{title}</strong>
          <small>{description}</small>
        </div>
        <span className="hm-current-value">
          {Number.isFinite(selectedValue) ? numberFormat(selectedValue, decimals) : "—"}
        </span>
      </div>

      <svg
        className="hm-chart"
        viewBox={`0 0 ${CHART.width} ${CHART.height}`}
        role="img"
        aria-label={`${title}. Nível selecionado ${selectedIndex + 1}: ${
          Number.isFinite(selectedValue) ? numberFormat(selectedValue, decimals) : "sem dados"
        }.`}
      >
        <title>{`${title} nos ${count} níveis da hierarquia`}</title>

        {[0, 0.5, 1].map((fraction) => {
          const value = fraction * maxValue;
          const axisY = y(value);
          return (
            <g key={fraction}>
              <line
                x1={CHART.left}
                y1={axisY}
                x2={CHART.width - CHART.right}
                y2={axisY}
                className="hm-grid-line"
              />
              <text x={CHART.left - 10} y={axisY + 4} textAnchor="end" className="hm-axis-label">
                {numberFormat(value, value < 1 ? 1 : 0)}
              </text>
            </g>
          );
        })}

        <line
          x1={x(selectedIndex)}
          y1={CHART.top}
          x2={x(selectedIndex)}
          y2={CHART.height - CHART.bottom}
          className="hm-selection-guide"
        />

        {segments.map((points, index) =>
          points.length > 1 ? (
            <polyline
              key={index}
              points={points.join(" ")}
              fill="none"
              stroke={color}
              strokeWidth="2.7"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          ) : null,
        )}

        {values.map((value, index) => (
          <g key={index}>
            <text x={x(index)} y={CHART.height - 10} textAnchor="middle" className="hm-axis-label">
              {index + 1}
            </text>
            {Number.isFinite(value) && (
              <circle
                cx={x(index)}
                cy={y(value)}
                r={index === selectedIndex ? 6 : 3.7}
                fill={index === selectedIndex ? "#fffefa" : color}
                stroke={color}
                strokeWidth={index === selectedIndex ? 3 : 1.5}
              >
                <title>{`Nível ${index + 1}: ${numberFormat(value, decimals)}`}</title>
              </circle>
            )}
          </g>
        ))}
        <text
          x={CHART.width - CHART.right}
          y={CHART.height - 1}
          textAnchor="end"
          className="hm-axis-caption"
        >
          Nível hierárquico
        </text>
      </svg>
    </div>
  );
}

export default function HierarchyMetrics({ levels = [], selectedIndex = 0 }) {
  if (!levels.length) return null;

  const regions = levels.map((level) => Number(level.num_regions));
  const mse = levels.map((level) => Number(level.homogeneidade_mse));
  const active = levels[selectedIndex] || levels[0];

  return (
    <section className="panel hm-panel" aria-label="Evolução das métricas por nível">
      <div className="results-heading">
        <div>
          <span className="eyebrow">ANÁLISE HIERÁRQUICA</span>
          <h2>Regiões e homogeneidade por nível</h2>
        </div>
        <span className="hm-level-badge">Nível {selectedIndex + 1}</span>
      </div>

      <p className="hm-description">
        A linha vertical marca o nível selecionado acima. Os gráficos usam os valores
        já calculados pela API, sem executar novamente a segmentação.
      </p>

      <div className="hm-charts">
        <TrendChart
          title="Quantidade de regiões"
          description="Diminui com as fusões sucessivas"
          values={regions}
          selectedIndex={selectedIndex}
          color="#547c60"
          decimals={0}
        />
        <TrendChart
          title="Homogeneidade de cores (MSE)"
          description="Erro RGB médio por canal; valores menores indicam maior homogeneidade"
          values={mse}
          selectedIndex={selectedIndex}
          color="#d28b62"
          decimals={4}
        />
      </div>

      <p className="hm-footnote">
        No nível {selectedIndex + 1}: <strong>{numberFormat(active.num_regions)} regiões</strong>
        {Number.isFinite(Number(active.homogeneidade_mse)) && (
          <> · <strong>MSE {numberFormat(active.homogeneidade_mse, 4)}</strong></>
        )}. O MSE é uma medida de homogeneidade, não de acurácia semântica.
      </p>

      <table className="hm-screen-reader-only">
        <caption>Dados completos utilizados nos gráficos</caption>
        <thead><tr><th>Nível</th><th>Regiões</th><th>MSE</th></tr></thead>
        <tbody>
          {levels.map((level, index) => (
            <tr key={index}>
              <td>{index + 1}</td>
              <td>{level.num_regions}</td>
              <td>{level.homogeneidade_mse}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
