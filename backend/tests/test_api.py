
"""Testes de contrato da API FastAPI."""

import base64
import asyncio
from io import BytesIO

import httpx
import numpy as np
import pytest
from PIL import Image

import app.main as api_module


def _request(method: str, url: str, **kwargs) -> httpx.Response:
    """Envia uma requisicao ASGI sem iniciar um servidor externo."""

    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=api_module.app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, url, **kwargs)

    return asyncio.run(send())


def _encoded_test_image() -> bytes:
    """Gera uma imagem PNG pequena com cores distintas."""

    pixels = np.zeros((4, 4, 3), dtype=np.uint8)

    for y in range(4):
        for x in range(4):
            pixels[y, x] = (
                x * 20,
                y * 20,
                (x + y) * 10,
            )

    buffer = BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")

    return buffer.getvalue()


def _decode_png(encoded: str) -> np.ndarray:
    """Decodifica uma imagem PNG recebida em Base64."""

    content = base64.b64decode(
        encoded,
        validate=True,
    )

    with Image.open(BytesIO(content)) as image:
        return np.asarray(image).copy()


def test_health_endpoint_returns_ok():
    """Verifica se a API esta disponivel."""

    response = _request("GET", "/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_local_frontend_origin():
    """Verifica se o frontend local pode acessar a API."""

    response = _request(
        "OPTIONS",
        "/segment",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )


def test_segment_endpoint_returns_images_stats_and_levels():
    """Verifica imagens, estatisticas e niveis retornados pela API."""

    response = _request(
        "POST",
        "/segment",
        files={
            "image": (
                "cores.png",
                _encoded_test_image(),
                "image/png",
            )
        },
        data={
            "max_side": "10",
            "k": "0",
            "min_size": "1",
            "sigma": "0",
            "connectivity": "4",
            "color_space": "rgb",
            "num_levels": "3",
        },
    )

    assert response.status_code == 200, response.text

    result = response.json()

    # Verifica a estrutura principal da resposta.
    assert set(result) == {
        "width",
        "height",
        "original_size",
        "resized_png",
        "graph_stats",
        "timings_ms",
        "levels",
    }

    assert result["width"] == 4
    assert result["height"] == 4
    assert result["original_size"] == [4, 4]

    # Verifica o grafo de pixels.
    assert result["graph_stats"] == {
        "num_vertices": 16,
        "num_edges": 24,
        "connectivity": 4,
    }

    # Verifica os tempos de processamento.
    assert set(result["timings_ms"]) == {
        "load",
        "build_graph",
        "segmentation",
        "hierarchy",
        "total",
    }

    # Verifica a imagem redimensionada.
    resized = _decode_png(result["resized_png"])
    assert resized.shape == (4, 4, 3)

    # Verifica os niveis da hierarquia.
    assert [
        level["num_regions"]
        for level in result["levels"]
    ] == [16, 6, 2]

    first_level = result["levels"][0]

    # Verifica os campos do primeiro nivel.
    # Inclui a nova metrica de homogeneidade.
    assert set(first_level) == {
        "level",
        "num_regions",
        "homogeneidade_mse",
        "segmented_png",
        "labels_png",
        "regions",
        "adjacency",
    }

    # Verifica a metrica MSE.
    assert isinstance(
        first_level["homogeneidade_mse"],
        (int, float),
    )

    assert first_level["homogeneidade_mse"] >= 0

    # Com uma regiao por pixel, o MSE deve ser zero.
    assert first_level["homogeneidade_mse"] == pytest.approx(
        0.0,
        abs=1e-10,
    )

    # Verifica a metrica em todos os niveis.
    for level in result["levels"]:
        assert "homogeneidade_mse" in level
        assert np.isfinite(level["homogeneidade_mse"])
        assert level["homogeneidade_mse"] >= 0

    # Compara imagens segmentadas e rotulos.
    segmented = _decode_png(
        first_level["segmented_png"]
    )

    encoded_labels = _decode_png(
        first_level["labels_png"]
    )

    assert (
        segmented.shape
        == encoded_labels.shape
        == (4, 4, 3)
    )

    # Recupera os identificadores das regioes.
    decoded_ids = (
        encoded_labels[:, :, 0].astype(np.uint32) * 256
    )

    decoded_ids += (
        encoded_labels[:, :, 1].astype(np.uint32)
    )

    assert set(np.unique(decoded_ids)) == set(range(16))

    # Verifica as informacoes das regioes.
    assert first_level["regions"][0].keys() == {
        "id",
        "color",
        "area",
        "centroid",
    }

    # Verifica as arestas do RAG.
    assert all(
        len(edge) == 3
        for edge in first_level["adjacency"]
    )


def test_segment_endpoint_returns_clear_validation_errors():
    """Verifica erros de arquivos e parametros invalidos."""

    unsupported_file = _request(
        "POST",
        "/segment",
        files={
            "image": (
                "arquivo.txt",
                b"texto",
                "text/plain",
            )
        },
    )

    assert unsupported_file.status_code == 415

    invalid_parameter = _request(
        "POST",
        "/segment",
        files={
            "image": (
                "cores.png",
                _encoded_test_image(),
                "image/png",
            )
        },
        data={"connectivity": "6"},
    )

    assert invalid_parameter.status_code == 422

    assert (
        "connectivity"
        in invalid_parameter.json()["detail"]
    )

    conflicting_size = _request(
        "POST",
        "/segment",
        files={
            "image": (
                "cores.png",
                _encoded_test_image(),
                "image/png",
            )
        },
        data={
            "max_side": "100",
            "preset": "medio",
        },
    )

    assert conflicting_size.status_code == 422

    assert (
        "não ambos"
        in conflicting_size.json()["detail"]
    )


def test_segment_endpoint_rejects_uploads_over_size_limit(
    monkeypatch,
):
    """Verifica o limite de tamanho dos arquivos enviados."""

    monkeypatch.setattr(
        api_module,
        "MAX_UPLOAD_BYTES",
        8,
    )

    response = _request(
        "POST",
        "/segment",
        files={
            "image": (
                "cores.png",
                _encoded_test_image(),
                "image/png",
            )
        },
    )

    assert response.status_code == 413

    assert (
        "limite"
        in response.json()["detail"]
    )
