"""Estrutura de grafo ponderado não direcionado implementada do zero.

A classe mantém uma lista de adjacência por vértice e oferece operações
básicas para construir e consultar grafos usados em segmentação de imagens.
"""

from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, Tuple


class Graph:
    """Representa um grafo ponderado não direcionado.

    O grafo usa lista de adjacência e mantém contadores de vértices e arestas.
    A estrutura é adequada para grafos de pixels e de regiões, onde a maioria
    das operações exige acesso rápido aos vizinhos de um dado vértice.

    Complexidade de tempo/espaço:
        - add_edge: O(1) amortizado.
        - neighbors / degree / has_edge: O(1) amortizado para busca na lista.
        - edges: O(V + E) para iterar todas as arestas sem duplicação.
        - espaço: O(V + E).
    """

    def __init__(self, num_vertices: int = 0):
        """Inicializa o grafo com um número opcional de vértices vazios.

        Args:
            num_vertices: quantidade inicial de vértices com IDs 0..num_vertices-1.
        """
        self._adj: Dict[int, List[Tuple[int, float]]] = {}
        for vertex in range(num_vertices):
            self.add_vertex(vertex)

    def add_vertex(self, u: int) -> None:
        """Cria um vértice isolado quando ele ainda não existe."""
        if u not in self._adj:
            self._adj[u] = []

    def add_edge(self, u: int, v: int, w: float) -> None:
        """Adiciona ou atualiza uma aresta não direcionada entre u e v.

        A aresta é armazenada em ambas as listas de adjacência, mas a contagem
        de arestas é mantida como grafo não direcionado.
        """
        self.add_vertex(u)
        self.add_vertex(v)

        if u == v:
            # Grafos de segmentação não usam laços; o método é tolerante e evita
            # duplicação indevida em autovizinhos.
            return

        neighbors_u = self._adj[u]
        neighbors_v = self._adj[v]

        for index, (neighbor, weight) in enumerate(neighbors_u):
            if neighbor == v:
                neighbors_u[index] = (v, float(w))
                break
        else:
            neighbors_u.append((v, float(w)))

        for index, (neighbor, weight) in enumerate(neighbors_v):
            if neighbor == u:
                neighbors_v[index] = (u, float(w))
                break
        else:
            neighbors_v.append((u, float(w)))

    def neighbors(self, u: int) -> List[int]:
        """Retorna a lista de vizinhos de u."""
        self.add_vertex(u)
        return [neighbor for neighbor, _ in self._adj[u]]

    def degree(self, u: int) -> int:
        """Retorna o grau do vértice u."""
        self.add_vertex(u)
        return len(self._adj[u])

    def num_vertices(self) -> int:
        """Quantidade de vértices presentes no grafo."""
        return len(self._adj)

    def num_edges(self) -> int:
        """Número de arestas do grafo, sem duplicação."""
        count = 0
        seen: set[Tuple[int, int]] = set()
        for u in sorted(self._adj):
            for v, _ in self._adj[u]:
                if v < u:
                    continue
                edge = (u, v) if u <= v else (v, u)
                if edge not in seen:
                    seen.add(edge)
                    count += 1
        return count

    def edges(self) -> Iterator[Tuple[int, int, float]]:
        """Itera as arestas do grafo sem duplicar pares não direcionados."""
        seen: set[Tuple[int, int]] = set()
        for u in sorted(self._adj):
            for v, w in self._adj[u]:
                if v < u:
                    continue
                key = (u, v)
                if key not in seen:
                    seen.add(key)
                    yield (u, v, float(w))

    def has_edge(self, u: int, v: int) -> bool:
        """Indica se existe aresta entre u e v."""
        self.add_vertex(u)
        self.add_vertex(v)
        return any(neighbor == v for neighbor, _ in self._adj[u])

    def __len__(self) -> int:
        """Permite usar len(graph) como número de vértices."""
        return self.num_vertices()
