
"""Benchmark de segmentação hierárquica por resolução."""

import csv
from pathlib import Path
from time import perf_counter

from app.imaging.loader import load_image
from app.imaging.graph_builder import build_pixel_graph
from app.segmentation.felzenszwalb import segment_felzenszwalb
from app.segmentation.hierarchy import HierarchyTree


ROOT = Path(__file__).resolve().parents[3]
IMAGEM = ROOT / "data" / "raw" / "carro.jpg"
SAIDA = ROOT / "data" / "results" / "benchmark_resolucoes.csv"


def executar_teste(resolucao, repeticao):
    inicio = perf_counter()

    imagem = load_image(IMAGEM, max_side=resolucao)
    t1 = perf_counter()

    grafo, largura, altura = build_pixel_graph(
        imagem.image,
        connectivity=8,
        color_space="rgb",
        sigma=0.8,
    )
    t2 = perf_counter()

    rotulos, regioes = segment_felzenszwalb(
        grafo, largura, altura, k=300, min_size=20
    )
    t3 = perf_counter()

    hierarquia = HierarchyTree(imagem.image, rotulos)
    hierarquia.build_levels(8)
    t4 = perf_counter()

    return {
        "resolucao": resolucao,
        "repeticao": repeticao,
        "vertices": grafo.num_vertices(),
        "arestas": grafo.num_edges(),
        "regioes": regioes,
        "carregamento_ms": round((t1 - inicio) * 1000, 2),
        "grafo_ms": round((t2 - t1) * 1000, 2),
        "segmentacao_ms": round((t3 - t2) * 1000, 2),
        "hierarquia_ms": round((t4 - t3) * 1000, 2),
        "tempo_total_ms": round((t4 - inicio) * 1000, 2),
    }


def main():
    if not IMAGEM.is_file():
        raise FileNotFoundError(f"Imagem não encontrada: {IMAGEM}")

    resultados = []

    for resolucao in (160, 320, 480):
        for repeticao in range(1, 4):
            resultado = executar_teste(resolucao, repeticao)
            resultados.append(resultado)

            print(
                f"{resolucao}px | Execução {repeticao} | "
                f"{resultado['regioes']} regiões | "
                f"{resultado['tempo_total_ms']} ms"
            )

    SAIDA.parent.mkdir(parents=True, exist_ok=True)

    with SAIDA.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(
            arquivo, fieldnames=resultados[0].keys()
        )
        escritor.writeheader()
        escritor.writerows(resultados)

    print(f"\nResultados salvos em: {SAIDA}")
    
    
    print("\n=== MÉDIA DOS RESULTADOS ===")

    for resolucao in (160, 320, 480):
        tempos = [
            resultado["tempo_total_ms"]
            for resultado in resultados
            if resultado["resolucao"] == resolucao
        ]

        media = sum(tempos) / len(tempos)

        print(
            f"Resolução {resolucao}px | "
            f"Tempo médio: {media:.2f} ms"
        )



if __name__ == "__main__":
    main()
