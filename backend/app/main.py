"""API FastAPI para segmentação hierárquica de imagens."""

from __future__ import annotations

import base64
import math
import time
from io import BytesIO

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from app.imaging.graph_builder import build_pixel_graph
from app.imaging.loader import PRESETS, LoadedImage, load_image
from app.segmentation.felzenszwalb import segment_felzenszwalb
from app.segmentation.hierarchy import HierarchyTree

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
MAX_SIDE = 480
MAX_SIGMA = 10.0
MAX_LEVELS = 16
MAX_ENCODED_LABEL_ID = 65_535
SUPPORTED_IMAGE_FORMATS = {"BMP", "GIF", "JPEG", "PNG", "TIFF", "WEBP"}
SUPPORTED_IMAGE_MIME_TYPES = {
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
}

app = FastAPI(
    title="Segmentação Hierárquica por Grafos",
    description="API para segmentação de imagens em múltiplas granularidades.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _encode_png(image: np.ndarray) -> str:
    """Codifica um array de imagem como PNG em Base64."""
    buffer = BytesIO()
    Image.fromarray(image).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _resolve_max_side(max_side: int | None, preset: str | None) -> int:
    """Valida e resolve o limite de redimensionamento solicitado."""
    if max_side is not None and preset is not None:
        raise HTTPException(
            status_code=422,
            detail="Informe max_side ou preset, não ambos.",
        )

    if preset is not None:
        normalized_preset = preset.strip().lower()
        if normalized_preset not in PRESETS:
            raise HTTPException(
                status_code=422,
                detail=f"Preset inválido. Opções: {', '.join(PRESETS)}.",
            )
        return PRESETS[normalized_preset]

    if max_side is None:
        return PRESETS["medio"]
    if not 1 <= max_side <= MAX_SIDE:
        raise HTTPException(
            status_code=422,
            detail=f"max_side deve estar entre 1 e {MAX_SIDE}.",
        )
    return max_side


def _validate_parameters(
    max_side: int | None,
    preset: str | None,
    k: float,
    min_size: int,
    sigma: float,
    connectivity: int,
    num_levels: int,
) -> int:
    """Valida parâmetros numéricos do processamento."""
    resolved_max_side = _resolve_max_side(max_side, preset)
    if not math.isfinite(k) or k < 0:
        raise HTTPException(status_code=422, detail="k deve ser finito e não negativo.")
    if min_size < 1:
        raise HTTPException(status_code=422, detail="min_size deve ser maior que zero.")
    if not math.isfinite(sigma) or not 0 <= sigma <= MAX_SIGMA:
        raise HTTPException(
            status_code=422,
            detail=f"sigma deve estar entre 0 e {MAX_SIGMA}.",
        )
    if connectivity not in (4, 8):
        raise HTTPException(
            status_code=422,
            detail="connectivity deve ser 4 ou 8.",
        )
    if not 1 <= num_levels <= MAX_LEVELS:
        raise HTTPException(
            status_code=422,
            detail=f"num_levels deve estar entre 1 e {MAX_LEVELS}.",
        )
    return resolved_max_side


def _load_uploaded_image(
    content: bytes, content_type: str | None, max_side: int
) -> LoadedImage:
    """Confere o tipo e as dimensões antes de decodificar a imagem."""
    normalized_content_type = (content_type or "").split(";", maxsplit=1)[0].lower()
    if (
        normalized_content_type
        and normalized_content_type != "application/octet-stream"
        and normalized_content_type not in SUPPORTED_IMAGE_MIME_TYPES
    ):
        raise HTTPException(status_code=415, detail="Tipo de arquivo não suportado.")

    try:
        with Image.open(BytesIO(content)) as probe:
            if probe.format not in SUPPORTED_IMAGE_FORMATS:
                raise HTTPException(
                    status_code=415,
                    detail="Formato de imagem não suportado.",
                )
            image_width, image_height = probe.size
            if image_width * image_height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=413,
                    detail=f"A imagem excede o limite de {MAX_IMAGE_PIXELS} pixels.",
                )
            probe.verify()

        return load_image(content, max_side=max_side)
    except HTTPException:
        raise
    except (
        Image.DecompressionBombError,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=f"Não foi possível ler a imagem enviada: {error}",
        ) from error


@app.get("/health")
def health() -> dict[str, str]:
    """Indica que a API está disponível."""
    return {"status": "ok"}


@app.post("/segment")
async def segment(
    image: UploadFile = File(...),
    max_side: int | None = Form(default=None),
    preset: str | None = Form(default=None),
    k: float = Form(default=300.0),
    min_size: int = Form(default=20),
    sigma: float = Form(default=0.8),
    connectivity: int = Form(default=8),
    num_levels: int = Form(default=8),
) -> dict[str, object]:
    """Executa o pipeline e retorna imagens, estatísticas e níveis em Base64."""
    total_start = time.perf_counter()
    resolved_max_side = _validate_parameters(
        max_side,
        preset,
        k,
        min_size,
        sigma,
        connectivity,
        num_levels,
    )

    stage_start = time.perf_counter()
    content = await image.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"O arquivo excede o limite de {MAX_UPLOAD_BYTES} bytes.",
        )
    if not content:
        raise HTTPException(status_code=400, detail="O arquivo enviado está vazio.")

    loaded = _load_uploaded_image(content, image.content_type, resolved_max_side)
    width, height = loaded.resized_size
    if min_size > width * height:
        raise HTTPException(
            status_code=422,
            detail="min_size não pode exceder o número de pixels da imagem processada.",
        )
    resized_png = _encode_png(loaded.image)
    load_ms = (time.perf_counter() - stage_start) * 1000

    stage_start = time.perf_counter()
    graph, graph_width, graph_height = build_pixel_graph(
        loaded.image,
        connectivity=connectivity,
        sigma=sigma,
    )
    build_graph_ms = (time.perf_counter() - stage_start) * 1000

    stage_start = time.perf_counter()
    base_labels, _ = segment_felzenszwalb(
        graph,
        graph_width,
        graph_height,
        k=k,
        min_size=min_size,
    )
    segmentation_ms = (time.perf_counter() - stage_start) * 1000

    stage_start = time.perf_counter()
    hierarchy = HierarchyTree(loaded.image, base_labels)
    hierarchy_levels = hierarchy.build_levels(num_levels)
    response_levels: list[dict[str, object]] = []

    for level_index, level in enumerate(hierarchy_levels):
        if level.num_regions - 1 > MAX_ENCODED_LABEL_ID:
            raise HTTPException(
                status_code=422,
                detail=(
                    "A codificação labels_png suporta até 65.536 regiões por nível."
                ),
            )

        region_colors = np.asarray(
            [
                level.region_graph.regions[region_id].color
                for region_id in range(level.num_regions)
            ],
            dtype=np.float64,
        )
        segmented_image = np.clip(
            np.rint(region_colors[level.labels]), 0, 255
        ).astype(np.uint8)

        encoded_labels = np.empty((*level.labels.shape, 3), dtype=np.uint8)
        encoded_labels[:, :, 0] = level.labels // 256
        encoded_labels[:, :, 1] = level.labels % 256
        encoded_labels[:, :, 2] = 0

        regions = [
            {
                "id": region_id,
                "color": [
                    int(np.clip(np.rint(channel), 0, 255))
                    for channel in level.region_graph.regions[region_id].color
                ],
                "area": level.region_graph.regions[region_id].area,
                "centroid": list(level.region_graph.regions[region_id].centroid),
            }
            for region_id in range(level.num_regions)
        ]
        adjacency = [
            [region_a, region_b, round(weight, 3)]
            for region_a, region_b, weight in level.region_graph.graph.edges()
        ]
        response_levels.append(
            {
                "level": level_index,
                "num_regions": level.num_regions,
                "segmented_png": _encode_png(segmented_image),
                "labels_png": _encode_png(encoded_labels),
                "regions": regions,
                "adjacency": adjacency,
            }
        )

    hierarchy_ms = (time.perf_counter() - stage_start) * 1000
    total_ms = (time.perf_counter() - total_start) * 1000

    return {
        "width": width,
        "height": height,
        "original_size": list(loaded.original_size),
        "resized_png": resized_png,
        "graph_stats": {
            "num_vertices": graph.num_vertices(),
            "num_edges": graph.num_edges(),
            "connectivity": connectivity,
        },
        "timings_ms": {
            "load": round(load_ms, 3),
            "build_graph": round(build_graph_ms, 3),
            "segmentation": round(segmentation_ms, 3),
            "hierarchy": round(hierarchy_ms, 3),
            "total": round(total_ms, 3),
        },
        "levels": response_levels,
    }
