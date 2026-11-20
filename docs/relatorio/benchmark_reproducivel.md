# Benchmark reproduzível

O benchmark original permanece em backend/app/evaluation/benchmark.py.
A versão consolidada está em scripts/benchmark_reproducivel.py.

## Executar na raiz
Instale as dependências em um ambiente virtual:
python -m pip install -r backend/requirements.txt
python scripts/benchmark_reproducivel.py --resolutions 160 320 480 --repetitions 5 --warmups 1

Os parâmetros do algoritmo são registrados em metadados.json. Fixam-se imagem,
hash SHA-256, versões, revisão Git, resoluções e ordem sequencial.
Para reproduzir o ambiente, use as versões registradas em pacotes. Tempos variam
com hardware, carga e cache: reproduzível é o procedimento, não o tempo exato.
A imagem não é aleatória; os testes usam sementes explícitas.
Aquecimentos são feitos e descartados separadamente para cada resolução.
Não há descarte de outliers nem arredondamento antes da agregação.

## Saídas
- observacoes.csv: uma linha por resolução e repetição.
- resumo.csv: média, desvio padrão amostral, mediana, mínimo e máximo de cada métrica.
- niveis.csv: regiões e MSE de cada nível de cada repetição (somente execução nova).
- metadados.json: proveniência e configuração.
- relatorio.md: tabela de tempo total e MSE.
- tempo_total_ms.svg e homogeneidade_mse.svg: média ± desvio padrão amostral.

São necessárias ao menos duas repetições para estimar dispersão. Recomenda-se cinco
ou mais. O desvio padrão descreve dispersão, não um intervalo de confiança.
Não misture configurações ou imagens distintas no mesmo CSV.

## Custos medidos
Carga → grafo → segmentação → hierarquia e níveis → métricas da partição base.
Tempo de pipeline termina após a hierarquia; tempo total inclui métricas base.
Auditoria de inclusão/MSE, exportação, criação de SVG e aquecimento ficam fora dos
tempos. A hierarquia usada preserva o RGB exato da imagem redimensionada no MSE.
O script interrompe se alguma partição não for aninhada ou o MSE cair além de 1e-8.
Sem referência anotada, MSE mede homogeneidade e não acurácia semântica.

## Dados históricos
python scripts/benchmark_reproducivel.py --summarize data/results/benchmark_resolucoes.csv --output data/results/historico_consolidado

Essa opção usa somente a biblioteca padrão e não executa o algoritmo.
O relatório e os metadados marcam explicitamente que os resultados são históricos.
A procedência do ambiente original é desconhecida. As observações antigas já
arredondadas são agregadas como registradas; não se recupera precisão perdida.
MSE entre resoluções não é um teste de MSE monotônico: cada resolução muda a imagem.
