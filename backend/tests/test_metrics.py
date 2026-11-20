
"""Testes automatizados das metricas de segmentacao."""

import numpy as np
import pytest

from app.evaluation.metrics import (
    rand_index,
    variation_of_information,
    region_statistics,
    color_homogeneity_mse,
)


def test_rand_index_identico():
    a = np.array([[0, 0], [1, 1]])
    assert rand_index(a, a) == 1.0


def test_rand_index_diferente():
    a = np.array([[0, 0], [1, 1]])
    b = np.zeros((2, 2), dtype=int)
    assert rand_index(a, b) == pytest.approx(1 / 3)


def test_variation_of_information():
    a = np.array([[0, 0], [1, 1]])
    b = np.zeros((2, 2), dtype=int)

    assert variation_of_information(a, a) == pytest.approx(0.0)
    assert variation_of_information(a, b) == pytest.approx(1.0)


def test_estatisticas_regioes():
    a = np.array([[0, 0], [1, 1]])
    resultado = region_statistics(a)

    assert resultado["num_pixels"] == 4
    assert resultado["num_regions"] == 2
    assert resultado["min_region_size"] == 2
    assert resultado["max_region_size"] == 2
    assert resultado["mean_region_size"] == 2.0


def test_homogeneidade_cores():
    imagem = np.array([
        [[0, 0, 0], [0, 0, 0]],
        [[255, 255, 255], [255, 255, 255]],
    ], dtype=np.uint8)

    rotulos = np.array([[0, 0], [1, 1]])

    assert color_homogeneity_mse(
        imagem, rotulos
    ) == pytest.approx(0.0)


def test_dimensoes_incompativeis():
    a = np.zeros((2, 2), dtype=int)
    b = np.zeros((3, 3), dtype=int)

    with pytest.raises(ValueError):
        rand_index(a, b)
