"""Métricas de qualidade de partições de rótulos implementadas com NumPy."""

from __future__ import annotations

import numpy as np


def contingency_matrix(
    labels_true: np.ndarray, labels_pred: np.ndarray
) -> np.ndarray:
    """Cria a matriz de contingência entre duas partições.

    Linhas correspondem a rótulos de referência e colunas aos rótulos previstos.

    Args:
        labels_true: matriz bidimensional da partição de referência.
        labels_pred: matriz bidimensional da partição avaliada.

    Raises:
        ValueError: quando as matrizes são vazias, não são 2D ou têm formas
            diferentes.

    Complexidade: O(P log P + R*C) em tempo e espaço, sendo P o número de
    pixels, R os rótulos de referência e C os rótulos previstos.
    """
    true = np.asarray(labels_true)
    predicted = np.asarray(labels_pred)
    if true.ndim != 2 or predicted.ndim != 2:
        raise ValueError("as matrizes de rótulos devem ser bidimensionais")
    if true.size == 0 or predicted.size == 0:
        raise ValueError("as matrizes de rótulos não podem ser vazias")
    if true.shape != predicted.shape:
        raise ValueError("as matrizes de rótulos devem ter as mesmas dimensões")

    _, true_inverse = np.unique(true.ravel(), return_inverse=True)
    _, predicted_inverse = np.unique(predicted.ravel(), return_inverse=True)
    num_true = int(true_inverse.max()) + 1
    num_predicted = int(predicted_inverse.max()) + 1
    encoded_pairs = true_inverse * num_predicted + predicted_inverse
    return np.bincount(
        encoded_pairs,
        minlength=num_true * num_predicted,
    ).reshape(num_true, num_predicted)


def variation_of_information(
    labels_true: np.ndarray, labels_pred: np.ndarray
) -> float:
    """Calcula a Variation of Information (VI) em bits entre partições.

    A métrica é H(A|B) + H(B|A), portanto valores menores indicam partições
    mais semelhantes e partições idênticas têm VI igual a zero.

    Complexidade: O(P log P + R*C) em tempo e espaço pela matriz de contingência.
    """
    counts = contingency_matrix(labels_true, labels_pred).astype(np.float64)
    probabilities = counts / counts.sum()
    true_probabilities = probabilities.sum(axis=1)
    predicted_probabilities = probabilities.sum(axis=0)

    true_entropy = -np.sum(
        true_probabilities[true_probabilities > 0]
        * np.log2(true_probabilities[true_probabilities > 0])
    )
    predicted_entropy = -np.sum(
        predicted_probabilities[predicted_probabilities > 0]
        * np.log2(predicted_probabilities[predicted_probabilities > 0])
    )

    independent_probabilities = (
        true_probabilities[:, None] * predicted_probabilities[None, :]
    )
    nonzero = probabilities > 0
    mutual_information = np.sum(
        probabilities[nonzero]
        * np.log2(probabilities[nonzero] / independent_probabilities[nonzero])
    )
    return max(0.0, float(true_entropy + predicted_entropy - 2 * mutual_information))


def rand_index(labels_true: np.ndarray, labels_pred: np.ndarray) -> float:
    """Calcula o Rand Index, proporção de pares classificados corretamente.

    O índice varia de zero a um; valor um indica partições idênticas,
    independentemente dos IDs usados para nomear as regiões.

    Complexidade: O(P log P + R*C) em tempo e espaço pela matriz de contingência.
    """
    counts = contingency_matrix(labels_true, labels_pred).astype(np.int64)
    num_pixels = int(counts.sum())
    total_pairs = num_pixels * (num_pixels - 1) // 2
    if total_pairs == 0:
        return 1.0

    true_pairs = int(np.sum(counts.sum(axis=1) * (counts.sum(axis=1) - 1) // 2))
    predicted_pairs = int(
        np.sum(counts.sum(axis=0) * (counts.sum(axis=0) - 1) // 2)
    )
    same_cluster_pairs = int(np.sum(counts * (counts - 1) // 2))
    different_cluster_pairs = (
        total_pairs - true_pairs - predicted_pairs + same_cluster_pairs
    )
    return float((same_cluster_pairs + different_cluster_pairs) / total_pairs)
