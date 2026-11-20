# Frontend — Graph Seg

Interface desenvolvida em **React 18 + Vite 5**, integrada à API **FastAPI** do projeto de segmentação hierárquica de imagens baseada em grafos.

## Requisitos

- Node.js 18 ou superior e npm.
- Backend instalado e em execução na URL `http://localhost:8000` (padrão).

## Iniciar a aplicação

No primeiro terminal, a partir de `backend/`, inicie a API:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Em outro terminal, dentro de `frontend/`:

```powershell
npm ci
npm run dev
```

Abra **http://localhost:5173** no navegador.

### Configuração opcional da API

O endereço padrão é `http://localhost:8000`. Para alterá-lo:

```powershell
Copy-Item .env.example .env
```

Edite `VITE_API_URL` no `.env` e reinicie o Vite após alterações. O serviço HTTP é implementado em `src/services/api.js`.

## Funcionalidades

- Envio de imagem com pré-visualização e validação básica no navegador.
- Configurações: resolução, conectividade 4/8, RGB/CIELAB, `k`, `sigma`, `min_size`, `num_levels`.
- Comparação entre imagem original e segmentação do nível selecionado.
- Navegação por níveis hierárquicos com controle deslizante e botões.
- **Dois gráficos SVG sem dependências adicionais:** quantidade de regiões e MSE RGB em todos os níveis.
- Indicador vertical e ponto destacado sincronizados com o nível selecionado.
- Grafo de adjacência de regiões (RAG) exibido a partir de `regions[].centroid` e `adjacency`.
- Estatísticas do grafo de pixels, tamanhos das regiões, MSE e tempos do processamento.

### Gráficos de níveis

O componente `src/components/HierarchyMetrics.jsx` utiliza os dados **já retornados pela API**:

```json
{
  "levels": [
    { "level": 0, "num_regions": 186, "homogeneidade_mse": 732.383 },
    { "level": 1, "num_regions": 97, "homogeneidade_mse": 765.6348 }
  ]
}
```

*O trecho é ilustrativo e omite outros campos do contrato, como imagens Base64 e adjacências.*

Ao selecionar outro nível em `HierarchyLevels.jsx`, a propriedade `selectedIndex` recebida pelo componente de gráficos muda e o marcador é atualizado **sem solicitar nova segmentação ao backend**. O MSE representa homogeneidade RGB, não avaliação semântica.

## Verificação

```powershell
npm run build
```

Depois de iniciar o backend e o frontend, carregue `data/raw/carro.jpg` com resolução média (320 px), `k=300`, `sigma=0.8`, `min_size=20` e oito níveis. Os gráficos devem exibir 186 regiões / MSE 732,3830 no nível 1, 27 / 1.075,1234 no nível 4 e 2 / 5.248,3535 no nível 8. O valor destacado deve acompanhar a seleção.

Não são necessárias bibliotecas adicionais de gráficos: os SVGs são desenhados diretamente pelo React.
