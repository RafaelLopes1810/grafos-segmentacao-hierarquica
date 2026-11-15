"""Testes para métricas de partições e exportação do benchmark."""

import csv

import numpy as np
import pytest

from app.evaluation import benchmark as benchmark_module
from app.evaluation.metrics import (
    contingency_matrix,
    rand_index,
    variation_of_information,
)


def test_identical_partitions_have_zero_vi_and_perfect_rand_index():
    """IDs diferentes para a mesma partição não alteram as métricas."""
    labels_true = np.array([[0, 0, 1], [0, 2, 2]], dtype=np.int32)
    labels_pred = np.array([[8, 8, 4], [8, 6, 6]], dtype=np.int32)

    assert variation_of_information(labels_true, labels_pred) == pytest.approx(0)
    assert rand_index(labels_true, labels_pred) == pytest.approx(1)


def test_metrics_match_crossed_two_by_two_partitions():
    """A contingência e as métricas devem tratar corretamente partições cruzadas."""
    labels_true = np.array([[0, 0], [1, 1]], dtype=np.int32)
    labels_pred = np.array([[0, 1], [0, 1]], dtype=np.int32)

    assert np.array_equal(contingency_matrix(labels_true, labels_pred), [[1, 1], [1, 1]])
    assert variation_of_information(labels_true, labels_pred) == pytest.approx(2)
    assert rand_index(labels_true, labels_pred) == pytest.approx(1 / 3)


def test_metrics_handle_single_pixel_and_reject_mismatched_shapes():
    """Partições de um pixel têm Rand perfeito e dimensões distintas são inválidas."""
    singleton = np.array([[42]], dtype=np.int32)

    assert variation_of_information(singleton, singleton) == 0
    assert rand_index(singleton, singleton) == 1
    with pytest.raises(ValueError, match="mesmas dimensões"):
        variation_of_information(np.zeros((1, 2)), np.zeros((2, 1)))


def test_benchmark_exports_size_connectivity_pairs(tmp_path, monkeypatch):
    """O benchmark usa as combinações exigidas e grava os tempos em CSV."""
    assert benchmark_module.MAX_SIDE_VALUES == (160, 320, 480)
    assert benchmark_module.CONNECTIVITIES == (4, 8)

    monkeypatch.setattr(benchmark_module, "MAX_SIDE_VALUES", (8,))
    output_path = tmp_path / "nested" / "benchmark.csv"

    rows = benchmark_module.run_benchmark(output_path=output_path)

    assert len(rows) == 2
    assert [row["max_side"] for row in rows] == [8, 8]
    assert [row["connectivity"] for row in rows] == [4, 8]
    assert [row["num_vertices"] for row in rows] == [64, 64]
    with output_path.open(newline="", encoding="utf-8") as csv_file:
        exported_rows = list(csv.DictReader(csv_file))
    assert len(exported_rows) == 2
    assert exported_rows[0]["load_ms"]
    assert exported_rows[0]["hierarchy_ms"]
