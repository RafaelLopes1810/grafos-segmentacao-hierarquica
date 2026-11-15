"""Mede os tempos do pipeline e salva as execuções em CSV."""

from __future__ import annotations

import csv
import time
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from app.imaging.graph_builder import build_pixel_graph
from app.imaging.loader import load_image
from app.segmentation.felzenszwalb import segment_felzenszwalb
from app.segmentation.hierarchy import HierarchyTree

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPOSITORY_ROOT / "data" / "results" / "benchmark.csv"
MAX_SIDE_VALUES = (160, 320, 480)
CONNECTIVITIES = (4, 8)
BENCHMARK_K = 300.0
BENCHMARK_MIN_SIZE = 20
BENCHMARK_SIGMA = 0.8
BENCHMARK_LEVELS = 5


def _create_benchmark_image() -> bytes:
    """Cria uma imagem sintética 480x480 e a codifica em PNG."""
    rng = np.random.default_rng(42)
    patch_size = 16
    patch_count = 480 // patch_size
    patch_colors = rng.integers(
        0,
        256,
        size=(patch_count, patch_count, 3),
        dtype=np.uint8,
    )
    pixels = np.repeat(
        np.repeat(patch_colors, patch_size, axis=0),
        patch_size,
        axis=1,
    )
    buffer = BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")
    return buffer.getvalue()


def run_benchmark(
    output_path: Path = DEFAULT_OUTPUT,
) -> list[dict[str, int | float]]:
    """Mede as etapas do pipeline para os tamanhos e conectividades definidos.

    A mesma imagem sintética é redimensionada para 160, 320 e 480 pixels no
    maior lado. Cada combinação de tamanho e conectividade gera uma linha CSV.

    Args:
        output_path: caminho do CSV; por padrão, data/results/benchmark.csv.

    Returns:
        Linhas gravadas no CSV.

    Complexidade: executa seis pipelines, com construção do grafo O(V + E),
    segmentação O(E log E) e fusões hierárquicas pelo heap.
    """
    source_image = _create_benchmark_image()
    rows: list[dict[str, int | float]] = []

    for max_side in MAX_SIDE_VALUES:
        for connectivity in CONNECTIVITIES:
            total_start = time.perf_counter()

            stage_start = time.perf_counter()
            loaded = load_image(source_image, max_side=max_side)
            load_ms = (time.perf_counter() - stage_start) * 1000

            stage_start = time.perf_counter()
            graph, width, height = build_pixel_graph(
                loaded.image,
                connectivity=connectivity,
                sigma=BENCHMARK_SIGMA,
            )
            build_graph_ms = (time.perf_counter() - stage_start) * 1000

            stage_start = time.perf_counter()
            labels, num_regions = segment_felzenszwalb(
                graph,
                width,
                height,
                k=BENCHMARK_K,
                min_size=BENCHMARK_MIN_SIZE,
            )
            segmentation_ms = (time.perf_counter() - stage_start) * 1000

            stage_start = time.perf_counter()
            hierarchy = HierarchyTree(loaded.image, labels)
            levels = hierarchy.build_levels(BENCHMARK_LEVELS)
            hierarchy_ms = (time.perf_counter() - stage_start) * 1000
            total_ms = (time.perf_counter() - total_start) * 1000

            rows.append(
                {
                    "max_side": max_side,
                    "width": width,
                    "height": height,
                    "connectivity": connectivity,
                    "num_vertices": graph.num_vertices(),
                    "num_edges": graph.num_edges(),
                    "num_regions": num_regions,
                    "num_levels": len(levels),
                    "load_ms": round(load_ms, 3),
                    "build_graph_ms": round(build_graph_ms, 3),
                    "segmentation_ms": round(segmentation_ms, 3),
                    "hierarchy_ms": round(hierarchy_ms, 3),
                    "total_ms": round(total_ms, 3),
                }
            )

    csv_path = Path(output_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    return rows


def main() -> None:
    """Executa o benchmark padrão e informa o caminho do CSV."""
    rows = run_benchmark()
    print(f"Benchmark concluído: {len(rows)} execuções em {DEFAULT_OUTPUT}")


if __name__ == "__main__":
    main()
