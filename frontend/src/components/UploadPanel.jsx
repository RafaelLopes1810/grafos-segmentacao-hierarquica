const MAX_BYTES = 10 * 1024 * 1024;
const MAX_PIXELS = 20_000_000;
const ACCEPTED = new Set(['image/bmp', 'image/gif', 'image/jpeg', 'image/png', 'image/tiff', 'image/webp']);
const EXTENSIONS = /\.(bmp|gif|jpe?g|png|tiff?|webp)$/i;

function formatBytes(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function UploadPanel({ file, preview, onFile, error }) {
  async function handleFile(candidate) {
    if (!candidate) return;
    if (!(ACCEPTED.has(candidate.type) || (!candidate.type && EXTENSIONS.test(candidate.name)))) {
      onFile(null, 'Formato não suportado. Envie BMP, GIF, JPEG, PNG, TIFF ou WEBP.');
      return;
    }
    if (candidate.size > MAX_BYTES) {
      onFile(null, 'O arquivo excede o limite de 10 MiB da API.');
      return;
    }
    try {
      const dimensions = await new Promise((resolve, reject) => {
        const image = new Image();
        image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight });
        image.onerror = () => reject(new Error('O navegador não conseguiu ler esta imagem.'));
        image.src = URL.createObjectURL(candidate);
      });
      if (dimensions.width * dimensions.height > MAX_PIXELS) {
        onFile(null, 'A imagem excede o limite de 20 milhões de pixels da API.');
        return;
      }
      onFile(candidate, null);
    } catch {
      // TIFF and some less common codecs may be valid but not previewable in the browser.
      onFile(candidate, null);
    }
  }

  return (
    <section className="panel upload-panel">
      <div className="section-heading"><span className="step-number">01</span><div><h2>Imagem de entrada</h2><p>Escolha uma imagem para começar</p></div></div>
      <label className={`drop-zone ${file ? 'has-file' : ''}`}>
        <input type="file" accept=".bmp,.gif,.jpg,.jpeg,.png,.tif,.tiff,.webp,image/bmp,image/gif,image/jpeg,image/png,image/tiff,image/webp" onChange={(event) => handleFile(event.target.files?.[0])} />
        {preview ? <img className="upload-preview" src={preview} alt="Prévia da imagem selecionada" /> : <div className="upload-placeholder"><span className="upload-icon">↑</span><strong>Solte sua imagem aqui</strong><span>ou clique para procurar no computador</span><small>PNG, JPG, WEBP, TIFF, BMP ou GIF · até 10 MiB</small></div>}
        {file && <span className="file-chip">{file.name} <span>{formatBytes(file.size)}</span></span>}
      </label>
      {error && <p className="inline-error" role="alert">{error}</p>}
    </section>
  );
}
