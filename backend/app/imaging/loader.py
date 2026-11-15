"""Leitura, redimensionamento e preparação de imagens e máscaras."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Union

import numpy as np
from PIL import Image, ImageOps


class ImagePreset(IntEnum):
    """Tamanhos máximos predefinidos para o maior lado da imagem."""

    PEQUENO = 160
    MEDIO = 320
    GRANDE = 480


PEQUENO = ImagePreset.PEQUENO
MEDIO = ImagePreset.MEDIO
GRANDE = ImagePreset.GRANDE
PRESETS = {preset.name.lower(): preset.value for preset in ImagePreset}


@dataclass(frozen=True)
class LoadedImage:
    """Imagem RGB carregada e dimensões antes/depois do redimensionamento.

    As dimensões são armazenadas no formato (largura, altura).
    """

    image: np.ndarray
    original_size: tuple[int, int]
    resized_size: tuple[int, int]


ImageSource = Union[str, Path, bytes, BinaryIO]
MaxSide = Union[int, ImagePreset, str]


def _resolve_max_side(max_side: MaxSide) -> int:
    """Converte preset ou inteiro em limite de dimensão validado."""
    if isinstance(max_side, str):
        preset = max_side.strip().lower()
        if preset not in PRESETS:
            raise ValueError(
                f"Preset inválido: {max_side!r}. Opções: {', '.join(PRESETS)}"
            )
        return PRESETS[preset]

    if isinstance(max_side, bool) or not isinstance(max_side, int):
        raise TypeError("max_side deve ser um inteiro ou um preset conhecido")
    if max_side <= 0:
        raise ValueError("max_side deve ser maior que zero")
    return max_side


def load_image(
    source: ImageSource,
    max_side: MaxSide = ImagePreset.MEDIO,
    save_to: Union[str, Path, None] = None,
) -> LoadedImage:
    """Carrega uma imagem RGB e limita o maior lado sem ampliá-la.

    Fontes aceitas: caminho, bytes ou arquivo binário aberto. A redução usa
    Lanczos e aplica a orientação EXIF antes de registrar as dimensões.

    Args:
        source: caminho, conteúdo binário ou objeto de arquivo da imagem.
        max_side: tamanho máximo do maior lado, em pixels, ou preset nomeado.
        save_to: caminho opcional para salvar a imagem RGB já processada.

    Returns:
        Imagem uint8 no formato (altura, largura, 3), dimensões originais e
        dimensões finais, ambas no formato (largura, altura).

    Complexidade: O(W*H) em tempo e espaço, para decodificar e redimensionar.
    """
    limit = _resolve_max_side(max_side)
    image_source = BytesIO(source) if isinstance(source, bytes) else source

    with Image.open(image_source) as opened:
        rgb_image = ImageOps.exif_transpose(opened).convert("RGB")
        original_size = rgb_image.size
        width, height = original_size
        scale = min(1.0, limit / max(width, height))
        resized_size = (
            max(1, round(width * scale)),
            max(1, round(height * scale)),
        )

        if resized_size != original_size:
            rgb_image = rgb_image.resize(resized_size, Image.Resampling.LANCZOS)

        if save_to is not None:
            output_path = Path(save_to)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            rgb_image.save(output_path)

        image_array = np.asarray(rgb_image, dtype=np.uint8).copy()

    return LoadedImage(
        image=image_array,
        original_size=original_size,
        resized_size=resized_size,
    )


def resize_label_mask(
    mask: np.ndarray, output_size: tuple[int, int]
) -> np.ndarray:
    """Redimensiona uma máscara categórica por vizinho mais próximo.

    Args:
        mask: matriz bidimensional de IDs/rótulos.
        output_size: dimensões de saída no formato (largura, altura).

    Returns:
        Máscara redimensionada, preservando o dtype e os valores dos rótulos.

    Complexidade: O(W*H) em tempo e espaço para a matriz de saída.
    """
    labels = np.asarray(mask)
    if labels.ndim != 2 or labels.shape[0] == 0 or labels.shape[1] == 0:
        raise ValueError("mask deve ser uma matriz bidimensional não vazia")

    output_width, output_height = output_size
    if output_width <= 0 or output_height <= 0:
        raise ValueError("as dimensões de saída devem ser maiores que zero")

    input_height, input_width = labels.shape
    source_x = np.minimum(
        ((np.arange(output_width) + 0.5) * input_width / output_width).astype(
            np.intp
        ),
        input_width - 1,
    )
    source_y = np.minimum(
        ((np.arange(output_height) + 0.5) * input_height / output_height).astype(
            np.intp
        ),
        input_height - 1,
    )
    return labels[source_y[:, None], source_x[None, :]].copy()
