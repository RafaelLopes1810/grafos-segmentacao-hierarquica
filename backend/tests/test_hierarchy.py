"""Testes para o grafo de regiões e a hierarquia de fusões."""

import numpy as np
import pytest

from app.segmentation.hierarchy import HierarchyTree
from app.segmentation.region_graph import build_region_graph


def test_region_graph_has_region_statistics_and_boundary_edges():
    """O RAG deve calcular áreas, médias, centroides, caixas e adjacências."""
    image = np.zeros((2, 3, 3), dtype=np.uint8)
    image[:, 2] = (100, 0, 0)
    labels = np.array([[10, 10, 20], [10, 30, 20]], dtype=np.int32)

    rag = build_region_graph(image, labels)

    assert rag.num_regions == 3
    assert np.array_equal(
        rag.labels,
        np.array([[0, 0, 1], [0, 2, 1]], dtype=np.int32),
    )
    assert rag.regions[0].area == 3
    assert rag.regions[0].color == (0.0, 0.0, 0.0)
    assert rag.regions[0].centroid == pytest.approx((1 / 3, 1 / 3))
    assert rag.regions[0].bbox == (0, 0, 1, 1)
    assert rag.regions[1].area == 2
    assert rag.regions[1].color == (100.0, 0.0, 0.0)
    assert rag.regions[1].centroid == (2.0, 0.5)
    assert rag.regions[1].bbox == (2, 0, 2, 1)
    assert rag.graph.num_edges() == 3
    weights = {(u, v): weight for u, v, weight in rag.graph.edges()}
    assert weights[(0, 1)] == 100.0
    assert weights[(0, 2)] == 0.0
    assert weights[(1, 2)] == 100.0


def test_hierarchy_cuts_by_number_and_threshold():
    """Cortes por quantidade e altura devem retornar labels e RAG compatíveis."""
    image = np.zeros((4, 4, 3), dtype=np.uint8)
    labels = np.arange(16, dtype=np.int32).reshape(4, 4)
    hierarchy = HierarchyTree(image, labels)

    cut = hierarchy.cut_by_num_regions(6)
    threshold_cut = hierarchy.cut_by_threshold(0)

    assert cut.num_regions == 6
    assert len(np.unique(cut.labels)) == 6
    assert cut.region_graph.num_regions == 6
    assert threshold_cut.num_regions == 1
    assert np.all(threshold_cut.labels == 0)
    assert hierarchy.root_id == hierarchy.merges[-1].node_id
    assert all(
        node.num_regions_remaining == hierarchy.num_initial_regions - index - 1
        for index, node in enumerate(hierarchy.merges)
    )
    assert all(
        hierarchy.nodes[child].parent == node.node_id
        for node in hierarchy.merges
        for child in node.children
    )


def test_build_levels_are_geometric_decreasing_and_nested():
    """Níveis gerados devem diminuir em contagem e preservar inclusão exata."""
    image = np.zeros((4, 4, 3), dtype=np.uint8)
    labels = np.arange(16, dtype=np.int32).reshape(4, 4)
    hierarchy = HierarchyTree(image, labels)

    levels = hierarchy.build_levels(4)

    assert [level.num_regions for level in levels] == [16, 8, 4, 2]
    for fine, coarse in zip(levels, levels[1:]):
        assert coarse.num_regions < fine.num_regions
        for fine_id in np.unique(fine.labels):
            assert np.unique(coarse.labels[fine.labels == fine_id]).size == 1


def test_hierarchy_rejects_invalid_cut_arguments():
    """Parâmetros inválidos nos cortes devem ser rejeitados."""
    hierarchy = HierarchyTree(
        np.zeros((2, 2, 3), dtype=np.uint8),
        np.arange(4, dtype=np.int32).reshape(2, 2),
    )

    with pytest.raises(ValueError, match="num_regions"):
        hierarchy.cut_by_num_regions(5)
    with pytest.raises(ValueError, match="threshold"):
        hierarchy.cut_by_threshold(-1)
    with pytest.raises(ValueError, match="num_levels"):
        hierarchy.build_levels(0)
