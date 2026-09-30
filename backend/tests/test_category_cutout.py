"""Verify /api/category-media/{id}?cutout=true returns a 320x320 PNG with
tight-cropped, transparent-background object (alpha bbox height >= 60%)."""
import io
import os

import pytest
import requests
from PIL import Image

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")


@pytest.fixture(scope="module")
def cutout_bytes():
    r = requests.get(f"{BASE_URL}/api/category-media/corpo-umano", params={"cutout": "true"}, timeout=60)
    assert r.status_code == 200, r.text[:400]
    assert r.headers.get("content-type", "").startswith("image/png"), r.headers
    return r.content


def test_cutout_is_320_png(cutout_bytes):
    img = Image.open(io.BytesIO(cutout_bytes))
    assert img.format == "PNG"
    assert img.mode == "RGBA"
    assert img.size == (320, 320), img.size


def test_cutout_corners_transparent(cutout_bytes):
    img = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")
    px = img.load()
    # All 4 corners should be fully transparent (alpha == 0).
    for x, y in [(0, 0), (319, 0), (0, 319), (319, 319)]:
        assert px[x, y][3] == 0, f"corner {(x, y)} alpha={px[x, y][3]}"


def test_cutout_alpha_bbox_fills_canvas(cutout_bytes):
    """Alpha bbox height must be >= 60% of the 320px canvas."""
    img = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")
    alpha = img.split()[-1]
    bbox = alpha.getbbox()
    assert bbox is not None, "empty alpha channel"
    x0, y0, x1, y1 = bbox
    h = y1 - y0
    w = x1 - x0
    assert h >= 0.60 * 320, f"alpha bbox too short: h={h} (<{0.60 * 320})"
    # Sanity: object roughly square-ish (helps confirm tight crop).
    assert w >= 0.50 * 320, f"alpha bbox too narrow: w={w}"


def test_multiple_categories_cutout():
    """Spot-check a couple more categories to ensure the crop is stable."""
    for cid in ["natura", "mondo-animale"]:
        r = requests.get(f"{BASE_URL}/api/category-media/{cid}", params={"cutout": "true"}, timeout=60)
        if r.status_code == 404:
            pytest.skip(f"{cid} has no media configured")
        assert r.status_code == 200, f"{cid} -> {r.status_code}"
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        assert img.size == (320, 320)
        bbox = img.split()[-1].getbbox()
        assert bbox is not None
        assert (bbox[3] - bbox[1]) >= 0.60 * 320, f"{cid} alpha bbox short"
