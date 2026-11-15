"""Métricas e ferramentas de avaliação da segmentação."""

from .metrics import contingency_matrix, rand_index, variation_of_information

__all__ = [
    "contingency_matrix",
    "rand_index",
    "variation_of_information",
]
