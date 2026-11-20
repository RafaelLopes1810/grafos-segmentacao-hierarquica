"""Valida fronteiras e contratos sem abrir portas de rede."""
import numpy as np
import pytest
from .test_api import _request, _encoded_test_image, _decode_png
import app.main as api_module


@pytest.mark.parametrize("name,value", [
    ("k", "-1"), ("k", "nan"), ("k", "inf"),
    ("sigma", "-0.1"), ("sigma", "10.1"), ("sigma", "nan"), ("sigma", "inf"),
    ("min_size", "0"), ("min_size", "17"),
    ("num_levels", "0"), ("num_levels", "17"),
    ("max_side", "0"), ("max_side", "481"),
    ("connectivity", "0"), ("color_space", "hsv"), ("preset", "desconhecido"),
])
def test_invalid_numeric_and_enum_boundaries(name, value):
    response = _request("POST", "/segment",
        files={"image": ("test.png", _encoded_test_image(), "image/png")},
        data={"min_size": "1", name: value})
    assert response.status_code == 422
    assert response.json()["detail"]


@pytest.mark.parametrize("content,status", [(b"", 400), (b"not a PNG", 400)])
def test_empty_and_corrupted_upload(content, status):
    response = _request("POST", "/segment",
        files={"image": ("test.png", content, "image/png")})
    assert response.status_code == status


def test_missing_upload():
    assert _request("POST", "/segment").status_code == 422


def test_pixel_budget(monkeypatch):
    monkeypatch.setattr(api_module, "MAX_IMAGE_PIXELS", 15)
    response = _request("POST", "/segment",
        files={"image": ("test.png", _encoded_test_image(), "image/png")},
        data={"min_size": "1"})
    assert response.status_code == 413


@pytest.mark.parametrize("connectivity", [4, 8])
@pytest.mark.parametrize("color_space", ["rgb", "lab"])
def test_returned_partitions_mse_areas_and_adjacencies(connectivity, color_space):
    response = _request("POST", "/segment",
        files={"image": ("test.png", _encoded_test_image(), "application/octet-stream")},
        data={"min_size": "1", "k": "0", "sigma": "0", "num_levels": "16",
              "connectivity": str(connectivity), "color_space": color_space})
    assert response.status_code == 200, response.text
    payload = response.json()
    previous_labels = None
    previous_mse = -1
    for level in payload["levels"]:
        rgb = _decode_png(level["labels_png"]).astype(np.int64)
        labels = rgb[:, :, 0] * 256 + rgb[:, :, 1]
        ids, areas = np.unique(labels, return_counts=True)
        assert len(ids) == level["num_regions"]
        assert dict(zip(ids, areas)) == {r["id"]: r["area"] for r in level["regions"]}
        assert sum(r["area"] for r in level["regions"]) == payload["width"] * payload["height"]
        assert level["homogeneidade_mse"] >= previous_mse - 1e-8
        for a, b, weight in level["adjacency"]:
            assert a in ids and b in ids and a != b
            assert weight >= 0 and np.isfinite(weight)
        if previous_labels is not None:
            for region in np.unique(previous_labels):
                assert np.unique(labels[previous_labels == region]).size == 1
        previous_labels, previous_mse = labels, level["homogeneidade_mse"]
    assert all(np.isfinite(t) and t >= 0 for t in payload["timings_ms"].values())


def test_single_pixel_boundary():
    response = _request("POST", "/segment",
        files={"image": ("test.png", _encoded_test_image(), "image/png")},
        data={"max_side": "1", "min_size": "1", "num_levels": "16", "sigma": "0"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["width"] == data["height"] == 1
    assert len(data["levels"]) == 1
    assert data["levels"][0]["num_regions"] == 1
    assert data["levels"][0]["homogeneidade_mse"] == 0
    assert data["levels"][0]["adjacency"] == []
