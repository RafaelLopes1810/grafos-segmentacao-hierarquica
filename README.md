# Segmentação Hierárquica de Imagens com Grafos

Trabalho prático de **Teoria dos Grafos e Computabilidade**. A ideia é simples de explicar e divertida de implementar: pegar uma imagem, transformar ela num grafo e usar algoritmos de grafos pra descobrir "o que é o quê" dentro dela, em vários níveis de detalhe.

## Do que se trata?

Uma imagem é só um monte de pixels. Mas se a gente olhar cada pixel como um **vértice** e ligar pixels vizinhos com **arestas** (cujo peso é o quão diferentes eles são na cor), a imagem vira um grafo. A partir daí:

1. Vamos **juntando regiões parecidas** (usando Union-Find e uma lógica estilo Kruskal / Felzenszwalb–Huttenlocher);
2. Guardamos a **ordem das fusões**, o que gera uma **hierarquia** (um dendrograma);
3. Cortando essa hierarquia em pontos diferentes, a gente consegue ver a imagem com **poucas regiões grandes** ou com **muitas regiões pequenas**;
4. Em cada nível, montamos um **grafo de regiões (RAG)** pra visualizar quem é vizinho de quem.

Tudo isso com uma interface pra navegar pelos níveis da hierarquia e ver o resultado na hora.

> **Regra do trabalho:** é proibido usar bibliotecas prontas de grafos (tipo NetworkX) na solução. Elas só podem aparecer pra **comparar desempenho**. A estrutura de grafo e os algoritmos são todos nossos.

## Grupo

| Integrante | Responsabilidade |
|---|---|
| _Ana Luiza Rezende_ | _(a definir)_ |
| _Gustavo Costa Gabrich_ | _(a definir)_ |
| _Otto Esteves Oliveira_ | _(a definir)_ |
| _Rafael de Oliveira Caldeira Lopes_ | _(a definir)_ |

## Tecnologias

- **Backend / grafos:** Python (estrutura de grafo, Union-Find, segmentação e hierarquia feitos do zero)
- **Leitura de imagens:** Pillow / OpenCV / NumPy (só pra ler e desenhar pixels, sem grafo)
- **API:** FastAPI (ou Flask) ligando o backend ao frontend
- **Frontend:** a definir (web, com visualização da segmentação e do grafo de regiões)
- **Relatório:** LaTeX, template oficial da SBC

## Estrutura de pastas

```
grafos-segmentacao-hierarquica/
├── README.md
├── .gitignore
│
├── backend/                     # Tudo que é Python
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py              # API (rotas)
│   │   ├── core/                # Estruturas de grafo "na mão"
│   │   │   ├── graph.py         #   Grafo ponderado (lista de adjacência)
│   │   │   └── union_find.py    #   Union-Find (conjuntos disjuntos)
│   │   ├── imaging/             # Da imagem pro grafo
│   │   │   ├── loader.py        #   Leitura/redimensionamento de imagens
│   │   │   └── graph_builder.py #   Pixels -> vértices, vizinhança -> arestas
│   │   ├── segmentation/        # O coração do projeto
│   │   │   ├── felzenszwalb.py  #   Segmentação baseada em grafo
│   │   │   ├── hierarchy.py     #   Dendrograma / níveis da hierarquia
│   │   │   └── region_graph.py  #   Grafo de regiões (RAG)
│   │   └── evaluation/          # Medindo se ficou bom
│   │       ├── metrics.py       #   Métricas de qualidade
│   │       └── benchmark.py     #   Tempo de execução / comparações
│   └── tests/                   # Testes automatizados
│
├── frontend/                    # Interface gráfica (framework a definir)
│   └── README.md
│
├── data/                        # Imagens e resultados
│   ├── raw/                     #   Imagens originais (datasets)
│   ├── processed/               #   Imagens redimensionadas/preparadas
│   └── results/                 #   Saídas das segmentações
│
├── docs/                        # Documentação
│   ├── etapa1/                  #   Documento de modelagem e planejamento
│   │   └── uml/                 #   Diagramas UML (classes, componentes, casos de uso)
│   └── relatorio/               #   Relatório final em LaTeX (template SBC)
│
└── scripts/                     # Scripts auxiliares (baixar dados, rodar benchmarks...)
```

## Como rodar

_Ainda em construção!_ Vamos preencher essa parte conforme o backend e o frontend forem saindo.

## Etapas do trabalho

- [ ] **Etapa 1:** Modelagem e planejamento (documento + UML)
- [ ] **Etapa 2:** Desenvolvimento da ferramenta (protótipo funcional com interface)
- [ ] **Etapa 3:** Relatório final, apresentação e vídeo