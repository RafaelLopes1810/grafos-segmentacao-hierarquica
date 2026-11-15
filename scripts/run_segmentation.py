"""Executa o pipeline de segmentação hierárquica pela linha de comando."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.imaging.graph_builder import build_pixel_graph
from app.imaging.loader import PRESETS, load_image
from app.segmentation.felzenszwalb import segment_felzenszwalb
from app.segmentation.hierarchy import HierarchyTree


def _build_parser() -> argparse.ArgumentParser:
    """Cria o parser dos argumentos do comando."""
    parser = argparse.ArgumentParser(
        description="Executa a segmentação hierárquica de uma imagem."
    )
    parser.add_argument("--input", required=True, type=Path, help="Imagem de entrada")
    size_group = parser.add_mutually_exclusive_group()
    size_group.add_argument(
        "--preset",
        choices=sorted(PRESETS),
        help="Preset do maior lado: pequeno, medio ou grande (padrão: medio)",
    )
    size_group.add_argument(
        "--max-side",
        type=int,
        help="Limite inteiro para o maior lado da imagem",
    )
    parser.add_argument("--k", type=float, default=300.0, help="Escala de Felzenszwalb")
    parser.add_argument(
        "--min-size",
        type=int,
        default=20,
        help="Tamanho mínimo de componente na segmentação base",
    )
    parser.add_argument(
        "--levels",
        "--num-levels",
        dest="num_levels",
        type=int,
        default=8,
        help="Número máximo de níveis hierárquicos",
    )
    parser.add_argument("--sigma", type=float, default=0.8, help="Suavização gaussiana")
    parser.add_argument(
        "--connectivity",
        type=int,
        choices=(4, 8),
        default=8,
        help="Conectividade do grafo de pixels",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/results"),
        help="Diretório base de saída (padrão: data/results/)",
    )
    return parser


def _save_segmented_image(
    labels: np.ndarray, colors: np.ndarray, destination: Path
) -> None:
    """Pinta cada pixel com a cor média da região e salva um PNG."""
    segmented = np.clip(np.rint(colors[labels]), 0, 255).astype(np.uint8)
    Image.fromarray(segmented, mode="RGB").save(destination, format="PNG")


def run_pipeline(args: argparse.Namespace) -> dict[str, object]:
    """Executa as etapas do pipeline e grava imagens e resumo JSON."""
    input_path = args.input.expanduser()
    if not input_path.is_file():
        raise FileNotFoundError(f"Imagem de entrada não encontrada: {input_path}")

    max_side = args.max_side if args.max_side is not None else (args.preset or "medio")
    output_dir = args.out.expanduser() / input_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    timings: dict[str, float] = {}
    total_start = time.perf_counter()

    stage_start = time.perf_counter()
    loaded = load_image(input_path, max_side=max_side)
    timings["load"] = (time.perf_counter() - stage_start) * 1000

    stage_start = time.perf_counter()
    graph, width, height = build_pixel_graph(
        loaded.image,
        connectivity=args.connectivity,
        sigma=args.sigma,
    )
    timings["build_graph"] = (time.perf_counter() - stage_start) * 1000

    stage_start = time.perf_counter()
    labels, base_region_count = segment_felzenszwalb(
        graph,
        width,
        height,
        k=args.k,
        min_size=args.min_size,
    )
    timings["segmentation"] = (time.perf_counter() - stage_start) * 1000

    stage_start = time.perf_counter()
    hierarchy = HierarchyTree(loaded.image, labels)
    levels = hierarchy.build_levels(args.num_levels)
    timings["hierarchy"] = (time.perf_counter() - stage_start) * 1000

    stage_start = time.perf_counter()
    Image.fromarray(loaded.image, mode="RGB").save(
        output_dir / "redimensionada.png", format="PNG"
    )
    level_summaries: list[dict[str, object]] = []

    for level_index, level in enumerate(levels):
        region_colors = np.asarray(
            [
                level.region_graph.regions[region_id].color
                for region_id in range(level.num_regions)
            ],
            dtype=np.float64,
        )
        image_name = f"nivel_{level_index:02d}.png"
        _save_segmented_image(
            level.labels, region_colors, output_dir / image_name
        )
        level_summaries.append(
            {
                "level": level_index,
                "num_regions": level.num_regions,
                "image": image_name,
            }
        )

    timings["save_results"] = (time.perf_counter() - stage_start) * 1000
    timings["total"] = (time.perf_counter() - total_start) * 1000

    summary: dict[str, object] = {
        "input": input_path.name,
        "original_size": list(loaded.original_size),
        "resized_size": list(loaded.resized_size),
        "graph_stats": {
            "num_vertices": graph.num_vertices(),
            "num_edges": graph.num_edges(),
            "connectivity": args.connectivity,
        },
        "parameters": {
            "k": args.k,
            "min_size": args.min_size,
            "sigma": args.sigma,
            "base_num_regions": base_region_count,
        },
        "timings_ms": {
            name: round(milliseconds, 3)
            for name, milliseconds in timings.items()
        },
        "levels": level_summaries,
    }

    summary_path = output_dir / "resumo.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada do comando."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        summary = run_pipeline(args)
    except (ValueError, TypeError, OSError) as error:
        parser.error(str(error))

    graph_stats = summary["graph_stats"]
    timings = summary["timings_ms"]
    print(
        "Grafo: "
        f"{graph_stats['num_vertices']} vértices, "
        f"{graph_stats['num_edges']} arestas "
        f"(conectividade {graph_stats['connectivity']})"
    )
    for name in ("load", "build_graph", "segmentation", "hierarchy", "save_results", "total"):
        print(f"{name}: {timings[name]:.3f} ms")
    print(f"Resultados: {(args.out.expanduser() / args.input.stem).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
