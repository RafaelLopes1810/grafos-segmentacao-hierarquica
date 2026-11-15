"""Teste de integração do comando de segmentação."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CLI_SCRIPT = REPOSITORY_ROOT / "scripts" / "run_segmentation.py"


def test_cli_saves_all_hierarchy_outputs_and_summary(tmp_path):
    """O comando deve executar o pipeline e gerar as saídas documentadas."""
    image_path = tmp_path / "miniatura.png"
    pixels = np.zeros((4, 4, 3), dtype=np.uint8)
    for y in range(4):
        for x in range(4):
            pixels[y, x] = (x * 20, y * 20, (x + y) * 10)
    Image.fromarray(pixels).save(image_path)
    output_root = tmp_path / "results"

    completed = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            "--input",
            str(image_path),
            "--preset",
            "pequeno",
            "--k",
            "0",
            "--min-size",
            "1",
            "--levels",
            "3",
            "--sigma",
            "0",
            "--connectivity",
            "4",
            "--out",
            str(output_root),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert "16 vértices, 24 arestas" in completed.stdout

    result_dir = output_root / "miniatura"
    assert (result_dir / "redimensionada.png").exists()
    with Image.open(result_dir / "redimensionada.png") as resized:
        assert resized.size == (4, 4)

    summary = json.loads((result_dir / "resumo.json").read_text(encoding="utf-8"))
    assert summary["graph_stats"] == {
        "num_vertices": 16,
        "num_edges": 24,
        "connectivity": 4,
    }
    assert [level["num_regions"] for level in summary["levels"]] == [16, 6, 2]
    for level in summary["levels"]:
        with Image.open(result_dir / level["image"]) as segmented:
            assert segmented.size == (4, 4)
            assert segmented.mode == "RGB"
    assert {
        "load",
        "build_graph",
        "segmentation",
        "hierarchy",
        "save_results",
        "total",
    }.issubset(summary["timings_ms"])
