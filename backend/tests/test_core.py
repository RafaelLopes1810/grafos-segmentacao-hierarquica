"""Testes unitários para as estruturas de grafo e Union-Find."""

import pytest

from app.core.graph import Graph
from app.core.union_find import UnionFind


def test_union_find_unions_and_preserves_sizes():
    """Elementos unidos devem compartilhar raiz e manter tamanho correto."""
    uf = UnionFind(6)

    uf.union(0, 1)
    uf.union(1, 2)
    uf.union(3, 4)

    assert uf.find(0) == uf.find(2)
    assert uf.find(3) == uf.find(4)
    assert uf.find(5) == 5
    assert uf.size(0) == 3
    assert uf.size(3) == 2
    assert uf.num_components() == 3

    uf.find(0)
    assert uf.parent[0] == uf.parent[1] == uf.parent[2]


def test_union_find_updates_internal_weight():
    """Pesos internos auxiliares devem refletir o maior valor da componente."""
    uf = UnionFind(4)
    uf.union(0, 1)
    uf.set_internal_weight(0, 3.5)
    uf.set_internal_weight(1, 7.2)

    assert uf.get_internal_weight(0) == 7.2
    assert uf.get_internal_weight(1) == 7.2


def test_graph_tracks_edges_and_neighbors():
    """O grafo deve manter arestas não direcionadas e contagens corretas."""
    graph = Graph(5)
    graph.add_edge(0, 1, 3.5)
    graph.add_edge(0, 2, 2.5)
    graph.add_edge(1, 2, 4.0)

    assert graph.num_vertices() == 5
    assert graph.num_edges() == 3
    assert graph.degree(0) == 2
    assert graph.degree(1) == 2
    assert graph.has_edge(1, 0) is True
    assert graph.has_edge(0, 3) is False
    assert sorted(graph.neighbors(0)) == [1, 2]

    edges = list(graph.edges())
    assert sorted((u, v, w) for u, v, w in edges) == [
        (0, 1, 3.5),
        (0, 2, 2.5),
        (1, 2, 4.0),
    ]


def test_graph_rejects_duplicate_edge_update():
    """Uma mesma aresta não deve duplicar em adjacência se adicionada novamente."""
    graph = Graph()
    graph.add_edge(0, 1, 2.0)
    graph.add_edge(0, 1, 5.0)

    assert graph.num_edges() == 1
    assert graph.has_edge(0, 1) is True
    assert sorted(graph.neighbors(0)) == [1]
    assert graph.degree(0) == 1
