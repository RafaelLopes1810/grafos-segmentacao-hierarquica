"""Construção do grafo de adjacência de regiões (RAG)."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np

from app.core.graph import Graph


@dataclass(frozen=True)
class Region:
    """Atributos da região.

    centroid usa coordenadas (x, y); bbox é inclusiva (xmin, ymin, xmax, ymax).
    """

    id: int
    area: int
    color: tuple[float, float, float]
    centroid: tuple[float, float]
    bbox: tuple[int, int, int, int]


@dataclass(frozen=True)
class RegionGraph:
    """RAG e metadados das regiões representados por seus rótulos."""

    graph: Graph
    regions: dict[int, Region]
    labels: np.ndarray

    @property
    def num_regions(self) -> int:
        """Quantidade de regiões no RAG."""
        return len(self.regions)


def build_region_graph(image: np.ndarray, labels: np.ndarray) -> RegionGraph:
    """Constrói um RAG e calcula estatísticas para cada região.

    Vértices que compartilham uma borda horizontal ou vertical são ligados.
    Os rótulos de entrada podem ser quaisquer inteiros; na saída são
    normalizados para IDs consecutivos a partir de zero.

    Args:
        image: imagem RGB uint8 no formato (altura, largura, 3).
        labels: matriz bidimensional de IDs de região.

    Returns:
        Grafo, metadados por região e matriz de rótulos normalizada.

    Raises:
        ValueError: quando imagem e rótulos não têm formato compatível.

    Complexidade: O(P log P) em tempo e O(P + R + A) em espaço, onde P é o
    número de pixels, R o número de regiões e A o número de adjacências.
    """
    pixels = np.asarray(image)
    source_labels = np.asarray(labels)
    if (
        pixels.ndim != 3
        or pixels.shape[2] != 3
        or pixels.dtype != np.uint8
        or pixels.shape[0] == 0
        or pixels.shape[1] == 0
    ):
        raise ValueError("image deve ser uma matriz RGB uint8 não vazia")
    if (
        source_labels.ndim != 2
        or source_labels.shape[0] == 0
        or source_labels.shape[1] == 0
        or not np.issubdtype(source_labels.dtype, np.integer)
    ):
        raise ValueError("labels deve ser uma matriz bidimensional de inteiros")
    if source_labels.shape != pixels.shape[:2]:
        raise ValueError("image e labels devem ter as mesmas dimensões")

    height, width = source_labels.shape
    unique_labels, inverse = np.unique(source_labels, return_inverse=True)
    normalized_labels = inverse.reshape(height, width).astype(np.int32)
    num_regions = len(unique_labels)
    flat_labels = normalized_labels.ravel()
    pixel_colors = pixels.reshape(-1, 3).astype(np.float64)
    areas = np.bincount(flat_labels, minlength=num_regions)

    mean_colors = np.column_stack(
        [
            np.bincount(
                flat_labels,
                weights=pixel_colors[:, channel],
                minlength=num_regions,
            )
            / areas
            for channel in range(3)
        ]
    )

    x_coordinates = np.tile(np.arange(width, dtype=np.intp), height)
    y_coordinates = np.repeat(np.arange(height, dtype=np.intp), width)
    x_sums = np.bincount(
        flat_labels, weights=x_coordinates, minlength=num_regions
    )
    y_sums = np.bincount(
        flat_labels, weights=y_coordinates, minlength=num_regions
    )
    min_x = np.full(num_regions, width, dtype=np.intp)
    min_y = np.full(num_regions, height, dtype=np.intp)
    max_x = np.full(num_regions, -1, dtype=np.intp)
    max_y = np.full(num_regions, -1, dtype=np.intp)
    np.minimum.at(min_x, flat_labels, x_coordinates)
    np.minimum.at(min_y, flat_labels, y_coordinates)
    np.maximum.at(max_x, flat_labels, x_coordinates)
    np.maximum.at(max_y, flat_labels, y_coordinates)

    regions: dict[int, Region] = {}
    for region_id in range(num_regions):
        area = int(areas[region_id])
        regions[region_id] = Region(
            id=region_id,
            area=area,
            color=tuple(float(value) for value in mean_colors[region_id]),
            centroid=(
                float(x_sums[region_id] / area),
                float(y_sums[region_id] / area),
            ),
            bbox=(
                int(min_x[region_id]),
                int(min_y[region_id]),
                int(max_x[region_id]),
                int(max_y[region_id]),
            ),
        )

    boundary_pairs: list[np.ndarray] = []
    for first, second in (
        (normalized_labels[:, :-1], normalized_labels[:, 1:]),
        (normalized_labels[:-1, :], normalized_labels[1:, :]),
    ):
        different = first != second
        if np.any(different):
            left = first[different]
            right = second[different]
            boundary_pairs.append(
                np.column_stack((np.minimum(left, right), np.maximum(left, right)))
            )

    graph = Graph(num_regions)
    if boundary_pairs:
        unique_pairs = np.unique(np.concatenate(boundary_pairs, axis=0), axis=0)
        for region_a, region_b in unique_pairs:
            color_difference = mean_colors[region_a] - mean_colors[region_b]
            weight = sqrt(float(np.dot(color_difference, color_difference)))
            graph.add_edge(int(region_a), int(region_b), weight)

    return RegionGraph(graph=graph, regions=regions, labels=normalized_labels)
