import { useEffect, useState } from 'react';
import UploadPanel from './components/UploadPanel.jsx';
import SettingsPanel from './components/SettingsPanel.jsx';
import ImageComparison, { pngSource } from './components/ImageComparison.jsx';
import HierarchyLevels from './components/HierarchyLevels.jsx';
import RegionGraph from './components/RegionGraph.jsx';
import Statistics from './components/Statistics.jsx';
import { segmentImage } from './services/api.js';

const INITIAL_SETTINGS = { preset: 'medio', connectivity: 8, color_space: 'rgb', k: 300, sigma: 0.8, min_size: 20, num_levels: 8 };

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [fileError, setFileError] = useState('');
  const [settings, setSettings] = useState(INITIAL_SETTINGS);
  const [result, setResult] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => () => { if (preview.startsWith('blob:')) URL.revokeObjectURL(preview); }, [preview]);
  const original = preview || (result?.resized_png ? pngSource(result.resized_png) : '');
  const selectedLevel = result?.levels?.[selectedIndex];

  function handleFile(nextFile, issue) {
    if (!nextFile && !issue) return;
    setFileError(issue || ''); setError(''); setResult(null); setSelectedIndex(0);
    if (nextFile) { setFile(nextFile); setPreview(URL.createObjectURL(nextFile)); }
    else if (issue) { setFile(null); setPreview(''); }
  }

  async function handleSubmit() {
    setError(''); setLoading(true);
    try {
      const data = await segmentImage(file, settings);
      if (!data.levels?.length) throw new Error('A API concluiu o processamento, mas não retornou níveis de segmentação.');
      setResult(data); setSelectedIndex(0);
    } catch (issue) { setError(issue.message || 'Ocorreu um erro durante a segmentação.'); }
    finally { setLoading(false); }
  }

  return (
    <div className="app-shell">
      <header className="topbar"><a className="brand" href="#top" aria-label="Graph Seg início"><span className="brand-mark"><i /><i /><i /><i /></span><span>graph<span className="brand-light">seg</span></span></a><span className="topbar-tag"><span className="status-dot" /> Laboratório de segmentação</span><a className="github-link" href="https://fastapi.tiangolo.com/" target="_blank" rel="noreferrer">API local <span>↗</span></a></header>
      <main id="top">
        <section className="hero"><div className="hero-copy"><span className="eyebrow"><span className="eyebrow-line" /> TEORIA DOS GRAFOS · VISÃO COMPUTACIONAL</span><h1>Enxergue a imagem<br />em <em>camadas.</em></h1><p>Transforme pixels em vértices, descubra regiões conectadas e explore a hierarquia da segmentação.</p></div><div className="hero-art" aria-hidden="true"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit orbit-three" /><span className="art-node node-a" /><span className="art-node node-b" /><span className="art-node node-c" /><span className="art-node node-d" /><span className="art-node node-e" /><span className="art-node node-f" /><span className="art-link link-a" /><span className="art-link link-b" /><span className="art-link link-c" /><span className="art-link link-d" /><div className="art-caption">pixels → regiões → hierarquia</div></div></section>
        <div className="workspace-grid"><div className="controls-column"><UploadPanel file={file} preview={preview} onFile={handleFile} error={fileError} /><SettingsPanel settings={settings} onChange={setSettings} onSubmit={handleSubmit} loading={loading} disabled={!file || Boolean(fileError)} />{error && <div className="error-banner" role="alert"><span>!</span><div><strong>Não foi possível processar</strong><p>{error}</p></div></div>}</div>
          <div className="results-column">{result && selectedLevel ? <><div className="result-title"><div><span className="eyebrow"><span className="eyebrow-line" /> RESULTADO DA ANÁLISE</span><h2>Uma imagem, várias leituras.</h2></div><span className="resolution-badge">Processada · {result.width} × {result.height}</span></div><ImageComparison original={original} segmented={selectedLevel} level={selectedIndex} originalSize={result.original_size} width={result.width} height={result.height} /><HierarchyLevels levels={result.levels} selectedIndex={selectedIndex} onSelect={setSelectedIndex} /><RegionGraph level={selectedLevel} width={result.width} height={result.height} /><Statistics graphStats={result.graph_stats} timings={result.timings_ms} regionCount={selectedLevel.num_regions} /></> : <div className="results-empty"><div className="empty-illustration"><div className="empty-frame"><span /><span /><span /><span /><span /><span /><span /><span /><span /></div><div className="empty-arrow">→</div><div className="empty-frame segmented"><span /><span /><span /><span /></div></div><span className="eyebrow">SEU ESPAÇO DE ANÁLISE</span><h2>A próxima camada<br />está na sua imagem.</h2><p>Envie uma imagem e execute a segmentação para explorar as regiões, níveis hierárquicos e conexões do grafo.</p><div className="empty-steps"><span><b>01</b> Escolha uma imagem</span><span><b>02</b> Ajuste os parâmetros</span><span><b>03</b> Explore os resultados</span></div></div>}</div>
        </div>
      </main><footer className="footer"><span>GRAPH SEG <i>·</i> Segmentação hierárquica baseada em grafos</span><span>Construído para Teoria dos Grafos</span></footer>
    </div>
  );
}
