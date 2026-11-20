"""Benchmark com dados brutos, proveniência, médias, dispersão e SVG.
Exemplos (raiz do projeto):
  python scripts/benchmark_reproducivel.py --resolutions 160 320 480 --repetitions 5
  python scripts/benchmark_reproducivel.py --summarize data/results/benchmark_resolucoes.csv
A sumarização usa somente a biblioteca padrão. A execução requer backend/requirements.txt.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def write_csv(path, rows):
    if not rows:
        raise ValueError("Nenhuma observação para exportar.")
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows):
    """Desvio padrão amostral (ddof=1); n=1 é rejeitado, sem inventar dispersão."""
    groups = defaultdict(list)
    for row in rows:
        numeric = {key: float(value) for key, value in row.items()}
        if not all(math.isfinite(v) for v in numeric.values()):
            raise ValueError("Observações devem ser finitas.")
        if numeric["resolucao"] <= 0 or not numeric["resolucao"].is_integer():
            raise ValueError("Resolução deve ser inteira e positiva.")
        if numeric["repeticao"] <= 0 or not numeric["repeticao"].is_integer():
            raise ValueError("Repetição deve ser inteira e positiva.")
        if any(value < 0 for key, value in numeric.items() if key.endswith("_ms")):
            raise ValueError("Tempos não podem ser negativos.")
        groups[int(numeric["resolucao"])].append(numeric)
    if not groups:
        raise ValueError("Nenhuma observação.")
    result = []
    for resolution, samples in sorted(groups.items()):
        if len(samples) < 2:
            raise ValueError("São necessárias pelo menos duas repetições por resolução.")
        if len({s["repeticao"] for s in samples}) != len(samples):
            raise ValueError("Repetição duplicada na mesma resolução.")
        if any(set(s) != set(samples[0]) for s in samples):
            raise ValueError("Observações têm colunas diferentes.")
        row = {"resolucao": resolution, "n": len(samples)}
        for key in samples[0]:
            if key in ("resolucao", "repeticao"):
                continue
            values = [sample[key] for sample in samples]
            row[key + "_media"] = statistics.mean(values)
            row[key + "_desvio"] = statistics.stdev(values)
            row[key + "_mediana"] = statistics.median(values)
            row[key + "_min"] = min(values)
            row[key + "_max"] = max(values)
        result.append(row)
    return result


def svg_chart(summary, metric, title, unit):
    """Pontos com barras de média ± desvio; limites inferiores em zero."""
    high = max(r[metric + "_media"] + r[metric + "_desvio"] for r in summary)
    high = high * 1.15 if high else 1.0
    width, height = 760, 420
    left, right, top, bottom = 85, 700, 65, 340
    y = lambda value: bottom - (bottom - top) * max(0, value) / high
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="760" height="420" viewBox="0 0 760 420">',
             '<rect width="760" height="420" fill="white"/>',
             '<g font-family="sans-serif" font-size="13" fill="#17212b">',
             f'<text x="85" y="28" font-size="18">{escape(title)}</text>',
             f'<text x="85" y="49">{escape(unit)} · média ± desvio padrão amostral</text>']
    for tick in range(6):
        value = high * tick / 5
        position = y(value)
        parts += [f'<path d="M{left},{position} H{right}" stroke="#dde3e8"/>',
                  f'<text x="75" y="{position+4}" text-anchor="end">{value:.2f}</text>']
    parts += [f'<path d="M{left},{top} V{bottom} H{right}" fill="none" stroke="#17212b"/>']
    for index, row in enumerate(summary):
        x = left + (right - left) * (index + 0.5) / len(summary)
        mean, sd = row[metric + "_media"], row[metric + "_desvio"]
        parts += [f'<path d="M{x},{y(mean-sd)} V{y(mean+sd)} M{x-7},{y(mean-sd)} H{x+7} M{x-7},{y(mean+sd)} H{x+7}" stroke="#1967b3" fill="none"/>',
                  f'<circle cx="{x}" cy="{y(mean)}" r="5" fill="#1967b3"/>',
                  f'<text x="{x}" y="365" text-anchor="middle">{row["resolucao"]} px</text>',
                  f'<text x="{x}" y="385" text-anchor="middle">n={row["n"]}</text>']
    return "\n".join(parts + ['<text x="380" y="410" text-anchor="middle">Limite do maior lado (resolução)</text>', '</g></svg>'])


def export_results(rows, output, metadata):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    summary = summarize(rows)
    write_csv(output / "observacoes.csv", rows)
    write_csv(output / "resumo.csv", summary)
    (output / "metadados.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    metrics = [("tempo_total_ms", "Tempo total", "ms"),
               ("homogeneidade_mse", "Homogeneidade RGB da partição base", "RGB² por canal")]
    report = ["# Benchmark de segmentação", "", metadata["origem"], "",
              "Médias ± desvios padrão amostrais; mediana, mínimo e máximo no CSV.",
              "Barras de dispersão não são intervalos de confiança.",
              "O MSE entre resoluções não testa monotonicidade da hierarquia: são imagens diferentes.", "",
              "| Resolução | n | Tempo total (ms) | MSE RGB |",
              "|---:|---:|---:|---:|"]
    for row in summary:
        report.append(f'| {row["resolucao"]} | {row["n"]} | {row["tempo_total_ms_media"]:.3f} ± {row["tempo_total_ms_desvio"]:.3f} | {row["homogeneidade_mse_media"]:.4f} ± {row["homogeneidade_mse_desvio"]:.4f} |')
    for metric, title, unit in metrics:
        filename = metric + ".svg"
        (output / filename).write_text(svg_chart(summary, metric, title, unit), encoding="utf-8")
        report.extend(["", f"![{title}]({filename})"])
    (output / "relatorio.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return summary


def measure(image_path, resolution, repetition, config):
    import numpy as np
    from app.imaging.loader import load_image
    from app.imaging.graph_builder import build_pixel_graph
    from app.segmentation.felzenszwalb import segment_felzenszwalb
    from app.segmentation.hierarchy import HierarchyTree
    from app.evaluation.metrics import color_homogeneity_mse, region_statistics

    start = perf_counter()
    loaded = load_image(image_path, max_side=resolution)
    t1 = perf_counter()
    graph, width, height = build_pixel_graph(loaded.image,
        connectivity=config["connectivity"], sigma=config["sigma"], color_space=config["color_space"])
    t2 = perf_counter()
    labels, regions = segment_felzenszwalb(graph, width, height,
        k=config["k"], min_size=config["min_size"])
    t3 = perf_counter()
    tree = HierarchyTree(loaded.image, labels)
    levels = tree.build_levels(config["num_levels"])
    t4 = perf_counter()
    stats = region_statistics(labels)
    mse = color_homogeneity_mse(loaded.image, labels)
    t5 = perf_counter()
    # Auditoria excluída dos tempos medidos; valores de cada nível são exportados.
    audits = []
    previous = None
    previous_mse = -1.0
    for level in levels:
        current_mse = color_homogeneity_mse(loaded.image, level.labels)
        if current_mse < previous_mse - 1e-8:
            raise RuntimeError("MSE decrescente na hierarquia.")
        if previous is not None:
            for region in np.unique(previous):
                if np.unique(level.labels[previous == region]).size != 1:
                    raise RuntimeError("Partições não aninhadas.")
        audits.append({"resolucao": resolution, "repeticao": repetition,
                       "nivel": level.level, "regioes": level.num_regions, "mse": current_mse})
        previous, previous_mse = level.labels, current_mse
    return {
        "resolucao": resolution, "repeticao": repetition, "largura": width, "altura": height,
        "vertices": graph.num_vertices(), "arestas": graph.num_edges(), "regioes": regions,
        "tamanho_minimo_regiao": stats["min_region_size"],
        "tamanho_maximo_regiao": stats["max_region_size"],
        "tamanho_medio_regioes": stats["mean_region_size"],
        "mediana_tamanho_regioes": stats["median_region_size"],
        "homogeneidade_mse": mse, "carregamento_ms": (t1-start)*1000,
        "grafo_ms": (t2-t1)*1000, "segmentacao_ms": (t3-t2)*1000,
        "hierarquia_ms": (t4-t3)*1000, "metricas_ms": (t5-t4)*1000,
        "tempo_pipeline_ms": (t4-start)*1000, "tempo_total_ms": (t5-start)*1000,
    }, audits


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=ROOT / "data/raw/carro.jpg")
    parser.add_argument("--output", type=Path, default=ROOT / "data/results/reproduzivel")
    parser.add_argument("--resolutions", type=int, nargs="+", default=[160, 320, 480])
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--summarize", type=Path)
    args = parser.parse_args(argv)
    if args.repetitions < 2 or args.warmups < 0 or any(n < 1 for n in args.resolutions):
        parser.error("Use pelo menos 2 repetições, aquecimento não negativo e resoluções positivas.")
    if len(set(args.resolutions)) != len(args.resolutions):
        parser.error("Resoluções duplicadas.")
    if args.summarize:
        with args.summarize.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        metadata = {"origem": "Sumarização de dados existentes; nenhuma nova medição foi realizada.",
                    "arquivo_fonte": str(args.summarize),
                    "sha256_fonte": hashlib.sha256(args.summarize.read_bytes()).hexdigest(),
                    "ambiente_original": "Não registrado; não inferido."}
    else:
        config = {"connectivity": 8, "color_space": "rgb", "sigma": 0.8,
                  "k": 300, "min_size": 20, "num_levels": 8}
        image_hash = hashlib.sha256(args.image.read_bytes()).hexdigest()
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        metadata = {"origem": "Medições novas, sequenciais, após aquecimento por resolução.",
                    "python": sys.version, "platform": platform.platform(),
                    "processor": platform.processor(), "git_revision": revision.stdout.strip() or None,
                    "imagem": str(args.image), "sha256_imagem": image_hash,
                    "configuracao": config, "resolucoes": args.resolutions,
                    "repeticoes": args.repetitions, "aquecimentos": args.warmups,
                    "pacotes": {name: importlib.metadata.version(name) for name in
                                ("numpy", "pillow", "opencv-python")}}
        rows, levels = [], []
        for resolution in args.resolutions:
            for _ in range(args.warmups):
                measure(args.image, resolution, 0, config)
            for repetition in range(1, args.repetitions + 1):
                row, audits = measure(args.image, resolution, repetition, config)
                rows.append(row)
                levels.extend(audits)
                print(f'{resolution}px #{repetition}: {row["tempo_total_ms"]:.3f} ms')
        args.output.mkdir(parents=True, exist_ok=True)
        write_csv(args.output / "niveis.csv", levels)
    summary = export_results(rows, args.output, metadata)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
