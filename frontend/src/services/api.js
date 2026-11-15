const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export async function segmentImage(file, settings, signal) {
  const form = new FormData();
  form.append('image', file);
  form.append('preset', settings.preset);
  form.append('connectivity', String(settings.connectivity));
  form.append('color_space', settings.color_space);
  form.append('k', String(settings.k));
  form.append('sigma', String(settings.sigma));
  form.append('min_size', String(settings.min_size));
  form.append('num_levels', String(settings.num_levels));

  let response;
  try {
    response = await fetch(`${API_URL}/segment`, { method: 'POST', body: form, signal });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error(`Não foi possível conectar à API em ${API_URL}. Verifique se o backend está iniciado.`);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join('; ') : detail || `A API respondeu com erro ${response.status}.`);
  }
  return response.json();
}

export { API_URL };
