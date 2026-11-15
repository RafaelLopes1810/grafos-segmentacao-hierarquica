function Field({ label, hint, children }) {
  return <label className="field"><span className="field-label">{label}</span>{children}{hint && <small>{hint}</small>}</label>;
}

export default function SettingsPanel({ settings, onChange, onSubmit, loading, disabled }) {
  const set = (key) => (event) => onChange({ ...settings, [key]: event.target.value });
  return (
    <section className="panel settings-panel">
      <div className="section-heading"><span className="step-number">02</span><div><h2>Parâmetros</h2><p>Ajuste a análise do grafo</p></div></div>
      <div className="settings-grid">
        <Field label="Resolução"><select value={settings.preset} onChange={set('preset')}><option value="pequeno">Pequena · 160 px</option><option value="medio">Média · 320 px</option><option value="grande">Grande · 480 px</option></select></Field>
        <Field label="Conectividade"><select value={settings.connectivity} onChange={set('connectivity')}><option value="4">4 vizinhos</option><option value="8">8 vizinhos</option></select></Field>
        <Field label="Espaço de cor"><select value={settings.color_space} onChange={set('color_space')}><option value="rgb">RGB</option><option value="lab">CIE Lab</option></select></Field>
        <Field label="Níveis hierárquicos"><input type="number" min="1" max="16" step="1" value={settings.num_levels} onChange={set('num_levels')} /><small>De 1 a 16 níveis</small></Field>
        <Field label="Escala · k"><input type="number" min="0" step="10" value={settings.k} onChange={set('k')} /></Field>
        <Field label="Suavização · σ"><input type="number" min="0" max="10" step="0.1" value={settings.sigma} onChange={set('sigma')} /></Field>
        <Field label="Tamanho mínimo"><input type="number" min="1" step="1" value={settings.min_size} onChange={set('min_size')} /></Field>
      </div>
      <button className="primary-button" type="button" onClick={onSubmit} disabled={disabled || loading}>
        {loading ? <><span className="spinner" /> Processando imagem…</> : <>Executar segmentação <span aria-hidden="true">↗</span></>}
      </button>
      <p className="privacy-note">O processamento acontece localmente no backend deste projeto.</p>
    </section>
  );
}
