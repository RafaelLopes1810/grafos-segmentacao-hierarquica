"""Construção vetorizada do grafo de pixels a partir de uma imagem RGB."""

from __future__ import annotations

from math import isfinite

import cv2
import numpy as np

from app.core.graph import Graph


def build_pixel_graph(
    image: np.ndarray,
    connectivity: int = 8,
    sigma: float = 0.8,
) -> tuple[Graph, int, int]:
    """Cria um vértice por pixel e arestas com dissimilaridade de cor.

    Os pesos são distâncias euclidianas entre pixels vizinhos. Os pares de
    vizinhos e seus pesos são calculados em lotes com NumPy; somente a inserção
    na classe Graph é feita iterativamente.

    Args:
        image: imagem RGB uint8 no formato (altura, largura, 3).
        connectivity: conectividade 4 ou 8.
        sigma: desvio padrão da suavização gaussiana; zero desativa a etapa.

    Returns:
        Tupla com o grafo, largura e altura.

    Raises:
        ValueError: quando a imagem ou algum parâmetro não é válido.

    Complexidade: O(V + E) em tempo e espaço, com E <= 4V para conectividade 8.
    """
    pixels = np.asarray(image)
    if (
        pixels.ndim != 3
        or pixels.shape[2] != 3
        or pixels.shape[0] == 0
        or pixels.shape[1] == 0
        or pixels.dtype != np.uint8
    ):
        raise ValueError("image deve ser uma matriz RGB uint8 não vazia")
    if connectivity not in (4, 8):
        raise ValueError("connectivity deve ser 4 ou 8")
    if not isfinite(sigma) or sigma < 0:
        raise ValueError("sigma deve ser um número finito maior ou igual a zero")

    height, width, _ = pixels.shape
    smoothed = pixels
    if sigma > 0:
        smoothed = cv2.GaussianBlur(
            pixels,
            (0, 0),
            sigmaX=float(sigma),
            sigmaY=float(sigma),
            borderType=cv2.BORDER_REFLECT,
        )

    colors = smoothed.astype(np.float32)

    graph = Graph(width * height)
    offsets = [(0, 1), (1, 0)]
    if connectivity == 8:
        offsets.extend([(1, 1), (1, -1)])

    for delta_y, delta_x in offsets:
        y_start = max(0, -delta_y)
        y_end = height - max(0, delta_y)
        x_start = max(0, -delta_x)
        x_end = width - max(0, delta_x)
        if y_start >= y_end or x_start >= x_end:
            continue

        source = colors[y_start:y_end, x_start:x_end]
        target = colors[
            y_start + delta_y : y_end + delta_y,
            x_start + delta_x : x_end + delta_x,
        ]
        differences = target - source
        weights = np.sqrt(np.sum(differences * differences, axis=2))

        rows, columns = np.indices(weights.shape, dtype=np.intp)
        source_ids = (rows + y_start) * width + (columns + x_start)
        target_ids = (
            (rows + y_start + delta_y) * width + columns + x_start + delta_x
        )

        for u, v, weight in zip(
            source_ids.ravel(), target_ids.ravel(), weights.ravel()
        ):
            graph.add_edge(int(u), int(v), float(weight))

    return graph, width, height
