# Backend de segmentação hierárquica

Backend em Python para segmentar imagens com Felzenszwalb-Huttenlocher e
agrupar as regiões em uma hierarquia baseada em grafos.

## Instalação

Na raiz do repositório, instale as dependências:

```powershell
python -m pip install -r backend\requirements.txt
```

## API

Inicie o servidor no diretório `backend`:

```powershell
Set-Location backend
python -m uvicorn app.main:app --reload
```

Se iniciar a partir da raiz, informe o diretório da aplicação:

```powershell
python -m uvicorn app.main:app --reload --app-dir backend
```

A documentação interativa fica em `http://127.0.0.1:8000/docs`.

### Endpoints

- `GET /health` retorna `{"status": "ok"}`.
- `POST /segment` recebe multipart/form-data com o arquivo `image` e os campos
  opcionais `max_side`, `preset`, `k`, `min_size`, `sigma`, `connectivity`,
  `num_levels`. O processamento de cores usa RGB. Informe `max_side` ou
  `preset`, não ambos.

Limites atuais da API:

- upload de até 10 MiB;
- imagem original de até 20 milhões de pixels;
- `max_side` entre 1 e 480; presets `pequeno` (160), `medio` (320) e `grande`
  (480);
- `k` finito e não negativo, `min_size` positivo, `sigma` entre 0 e 10,
  conectividade 4 ou 8 e de 1 a 16 níveis;
- `labels_png` codifica IDs em dois canais, `id = R * 256 + G`, suportando até
  65.536 regiões por nível.

CORS permite origens locais nas portas 3000 e 5173, em `localhost` e `127.0.0.1`.

### Formato da resposta de `/segment`

As imagens são strings Base64 de PNG. `original_size` está no formato
`[largura, altura]`; `width` e `height` são as dimensões após o redimensionamento.
Cada item de `regions` representa um vértice do grafo de regiões. Cada item de
`adjacency` representa uma aresta `[id_a, id_b, peso]`.

```json
{
  "width": 320,
  "height": 240,
  "original_size": [1920, 1080],
  "resized_png": "<PNG em Base64>",
  "graph_stats": {
    "num_vertices": 76800,
    "num_edges": 305000,
    "connectivity": 8
  },
  "timings_ms": {
    "load": 12,
    "build_graph": 340,
    "segmentation": 1200,
    "hierarchy": 900,
    "total": 2500
  },
  "levels": [
    {
      "level": 0,
      "num_regions": 850,
      "segmented_png": "<PNG em Base64>",
      "labels_png": "<PNG RGB em Base64; id = R * 256 + G>",
      "regions": [
        {
          "id": 0,
          "color": [120, 80, 60],
          "area": 410,
          "centroid": [32.5, 80.1]
        }
      ],
      "adjacency": [[0, 1, 12.4], [0, 5, 30.2]]
    }
  ]
}
```

`segmented_png` pinta cada pixel com a cor média de sua região. `labels_png`
codifica o ID em vermelho e verde: `R` é o byte alto, `G` o byte baixo e `B` é
zero. `regions[].color` é RGB; `centroid` usa coordenadas `(x, y)`.

## Linha de comando

Na raiz do repositório, execute:

```powershell
python scripts\run_segmentation.py `
  --input data\raw\imagem.jpg `
  --preset medio `
  --k 300 `
  --min-size 20 `
  --levels 8 `
  --out data\results
```

Também é possível usar `--max-side` em vez de `--preset`. Os resultados ficam
em `data/results/<nome-da-imagem>/`, incluindo a imagem redimensionada, PNGs
dos níveis e `resumo.json`.

## Testes

Na pasta `backend`, rode a suíte completa:

```powershell
python -m pytest -q
```

## Métricas e benchmark

`app.evaluation.metrics` implementa `variation_of_information` (em bits),
`rand_index` e `contingency_matrix`, todos calculados com NumPy.

O benchmark usa uma imagem sintética determinística para medir load, construção
do grafo de pixels, segmentação e hierarquia nos tamanhos 160, 320 e 480, com
conectividades 4 e 8. Na pasta `backend`, execute:

```powershell
python -m app.evaluation.benchmark
```

O CSV com as seis combinações é salvo em `data/results/benchmark.csv`.
