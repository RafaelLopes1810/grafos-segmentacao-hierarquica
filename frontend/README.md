# Frontend — Graph Seg

Interface React + JavaScript + Vite para enviar imagens à API FastAPI, comparar níveis da hierarquia e explorar o grafo de regiões.

## Requisitos

- Node.js 18 ou superior e npm.
- Backend instalado e disponível em `http://localhost:8000`.

## Iniciar

Em um terminal, inicie a API a partir de `backend/`:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Em outro terminal, a partir de `frontend/`:

```powershell
npm install
npm run dev
```

Abra `http://localhost:5173`. A URL padrão da API é `http://localhost:8000`. Para alterá-la, copie `.env.example` para `.env` e ajuste `VITE_API_URL`; reinicie o Vite depois da alteração.

## Interface

- Upload com prévia e validação de formato, tamanho do arquivo (10 MiB) e dimensões (20 milhões de pixels).
- Configuração de preset, conectividade, espaço de cor, `k`, `sigma`, `min_size` e `num_levels`.
- Comparação entre imagem original e segmentação selecionada, com navegação dinâmica pelos níveis retornados.
- Grafo SVG do RAG usando `regions[].centroid` e `adjacency`, com opção de ocultar e controle de rótulos para preservar a legibilidade.
- Estatísticas do grafo de pixels e tempos retornados pela API.
