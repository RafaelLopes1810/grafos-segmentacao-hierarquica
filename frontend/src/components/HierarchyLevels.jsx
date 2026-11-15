export default function HierarchyLevels({ levels, selectedIndex, onSelect }) {
  if (!levels?.length) return null;
  const level = levels[selectedIndex];
  return (
    <section className="panel hierarchy-panel">
      <div className="results-heading"><div><span className="eyebrow">EXPLORAÇÃO HIERÁRQUICA</span><h2>Navegue entre os níveis</h2></div><span className="level-count">{levels.length} {levels.length === 1 ? 'nível' : 'níveis'}</span></div>
      <div className="level-slider"><span className="granularity-label">Mais detalhado</span><input aria-label="Nível de segmentação" type="range" min="0" max={levels.length - 1} step="1" value={selectedIndex} onChange={(event) => onSelect(Number(event.target.value))} /><span className="granularity-label">Mais agrupado</span></div>
      <div className="level-ticks">{levels.map((item, index) => <button key={`${item.level}-${index}`} type="button" className={index === selectedIndex ? 'level-tick active' : 'level-tick'} onClick={() => onSelect(index)}><span>Nível {index + 1}</span><strong>{item.num_regions}</strong><small>{item.num_regions === 1 ? 'região' : 'regiões'}</small></button>)}</div>
      <div className="selected-level"><span className="selected-level-index">{String(selectedIndex + 1).padStart(2, '0')}</span><div><strong>Nível {selectedIndex + 1}</strong><small>{selectedIndex === 0 ? 'Segmentação mais detalhada' : selectedIndex === levels.length - 1 ? 'Segmentação mais agrupada' : 'Granularidade intermediária'}</small></div><strong className="region-total">{level.num_regions}<small> regiões</small></strong></div>
    </section>
  );
}
