"""Segmentação baseada em grafo pelo método Felzenszwalb–Huttenlocher."""

from __future__ import annotations

from math import isfinite

import numpy as np

from app.core.graph import Graph
from app.core.union_find import UnionFind


def segment_felzenszwalb(
    graph: Graph,
    width: int,
    height: int,
    k: float = 300.0,
    min_size: int = 20,
) -> tuple[np.ndarray, int]:
    """Segmenta um grafo de pixels e retorna rótulos e quantidade de regiões.

    Primeiro, as arestas são processadas em ordem crescente e duas componentes
    são unidas quando o peso da aresta não excede os limiares internos de ambas.
    Em seguida, componentes menores que ``min_size`` são unidas a componentes
    vizinhas pelas arestas mais leves disponíveis.

    Args:
        graph: grafo ponderado de pixels com IDs entre 0 e width*height-1.
        width: largura da imagem em pixels.
        height: altura da imagem em pixels.
        k: parâmetro de escala não negativo do critério de fusão.
        min_size: menor tamanho desejado para os componentes finais.

    Returns:
        Tupla contendo a matriz de rótulos (height, width), com IDs consecutivos,
        e o número de regiões.

    Raises:
        ValueError: quando dimensões, parâmetros, arestas ou pesos são inválidos.

    Complexidade: O(E log E + V*α(V)) em tempo e O(V + E) em espaço.
    """
    if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
        raise ValueError("width deve ser um inteiro maior que zero")
    if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
        raise ValueError("height deve ser um inteiro maior que zero")
    if isinstance(k, bool) or not isfinite(k) or k < 0:
        raise ValueError("k deve ser um número finito maior ou igual a zero")
    if (
        isinstance(min_size, bool)
        or not isinstance(min_size, int)
        or min_size <= 0
    ):
        raise ValueError("min_size deve ser um inteiro maior que zero")

    num_pixels = width * height
    if graph.num_vertices() != num_pixels:
        raise ValueError(
            "o número de vértices do grafo deve ser igual a width * height"
        )

    edges = list(graph.edges())
    for u, v, weight in edges:
        if not (0 <= u < num_pixels and 0 <= v < num_pixels):
            raise ValueError(f"aresta contém vértice fora do intervalo: ({u}, {v})")
        if not isfinite(weight) or weight < 0:
            raise ValueError("os pesos das arestas devem ser finitos e não negativos")
    edges.sort(key=lambda edge: edge[2])

    components = UnionFind(num_pixels)

    for u, v, weight in edges:
        component_u = components.find(u)
        component_v = components.find(v)
        if component_u == component_v:
            continue

        threshold_u = (
            components.get_internal_weight(component_u)
            + k / components.size(component_u)
        )
        threshold_v = (
            components.get_internal_weight(component_v)
            + k / components.size(component_v)
        )
        if weight <= min(threshold_u, threshold_v):
            root = components.union(component_u, component_v)
            components.set_internal_weight(root, weight)

    for u, v, weight in edges:
        component_u = components.find(u)
        component_v = components.find(v)
        if component_u == component_v:
            continue
        if (
            components.size(component_u) < min_size
            or components.size(component_v) < min_size
        ):
            root = components.union(component_u, component_v)
            components.set_internal_weight(root, weight)

    labels = np.empty((height, width), dtype=np.int32)
    root_to_label: dict[int, int] = {}
    next_label = 0

    for pixel_id in range(num_pixels):
        root = components.find(pixel_id)
        if root not in root_to_label:
            root_to_label[root] = next_label
            next_label += 1
        labels[pixel_id // width, pixel_id % width] = root_to_label[root]

    return labels, next_label
