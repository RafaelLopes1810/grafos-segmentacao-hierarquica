# Segmentação Hierárquica de Imagens com Grafos

Projeto da disciplina **Teoria dos Grafos e Computabilidade**. Uma imagem digital é transformada em um grafo ponderado de pixels; um algoritmo de segmentação forma regiões e uma hierarquia de fusões permite explorar diferentes níveis de detalhamento. A aplicação combina **Python + FastAPI** no backend e **React + Vite** no frontend.

> As estruturas de grafos, Union-Find, segmentação e hierarquia foram implementadas no projeto; não é utilizada uma biblioteca pronta de algoritmos de grafos para realizar o processamento.

## Demonstração visual

As imagens abaixo foram produzidas com `data/raw/carro.jpg`, resolução máxima de 320 px, conectividade 8, `k=300`, `sigma=0.8`, `min_size=20` e oito níveis.

|                       Imagem de entrada                        |                      Nível 1: 186 regiões                      |                      Nível 8: 2 regiões                       |
| :------------------------------------------------------------: | :------------------------------------------------------------: | :-----------------------------------------------------------: |
| ![Carro redimensionado](data/results/carro/redimensionada.png) | ![Segmentação mais detalhada](data/results/carro/nivel_00.png) | ![Segmentação mais agrupada](data/results/carro/nivel_07.png) |

A interface permite escolher o nível, visualizar o grafo de adjacência de regiões (RAG), consultar áreas das regiões, tempos e homogeneidade RGB (MSE) e acompanhar **dois gráficos por nível**: quantidade de regiões e MSE.

## Integrantes

- Ana Luiza Rezende
- Gustavo Costa Gabrich
- Otto Esteves Oliveira
- Rafael de Oliveira Caldeira Lopes

As contribuições individuais podem ser verificadas no histórico de commits do repositório.

## Requisitos

- **Python 3.10 ou superior** e `pip` (o benchmark registrado foi realizado no Python 3.14.5).
- **Node.js 18 ou superior** e npm (Vite 5 / React 18).
- Git para versionamento.
- Sistema com navegador moderno e portas locais **8000** (API) e **5173** (frontend) disponíveis.

## Instalação no Windows (PowerShell)

Abra o terminal **na pasta raiz do repositório**:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
```

Em um **primeiro terminal**, inicie a API:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Em um **segundo terminal**, na raiz do repositório:

```powershell
cd frontend
npm ci
npm run dev
```

Acesse **http://localhost:5173**. A API deve responder em **http://localhost:8000/health** com `{"status":"ok"}`. Documentação interativa: **http://localhost:8000/docs**.

> Se o frontend não alcançar o backend, copie `frontend/.env.example` para `frontend/.env`, confira `VITE_API_URL=http://localhost:8000` e reinicie o Vite. Para outros sistemas operacionais, use o ativador apropriado do ambiente virtual (por exemplo, `source .venv/bin/activate`).

## Como utilizar a aplicação

1. Envie uma imagem suportada no painel **Imagem de entrada**.
2. Defina os parâmetros de segmentação e clique em **Executar segmentação**.
3. Compare a imagem original e a segmentada; selecione um nível na navegação hierárquica.
4. Observe os **gráficos de regiões e MSE**, o **RAG** e as **estatísticas** atualizados para o nível escolhido.

### Parâmetros

| Parâmetro       | Função                                                          | Valor padrão da interface |
| --------------- | --------------------------------------------------------------- | ------------------------- |
| Resolução       | Limita o maior lado da imagem; preserva a proporção             | Média (320 px)            |
| Conectividade   | Considera 4 ou 8 vizinhos por pixel no grafo inicial            | 8                         |
| Espaço de cores | Distância dos pesos das arestas: RGB ou CIELAB                  | RGB                       |
| `k`             | Controla a escala do agrupamento inicial                        | 300                       |
| `sigma`         | Suavização gaussiana antes do cálculo dos pesos                 | 0,8                       |
| `min_size`      | Pós-processamento de componentes pequenas                       | 20 pixels                 |
| `num_levels`    | Máximo de níveis hierárquicos solicitados (1 a 16 na interface) | 8                         |

O backend pode devolver **menos níveis** que o solicitado quando não existem quantidades distintas de regiões suficientes. O MSE avalia a homogeneidade RGB dentro das regiões; **não é uma medida de reconhecimento de objetos**. RI e VI comparam partições, não avaliam acurácia sem uma referência anotada.

## Testes automatizados

Com as dependências Python instaladas, execute os comandos abaixo **a partir da raiz do repositório**:

```powershell
cd backend
python -m pytest tests -v
```

Os testes cobrem a API FastAPI, estruturas de grafos, segmentação, hierarquia, invariantes matemáticos, métricas e casos-limite. Incluem verificação de que partições são aninhadas e de que o MSE não diminui nos agrupamentos da mesma imagem.

## Execução pela linha de comando (sem frontend)

Na raiz do repositório:

```powershell
python scripts/run_segmentation.py --input data/raw/carro.jpg --max-side 320 --connectivity 8 --color-space rgb --k 300 --sigma 0.8 --min-size 20 --levels 8 --out data/results
```

O comando salva os arquivos em `data/results/carro/`: `redimensionada.png`, `nivel_00.png` até o último nível produzido e `resumo.json` com as características do grafo, parâmetros, níveis e tempos.

## Benchmark reproduzível

Na raiz do repositório, execute uma nova rodada em uma pasta de saída separada para não sobrescrever os resultados versionados:

```powershell
python scripts/benchmark_reproducivel.py --image data/raw/carro.jpg --resolutions 160 320 480 --repetitions 5 --warmups 1 --output data/results/benchmark_local
```

O script fixa a imagem e os parâmetros, realiza um aquecimento por resolução e cinco medições sequenciais e registra o ambiente e a revisão Git. Gera:

| Arquivo                                        | Conteúdo                                                |
| ---------------------------------------------- | ------------------------------------------------------- |
| `observacoes.csv`                              | Medições individuais por resolução/repetição            |
| `resumo.csv`                                   | Média, desvio padrão amostral, mediana, mínimo e máximo |
| `niveis.csv`                                   | Número de regiões e MSE por nível em cada execução nova |
| `metadados.json`                               | Configuração, versões, hash da imagem e revisão Git     |
| `relatorio.md`                                 | Síntese dos resultados                                  |
| `tempo_total_ms.svg` e `homogeneidade_mse.svg` | Gráficos com médias e dispersão                         |

Para **consolidar o benchmark histórico sem executar o algoritmo novamente**:

```powershell
python scripts/benchmark_reproducivel.py --summarize data/results/benchmark_resolucoes.csv --output data/results/historico_local
```

Os dados completos da execução já registrada estão em [`data/results/reproduzivel/`](data/results/reproduzivel/). Consulte também [`docs/relatorio/benchmark_reproducivel.md`](docs/relatorio/benchmark_reproducivel.md).

### Exemplo de resultado registrado

| Limite do maior lado | Vértices | Arestas | Regiões base | Tempo médio total (5 execuções) |
| -------------------: | -------: | ------: | -----------: | ------------------------------: |
|               160 px |   17.120 |  67.681 |           62 |               474,31 ± 89,26 ms |
|               320 px |   68.160 | 271.043 |          186 |             1.471,35 ± 70,06 ms |
|               480 px |  153.600 | 612.002 |          416 |            3.257,31 ± 105,04 ms |

O desvio padrão descreve a dispersão das medições, **não um intervalo de confiança**. Tempos dependem do ambiente. Como a imagem muda quando redimensionada, a comparação de MSE entre resoluções não verifica monotonicidade da hierarquia.

## Apresentação e vídeo demonstrativo

O projeto conta com materiais de apresentação e um vídeo demonstrativo das funcionalidades desenvolvidas pelos integrantes.

### Slides da apresentação

Os slides apresentam a contextualização do problema, modelagem do grafo, algoritmos implementados, arquitetura, interface e resultados obtidos.

Estão disponíveis em dois formatos:

- [Apresentação em PDF](docs/apresenta%C3%A7%C3%A3o/Apresentacao_GraphSeg.pdf)
- [Apresentação em PowerPoint](docs/apresenta%C3%A7%C3%A3o/Apresentacao_GraphSeg.pptx)

Os arquivos estão armazenados na pasta `docs/apresentação/`.

### Vídeo demonstrativo

O vídeo apresenta o funcionamento da ferramenta e a explicação das funcionalidades desenvolvidas pelos integrantes.

Durante a demonstração, são abordados:

- Construção do grafo e segmentação hierárquica no backend.
- Interface React e navegação pelos níveis de segmentação.
- Métricas de avaliação, testes automatizados e validação matemática.
- Benchmark reproduzível e avaliação de desempenho.
- Gráficos de regiões e MSE, modelagem UML e documentação.

**Acesso ao vídeo:**

- [Assistir ao vídeo demonstrativo no YouTube](https://youtu.be/A1oKSajlQoY)
- [Documentação do vídeo](docs/video/README.md)

O arquivo `docs/video/README.md` contém a referência ao vídeo da apresentação.

## Estrutura do repositório

```text
backend/
  app/
    core/                # Graph, UnionFind
    imaging/             # leitura e grafo de pixels
    segmentation/        # Felzenszwalb, hierarquia e RAG
    evaluation/          # métricas e benchmark original
    main.py              # API FastAPI
  tests/                 # testes automatizados

frontend/
  src/
    components/          # upload, navegação, RAG, gráficos e estatísticas
    services/api.js      # cliente HTTP
    App.jsx              # composição da interface
  README.md

data/
  raw/carro.jpg          # imagem do benchmark
  results/               # segmentações e experimentos

docs/
  apresentação/          # slides em PDF e PowerPoint
    Apresentacao_GraphSeg.pdf
    Apresentacao_GraphSeg.pptx
  etapa1/uml/            # diagramas de classes, componentes e sequência
  relatorio/             # PDF SBC e documentação matemática/experimental
  video/                 # referência ao vídeo demonstrativo
    README.md

scripts/
  run_segmentation.py
  benchmark_reproducivel.py

README.md
```

## Documentação e materiais

- [Modelagem e planejamento da solução](docs/etapa1/uml/modelagem_e_planejamento.md)
- [Diagramas UML — Classes, Componentes e Sequência](docs/etapa1/uml/README.md)
- [Validação matemática da hierarquia](docs/relatorio/validacao_matematica.md)
- [Metodologia e resultados do benchmark](docs/relatorio/benchmark_reproducivel.md)
- [Relatório científico em PDF — Padrão SBC](docs/relatorio/Segmenta%C3%A7%C3%A3o_Hier%C3%A1rquica_de_Imagens_Baseada_em_Grafos%20%283%29.pdf)
- [Código-fonte do relatório em LaTeX](docs/relatorio/main.tex)
- [Capturas da interface e resultados](docs/relatorio/figuras/)
- [Documentação do frontend React](frontend/README.md)
- [Slides da apresentação em PDF](docs/apresenta%C3%A7%C3%A3o/Apresentacao_GraphSeg.pdf)
- [Slides da apresentação em PowerPoint](docs/apresenta%C3%A7%C3%A3o/Apresentacao_GraphSeg.pptx)
- [Vídeo demonstrativo do projeto](https://youtu.be/A1oKSajlQoY)

O relatório científico apresenta a fundamentação teórica,
a modelagem matemática, os algoritmos implementados,
a análise de complexidade, os testes automatizados,
os resultados experimentais e as contribuições individuais.

O projeto também disponibiliza os diagramas UML,
os dados do benchmark e as imagens obtidas durante
a segmentação hierárquica.

Os materiais de apresentação estão disponíveis na pasta
`docs/apresentação/`, enquanto o vídeo demonstrativo
pode ser acessado pelo link disponibilizado neste README.
