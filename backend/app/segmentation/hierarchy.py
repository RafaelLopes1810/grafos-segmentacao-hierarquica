"""Fusões aglomerativas de regiões e cortes de dendrograma."""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from math import isfinite, sqrt

import numpy as np

from app.core.union_find import UnionFind
from app.segmentation.region_graph import (
    Region,
    RegionGraph,
    build_region_graph,
)


@dataclass
class HierarchyNode:
    """Nó folha ou fusão do dendrograma."""

    node_id: int
    parent: int | None = None
    children: tuple[int, int] | None = None
    weight: float = 0.0
    height: float = 0.0
    num_regions_remaining: int = 0


@dataclass(frozen=True)
class HierarchyLevel:
    """Partição extraída da hierarquia e seu grafo de regiões."""

    level: int | None
    labels: np.ndarray
    num_regions: int
    region_graph: RegionGraph

    @property
    def rag(self) -> RegionGraph:
        """Alias curto para o grafo de regiões deste nível."""
        return self.region_graph


def _color_distance(color_a: tuple[float, float, float],
                    color_b: tuple[float, float, float]) -> float:
    """Distância euclidiana entre duas cores RGB médias."""
    return sqrt(sum((a - b) ** 2 for a, b in zip(color_a, color_b)))


def _merge_regions(region_a: Region, region_b: Region, new_id: int) -> Region:
    """Combina atributos de duas regiões com médias ponderadas pela área."""
    area = region_a.area + region_b.area
    color = tuple(
        (
            region_a.color[channel] * region_a.area
            + region_b.color[channel] * region_b.area
        )
        / area
        for channel in range(3)
    )
    centroid = (
        (
            region_a.centroid[0] * region_a.area
            + region_b.centroid[0] * region_b.area
        )
        / area,
        (
            region_a.centroid[1] * region_a.area
            + region_b.centroid[1] * region_b.area
        )
        / area,
    )
    bbox = (
        min(region_a.bbox[0], region_b.bbox[0]),
        min(region_a.bbox[1], region_b.bbox[1]),
        max(region_a.bbox[2], region_b.bbox[2]),
        max(region_a.bbox[3], region_b.bbox[3]),
    )
    return Region(
        id=new_id,
        area=area,
        color=color,
        centroid=centroid,
        bbox=bbox,
    )


class HierarchyTree:
    """Constrói um dendrograma completo a partir do RAG de uma partição base.

    As entradas do heap armazenam peso, IDs e versões das regiões. Entradas
    antigas são descartadas quando uma região já foi consumida por uma fusão.
    A altura do dendrograma é monotônica: registra o maior valor entre o peso
    da aresta usada e as alturas dos filhos, permitindo cortes por limiar válidos
    mesmo quando a distância média recalculada diminui após uma fusão.

    Complexidade: O(E log E) para as E entradas inseridas no heap (incluindo
    atualizações preguiçosas); espaço O(R + A + E), com R regiões e A adjacências.
    """

    def __init__(self, image: np.ndarray, initial_labels: np.ndarray):
        """Constrói o RAG inicial e realiza as fusões até restar uma região.

        Args:
            image: imagem RGB uint8 da partição base.
            initial_labels: rótulos do nível mais fino, como matriz 2D.
        """
        self.image = np.asarray(image).copy()
        self.initial_region_graph = build_region_graph(self.image, initial_labels)
        self.initial_labels = self.initial_region_graph.labels.copy()
        initial_regions = self.initial_region_graph.regions
        initial_count = len(initial_regions)

        self.nodes: dict[int, HierarchyNode] = {
            region_id: HierarchyNode(
                node_id=region_id,
                num_regions_remaining=initial_count,
            )
            for region_id in initial_regions
        }
        self.merges: list[HierarchyNode] = []

        active_regions = dict(initial_regions)
        adjacency: dict[int, dict[int, float]] = {
            region_id: {} for region_id in initial_regions
        }
        versions = {region_id: 0 for region_id in initial_regions}
        heap: list[tuple[float, int, int, int, int]] = []

        for region_a, region_b, weight in self.initial_region_graph.graph.edges():
            adjacency[region_a][region_b] = weight
            adjacency[region_b][region_a] = weight
            self._push_edge(heap, region_a, region_b, weight, versions)

        next_node_id = initial_count
        while len(active_regions) > 1:
            if not heap:
                raise ValueError("o grafo de regiões precisa ser conexo")

            weight, region_a, region_b, version_a, version_b = heapq.heappop(heap)
            if (
                region_a not in active_regions
                or region_b not in active_regions
                or versions[region_a] != version_a
                or versions[region_b] != version_b
                or adjacency[region_a].get(region_b) != weight
            ):
                continue

            merged_region = _merge_regions(
                active_regions[region_a],
                active_regions[region_b],
                next_node_id,
            )
            neighbors = (set(adjacency[region_a]) | set(adjacency[region_b])) - {
                region_a,
                region_b,
            }

            del active_regions[region_a]
            del active_regions[region_b]
            active_regions[next_node_id] = merged_region

            for neighbor in neighbors:
                adjacency[neighbor].pop(region_a, None)
                adjacency[neighbor].pop(region_b, None)
            adjacency.pop(region_a)
            adjacency.pop(region_b)
            adjacency[next_node_id] = {}

            height = max(
                weight,
                self.nodes[region_a].height,
                self.nodes[region_b].height,
            )
            merged_node = HierarchyNode(
                node_id=next_node_id,
                children=(region_a, region_b),
                weight=weight,
                height=height,
                num_regions_remaining=len(active_regions),
            )
            self.nodes[region_a].parent = next_node_id
            self.nodes[region_b].parent = next_node_id
            self.nodes[next_node_id] = merged_node
            self.merges.append(merged_node)

            versions[region_a] += 1
            versions[region_b] += 1
            versions[next_node_id] = 0

            for neighbor in neighbors:
                new_weight = _color_distance(
                    merged_region.color, active_regions[neighbor].color
                )
                adjacency[next_node_id][neighbor] = new_weight
                adjacency[neighbor][next_node_id] = new_weight
                self._push_edge(heap, next_node_id, neighbor, new_weight, versions)

            next_node_id += 1

        self.root_id = next(iter(active_regions))
        self.num_initial_regions = initial_count

    @staticmethod
    def _push_edge(
        heap: list[tuple[float, int, int, int, int]],
        region_a: int,
        region_b: int,
        weight: float,
        versions: dict[int, int],
    ) -> None:
        """Insere uma aresta no heap com IDs em ordem determinística."""
        if region_a > region_b:
            region_a, region_b = region_b, region_a
        heapq.heappush(
            heap,
            (
                weight,
                region_a,
                region_b,
                versions[region_a],
                versions[region_b],
            ),
        )

    def _create_level(
        self, merge_nodes: list[HierarchyNode], level: int | None = None
    ) -> HierarchyLevel:
        """Aplica fusões selecionadas às folhas e gera labels e RAG."""
        components = UnionFind(self.num_initial_regions)
        representatives = {
            region_id: region_id for region_id in range(self.num_initial_regions)
        }

        for node in merge_nodes:
            if node.children is None:
                continue
            child_a, child_b = node.children
            root = components.union(
                representatives[child_a],
                representatives[child_b],
            )
            representatives[node.node_id] = root

        leaf_roots = np.fromiter(
            (components.find(region_id) for region_id in range(self.num_initial_regions)),
            dtype=np.int64,
            count=self.num_initial_regions,
        )
        pixel_roots = leaf_roots[self.initial_labels]
        _, consecutive_labels = np.unique(pixel_roots, return_inverse=True)
        labels = consecutive_labels.reshape(self.initial_labels.shape).astype(np.int32)
        rag = build_region_graph(self.image, labels)
        return HierarchyLevel(
            level=level,
            labels=labels,
            num_regions=rag.num_regions,
            region_graph=rag,
        )

    def cut_by_num_regions(self, num_regions: int) -> HierarchyLevel:
        """Extrai a partição após fusões suficientes para obter n regiões.

        Complexidade: O(V*α(V) + P log P), incluindo a reconstrução do RAG.
        """
        if (
            isinstance(num_regions, bool)
            or not isinstance(num_regions, int)
            or not 1 <= num_regions <= self.num_initial_regions
        ):
            raise ValueError(
                f"num_regions deve estar entre 1 e {self.num_initial_regions}"
            )

        merges_to_apply = self.num_initial_regions - num_regions
        return self._create_level(self.merges[:merges_to_apply])

    def cut_by_threshold(self, threshold: float) -> HierarchyLevel:
        """Extrai a partição formada por fusões com altura até threshold.

        Complexidade: O(V*α(V) + P log P), incluindo a reconstrução do RAG.
        """
        if isinstance(threshold, bool) or not isfinite(threshold) or threshold < 0:
            raise ValueError("threshold deve ser finito e maior ou igual a zero")

        selected_merges = [
            node for node in self.merges if node.height <= threshold
        ]
        return self._create_level(selected_merges)

    def build_levels(self, num_levels: int) -> list[HierarchyLevel]:
        """Gera até num_levels partições aninhadas em contagens geométricas.

        O nível inicial é o mais fino e o final usa no mínimo duas regiões
        (ou uma, se a partição inicial já tiver apenas uma). Contagens repetidas
        são omitidas quando existem menos regiões que níveis solicitados.

        Complexidade: O(L*(V*α(V) + P log P)), sendo L o número de níveis gerados.
        """
        if (
            isinstance(num_levels, bool)
            or not isinstance(num_levels, int)
            or num_levels <= 0
        ):
            raise ValueError("num_levels deve ser um inteiro maior que zero")

        minimum = min(2, self.num_initial_regions)
        counts = [self.num_initial_regions]
        if num_levels > 1 and counts[0] > minimum:
            for index in range(1, num_levels):
                fraction = index / (num_levels - 1)
                count = round(
                    self.num_initial_regions
                    * (minimum / self.num_initial_regions) ** fraction
                )
                count = max(minimum, min(self.num_initial_regions, count))
                if count < counts[-1]:
                    counts.append(count)
            if counts[-1] != minimum:
                counts.append(minimum)

        return [
            self._create_level(
                self.merges[: self.num_initial_regions - count],
                level=level_index,
            )
            for level_index, count in enumerate(counts)
        ]
