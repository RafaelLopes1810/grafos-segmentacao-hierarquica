"""Estrutura Union-Find com compressão de caminho e união por rank/tamanho.

A estrutura mantém as componentes e também um peso interno auxiliar usado em
algoritmos de segmentação baseados em grafos, como Felzenszwalb-Huttenlocher.
"""

from __future__ import annotations

from typing import Iterable, List


class UnionFind:
    """Implementa a estrutura disjunta com compressão de caminho.

    Complexidade de tempo/espaço:
        - find: O(α(n)) amortizado com compressão.
        - union: O(α(n)) amortizado.
        - espaço: O(n).
    """

    def __init__(self, n: int):
        """Inicializa n elementos, cada um em sua própria componente."""
        if n < 0:
            raise ValueError("n deve ser maior ou igual a zero")

        self.parent: List[int] = list(range(n))
        self.rank: List[int] = [0] * n
        self._size: List[int] = [1] * n
        self.component_count = n
        self.internal_weight: List[float] = [0.0] * n

    def find(self, x: int) -> int:
        """Retorna a raiz da árvore que contém x, com compressão iterativa."""
        if not 0 <= x < len(self.parent):
            raise IndexError(f"Índice {x} fora do intervalo válido: [0, {len(self.parent)})")

        root = x
        while self.parent[root] != root:
            root = self.parent[root]

        while x != root:
            parent = self.parent[x]
            self.parent[x] = root
            x = parent

        return root

    def union(self, x: int, y: int) -> int:
        """Une as componentes de x e y e retorna a raiz da nova componente."""
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return root_x

        if self.rank[root_x] < self.rank[root_y]:
            root_x, root_y = root_y, root_x

        self.parent[root_y] = root_x
        self._size[root_x] += self._size[root_y]
        self.internal_weight[root_x] = max(
            self.internal_weight[root_x], self.internal_weight[root_y]
        )

        if self.rank[root_x] == self.rank[root_y]:
            self.rank[root_x] += 1

        self.component_count -= 1
        return root_x

    def size_of(self, x: int) -> int:
        """Retorna o tamanho da componente de x."""
        return self._size[self.find(x)]

    def size(self, x: int) -> int:
        """Alias para size_of, preservando a convenção do prompt."""
        return self.size_of(x)

    def num_components(self) -> int:
        """Número de componentes atualmente existentes."""
        return self.component_count

    def set_internal_weight(self, x: int, value: float) -> None:
        """Atualiza o peso interno auxiliar da componente de x."""
        root = self.find(x)
        self.internal_weight[root] = max(self.internal_weight[root], float(value))

    def get_internal_weight(self, x: int) -> float:
        """Consulta o maior peso interno da componente de x."""
        return self.internal_weight[self.find(x)]

    def __len__(self) -> int:
        """Tamanho do conjunto de elementos."""
        return len(self.parent)
