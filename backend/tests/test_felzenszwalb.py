"""Testes para a segmentação Felzenszwalb-Huttenlocher."""

import numpy as np
import pytest

from app.imaging.graph_builder import build_pixel_graph
from app.segmentation.felzenszwalb import segment_felzenszwalb


def _two_color_image() -> np.ndarray:
    """Cria duas regiões planas separadas por uma borda de alto contraste."""
    image = np.zeros((2, 4, 3), dtype=np.uint8)
    image[:, 2:] = 255
    return image


def test_felzenszwalb_segments_two_distinct_color_blocks():
    """Blocos uniformes com grande diferença de cor permanecem separados."""
    graph, width, height = build_pixel_graph(
        _two_color_image(), connectivity=4, sigma=0
    )

    labels, num_regions = segment_felzenszwalb(
        graph, width, height, k=0, min_size=1
    )

    assert labels.shape == (2, 4)
    assert num_regions == 2
    assert np.array_equal(labels[:, :2], np.zeros((2, 2), dtype=np.int32))
    assert np.array_equal(labels[:, 2:], np.ones((2, 2), dtype=np.int32))
    assert set(np.unique(labels)) == {0, 1}


def test_felzenszwalb_merges_small_components_in_postprocessing():
    """O pós-processamento une componentes menores que min_size."""
    graph, width, height = build_pixel_graph(
        _two_color_image(), connectivity=4, sigma=0
    )

    labels, num_regions = segment_felzenszwalb(
        graph, width, height, k=0, min_size=5
    )

    assert num_regions == 1
    assert np.all(labels == 0)


@pytest.mark.parametrize(
    ("width", "height", "k", "min_size"),
    [
        (0, 2, 0, 1),
        (4, 2, -1, 1),
        (4, 2, 0, 0),
    ],
)
def test_felzenszwalb_rejects_invalid_parameters(width, height, k, min_size):
    """Dimensões e parâmetros fora da faixa devem gerar erros claros."""
    graph, _, _ = build_pixel_graph(
        _two_color_image(), connectivity=4, sigma=0
    )

    with pytest.raises(ValueError):
        segment_felzenszwalb(graph, width, height, k=k, min_size=min_size)


def test_felzenszwalb_rejects_dimension_mismatch():
    """As dimensões precisam corresponder à quantidade de vértices."""
    graph, _, _ = build_pixel_graph(
        _two_color_image(), connectivity=4, sigma=0
    )

    with pytest.raises(ValueError, match="width \\* height"):
        segment_felzenszwalb(graph, 2, 2)
