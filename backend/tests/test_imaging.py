"""Testes para carregamento de imagens e construção do grafo de pixels."""

from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from app.imaging.graph_builder import build_pixel_graph
from app.imaging.loader import ImagePreset, load_image, resize_label_mask


def test_load_image_resizes_without_changing_aspect_ratio():
    """O limite deve reduzir a imagem e preservar proporção e formato RGB."""
    source = BytesIO()
    Image.new("RGB", (6, 4), (30, 60, 90)).save(source, format="PNG")

    loaded = load_image(source.getvalue(), max_side=3)

    assert loaded.original_size == (6, 4)
    assert loaded.resized_size == (3, 2)
    assert loaded.image.shape == (2, 3, 3)
    assert loaded.image.dtype == np.uint8
    assert np.all(loaded.image == (30, 60, 90))


def test_load_image_keeps_small_input_and_accepts_preset(tmp_path):
    """Imagens abaixo do preset não devem ser ampliadas."""
    source_path = tmp_path / "small.png"
    Image.new("RGB", (4, 2), (1, 2, 3)).save(source_path)
    processed_path = tmp_path / "processed" / "small.png"

    loaded = load_image(source_path, max_side=ImagePreset.MEDIO, save_to=processed_path)

    assert loaded.original_size == loaded.resized_size == (4, 2)
    assert processed_path.exists()
    assert Image.open(processed_path).size == (4, 2)


def test_load_image_rejects_unknown_preset():
    """Presets desconhecidos devem falhar com uma mensagem clara."""
    with pytest.raises(ValueError, match="Preset inválido"):
        load_image(b"not an image", max_side="extra-grande")


def test_resize_label_mask_preserves_labels_with_nearest_neighbor():
    """Redimensionar rótulos não deve interpolar nem criar IDs intermediários."""
    mask = np.array([[0, 7], [12, 31]], dtype=np.int32)

    resized = resize_label_mask(mask, (4, 4))

    assert resized.dtype == mask.dtype
    assert np.array_equal(
        resized,
        np.array(
            [
                [0, 0, 7, 7],
                [0, 0, 7, 7],
                [12, 12, 31, 31],
                [12, 12, 31, 31],
            ],
            dtype=np.int32,
        ),
    )


@pytest.mark.parametrize(("connectivity", "expected_edges"), [(4, 12), (8, 20)])
def test_build_pixel_graph_has_expected_size_for_3_by_3_image(
    connectivity, expected_edges
):
    """A grade 3x3 deve conter o número esperado de arestas 4/8-conexas."""
    image = np.zeros((3, 3, 3), dtype=np.uint8)
    image[0, 1] = (3, 4, 0)

    graph, width, height = build_pixel_graph(
        image, connectivity=connectivity, sigma=0
    )

    assert (width, height) == (3, 3)
    assert graph.num_vertices() == 9
    assert graph.num_edges() == expected_edges
    assert graph.has_edge(0, 1)
    assert graph.has_edge(0, 3)
    assert graph.has_edge(0, 4) is (connectivity == 8)
    assert dict(((u, v), weight) for u, v, weight in graph.edges())[(0, 1)] == 5.0


def test_build_pixel_graph_supports_lab_and_rejects_bad_parameters():
    """O caminho Lab deve funcionar e parâmetros inválidos devem ser rejeitados."""
    image = np.zeros((2, 2, 3), dtype=np.uint8)
    image[:, 1] = (255, 0, 0)

    graph, _, _ = build_pixel_graph(
        image, connectivity=4, color_space="lab", sigma=0
    )
    assert graph.num_edges() == 4
    assert all(weight >= 0 for _, _, weight in graph.edges())

    with pytest.raises(ValueError, match="connectivity"):
        build_pixel_graph(image, connectivity=6)
