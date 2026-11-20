
"""Metricas para avaliacao da segmentacao de imagens."""

import numpy as np


def _validar_rotulos(rotulos, nome):
    """Valida uma matriz de rotulos de segmentacao."""
    matriz = np.asarray(rotulos)

    if (
        matriz.ndim != 2
        or matriz.size == 0
        or not np.issubdtype(matriz.dtype, np.integer)
    ):
        raise ValueError(
            f"{nome} deve ser uma matriz 2D nao vazia de inteiros."
        )

    return matriz


def _contingencia(referencia, segmentacao):
    """Calcula contagens e intersecoes entre regioes."""
    ref = _validar_rotulos(referencia, "referencia")
    seg = _validar_rotulos(segmentacao, "segmentacao")

    if ref.shape != seg.shape:
        raise ValueError(
            "As segmentacoes devem ter as mesmas dimensoes."
        )

    # Converte as matrizes em vetores unidimensionais.
    _, ref_ids, ref_counts = np.unique(
        ref.ravel(),
        return_inverse=True,
        return_counts=True
    )

    _, seg_ids, seg_counts = np.unique(
        seg.ravel(),
        return_inverse=True,
        return_counts=True
    )

    # Identifica os pares de regioes correspondentes.
    pares = np.column_stack((ref_ids, seg_ids))

    pares_unicos, contagens = np.unique(
        pares,
        axis=0,
        return_counts=True
    )

    return ref_counts, seg_counts, pares_unicos, contagens


def rand_index(referencia, segmentacao):
    """Calcula o Rand Index entre duas segmentacoes.

    Retorna um valor entre 0 e 1.
    Valor 1 indica concordancia perfeita entre particoes.
    """
    ref_counts, seg_counts, _, joint_counts = _contingencia(
        referencia, segmentacao
    )

    n = int(ref_counts.sum())

    if n < 2:
        return 1.0

    def contar_pares(contagens):
        return sum(
            int(c) * (int(c) - 1) // 2
            for c in contagens
        )

    total_pares = n * (n - 1) // 2

    pares_ref = contar_pares(ref_counts)
    pares_seg = contar_pares(seg_counts)
    pares_ambos = contar_pares(joint_counts)

    pares_diferentes = (
        total_pares - pares_ref - pares_seg + pares_ambos
    )

    resultado = (
        pares_ambos + pares_diferentes
    ) / total_pares

    return float(resultado)


def variation_of_information(referencia, segmentacao):
    """Calcula a Variation of Information (VI), em bits.

    Valor 0 indica particoes identicas.
    Valores maiores indicam maior diferenca de informacao.
    """
    ref_counts, seg_counts, pares, joint_counts = (
        _contingencia(referencia, segmentacao)
    )

    n = float(ref_counts.sum())

    p_ref = ref_counts / n
    p_seg = seg_counts / n
    p_joint = joint_counts / n

    # Entropia de cada segmentacao.
    entropia_ref = -np.sum(
        p_ref * np.log2(p_ref)
    )

    entropia_seg = -np.sum(
        p_seg * np.log2(p_seg)
    )

    # Informacao mutua entre as particoes.
    informacao_mutua = np.sum(
        p_joint * np.log2(
            p_joint / (
                p_ref[pares[:, 0]]
                * p_seg[pares[:, 1]]
            )
        )
    )

    vi = (
        entropia_ref
        + entropia_seg
        - 2 * informacao_mutua
    )

    # Evita resultados negativos por arredondamento.
    return float(max(0.0, vi))


def region_statistics(rotulos):
    """Calcula estatisticas das regioes segmentadas."""
    matriz = _validar_rotulos(rotulos, "rotulos")

    _, contagens = np.unique(
        matriz.ravel(),
        return_counts=True
    )

    return {
        "num_pixels": int(matriz.size),
        "num_regions": int(len(contagens)),
        "min_region_size": int(contagens.min()),
        "max_region_size": int(contagens.max()),
        "mean_region_size": float(contagens.mean()),
        "median_region_size": float(np.median(contagens)),
    }


def color_homogeneity_mse(imagem, rotulos):
    """Calcula o erro quadratico medio das cores por regiao.

    Valores menores indicam maior homogeneidade de cores.
    Nao exige uma segmentacao de referencia.
    """
    matriz = _validar_rotulos(rotulos, "rotulos")
    pixels = np.asarray(imagem)

    if (
        pixels.ndim != 3
        or pixels.shape[2] != 3
        or pixels.shape[:2] != matriz.shape
        or not np.issubdtype(pixels.dtype, np.number)
        or not np.all(np.isfinite(pixels))
    ):
        raise ValueError(
            "A imagem deve ser RGB, numerica, finita "
            "e ter as mesmas dimensoes dos rotulos."
        )

    # Transforma a imagem RGB em uma lista de pixels.
    cores = pixels.reshape(-1, 3).astype(np.float64)

    # Converte rotulos em indices consecutivos.
    _, ids = np.unique(
        matriz.ravel(),
        return_inverse=True
    )

    contagens = np.bincount(ids)

    # Calcula a cor media de cada regiao.
    medias = np.column_stack([
        np.bincount(
            ids,
            weights=cores[:, canal]
        ) / contagens
        for canal in range(3)
    ])

    # Diferenca entre cada pixel e a media da regiao.
    diferencas = cores - medias[ids]

    # Erro quadratico medio.
    return float(np.mean(diferencas ** 2))
