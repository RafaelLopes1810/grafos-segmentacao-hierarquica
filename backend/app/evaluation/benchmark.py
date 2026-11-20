
"""Benchmark de segmentacao hierarquica de imagens por resolucao."""

import csv
from pathlib import Path
from time import perf_counter

from app.imaging.loader import load_image
from app.imaging.graph_builder import build_pixel_graph
from app.segmentation.felzenszwalb import segment_felzenszwalb
from app.segmentation.hierarchy import HierarchyTree
from app.evaluation.metrics import (
    region_statistics,
    color_homogeneity_mse,
)


# Caminhos dos arquivos
ROOT = Path(__file__).resolve().parents[3]
IMAGEM = ROOT / "data" / "raw" / "carro.jpg"
SAIDA = ROOT / "data" / "results" / "benchmark_resolucoes.csv"


def executar_teste(resolucao, repeticao):
    """Executa a segmentacao e coleta metricas de desempenho."""

    inicio = perf_counter()

    # 1. Carregamento da imagem
    imagem = load_image(
        IMAGEM,
        max_side=resolucao
    )
    t1 = perf_counter()

    # 2. Construcao do grafo de pixels
    grafo, largura, altura = build_pixel_graph(
        imagem.image,
        connectivity=8,
        color_space="rgb",
        sigma=0.8,
    )
    t2 = perf_counter()

    # 3. Segmentacao por Felzenszwalb
    rotulos, regioes = segment_felzenszwalb(
        grafo,
        largura,
        altura,
        k=300,
        min_size=20,
    )
    t3 = perf_counter()

    # 4. Construcao da hierarquia
    hierarquia = HierarchyTree(
        imagem.image,
        rotulos
    )

    hierarquia.build_levels(8)
    t4 = perf_counter()

    # 5. Calculo das metricas
    estatisticas = region_statistics(rotulos)

    homogeneidade = color_homogeneity_mse(
        imagem.image,
        rotulos
    )

    t5 = perf_counter()

    # 6. Organizacao dos resultados
    return {
        "resolucao": resolucao,
        "repeticao": repeticao,
        "largura": largura,
        "altura": altura,
        "vertices": grafo.num_vertices(),
        "arestas": grafo.num_edges(),
        "regioes": regioes,

        # Metricas das regioes
        "tamanho_minimo_regiao": (
            estatisticas["min_region_size"]
        ),
        "tamanho_maximo_regiao": (
            estatisticas["max_region_size"]
        ),
        "tamanho_medio_regioes": round(
            estatisticas["mean_region_size"], 2
        ),
        "mediana_tamanho_regioes": round(
            estatisticas["median_region_size"], 2
        ),
        "homogeneidade_mse": round(
            homogeneidade, 4
        ),

        # Tempos de execucao em milissegundos
        "carregamento_ms": round(
            (t1 - inicio) * 1000, 2
        ),
        "grafo_ms": round(
            (t2 - t1) * 1000, 2
        ),
        "segmentacao_ms": round(
            (t3 - t2) * 1000, 2
        ),
        "hierarquia_ms": round(
            (t4 - t3) * 1000, 2
        ),
        "metricas_ms": round(
            (t5 - t4) * 1000, 2
        ),

        # Mantem o tempo original para comparacoes
        "tempo_pipeline_ms": round(
            (t4 - inicio) * 1000, 2
        ),

        # Tempo completo incluindo as metricas
        "tempo_total_ms": round(
            (t5 - inicio) * 1000, 2
        ),
    }


def main():
    """Executa os testes e salva os resultados em CSV."""

    if not IMAGEM.is_file():
        raise FileNotFoundError(
            f"Imagem nao encontrada: {IMAGEM}"
        )

    resultados = []

    print("\n=== BENCHMARK DE SEGMENTACAO ===\n")

    # Tres resolucoes e tres repeticoes
    for resolucao in (160, 320, 480):

        for repeticao in range(1, 4):

            resultado = executar_teste(
                resolucao,
                repeticao
            )

            resultados.append(resultado)

            print(
                f"{resolucao}px | "
                f"Execucao {repeticao} | "
                f"{resultado['regioes']} regioes | "
                f"{resultado['tempo_total_ms']:.2f} ms | "
                f"MSE: {resultado['homogeneidade_mse']:.4f}"
            )

    # 7. Exportacao dos resultados
    SAIDA.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with SAIDA.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as arquivo:

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=resultados[0].keys()
        )

        escritor.writeheader()
        escritor.writerows(resultados)

    print(f"\nResultados salvos em: {SAIDA}")

    # 8. Calculo automatico das medias
    print("\n=== MEDIA DOS RESULTADOS ===\n")

    for resolucao in (160, 320, 480):

        testes = [
            resultado
            for resultado in resultados
            if resultado["resolucao"] == resolucao
        ]

        quantidade = len(testes)

        media_pipeline = sum(
            teste["tempo_pipeline_ms"]
            for teste in testes
        ) / quantidade

        media_total = sum(
            teste["tempo_total_ms"]
            for teste in testes
        ) / quantidade

        media_mse = sum(
            teste["homogeneidade_mse"]
            for teste in testes
        ) / quantidade

        media_tamanho = sum(
            teste["tamanho_medio_regioes"]
            for teste in testes
        ) / quantidade

        print(f"Resolucao: {resolucao}px")
        print(f"Regioes: {testes[0]['regioes']}")
        print(f"Tempo do pipeline: {media_pipeline:.2f} ms")
        print(f"Tempo total: {media_total:.2f} ms")
        print(f"Homogeneidade MSE: {media_mse:.4f}")
        print(f"Tamanho medio das regioes: {media_tamanho:.2f}")
        print("-" * 45)

    print("\nBenchmark finalizado com sucesso!")


if __name__ == "__main__":
    main()
