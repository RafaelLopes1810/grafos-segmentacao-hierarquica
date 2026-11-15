export function pngSource(encoded) {
  return encoded ? `data:image/png;base64,${encoded}` : '';
}

export default function ImageComparison({ original, segmented, level, originalSize, width, height }) {
  return (
    <div className="image-comparison">
      <figure className="image-card"><div className="image-wrap"><img src={original} alt="Imagem original" /></div><figcaption><span>Original</span><small>{originalSize[0]} × {originalSize[1]} px</small></figcaption></figure>
      <figure className="image-card"><div className="image-wrap"><img src={pngSource(segmented.segmented_png)} alt={`Segmentação do nível ${level + 1}`} /></div><figcaption><span>Segmentada</span><small>{segmented.num_regions} regiões</small></figcaption></figure>
    </div>
  );
}
