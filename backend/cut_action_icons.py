"""One-off: strip the fake checkerboard background from the generated action
icons (gen_out/*.png), keep the object with soft edges, crop and pad to the
same 512x512 canvas as the existing kind-*.png assets.
Run: python cut_action_icons.py"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = os.path.join(os.path.dirname(__file__), "gen_out")
DST = os.path.join(os.path.dirname(__file__), "..", "frontend", "assets", "images")
CANVAS, PAD = 512, 26
SAT_LO, SAT_HI = 4, 12  # chroma below LO = background (neutral checkerboard ≤ 4), above HI = object

NAMES = {
    "heart-base": "act-heart-base.png",
    "heart-active": "act-heart-active.png",
    "bookmark-base": "act-bookmark-base.png",
    "bookmark-active": "act-bookmark-active.png",
    "share": "act-share.png",
}


def cut(src: str, dst: str):
    im = Image.open(src).convert("RGB")
    px = np.asarray(im).astype(np.int16)
    sat = px.max(axis=2) - px.min(axis=2)
    # Object mask: chroma above HI is solid object; everything else is candidate background.
    solid = (sat >= SAT_HI).astype(np.uint8) * 255
    mask = Image.fromarray(solid, "L").copy()  # writable (fromarray shares the read-only buffer)
    # Flood-fill the background from the four corners (value 128) across the
    # non-solid area: neutral pixels enclosed by the object (specular highlights)
    # are not reached and stay part of it.
    w, h = mask.size
    for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if mask.getpixel(pt) == 0:
            ImageDraw.floodfill(mask, pt, 128, thresh=0)
    reach = np.asarray(mask) == 128
    # Soft alpha on reachable pixels by chroma; unreachable = fully opaque.
    soft = np.clip((sat - SAT_LO) / float(SAT_HI - SAT_LO), 0, 1)
    # Rim lights next to the object are neutral but darker than the pale
    # checkerboard tiles (≥ 215): near the solid object, darkness also counts.
    lum = px.mean(axis=2)
    near = np.asarray(Image.fromarray(solid, "L").filter(ImageFilter.MaxFilter(9))) > 0
    dark = np.clip((212 - lum) / 10.0, 0, 1)
    soft = np.where(near, np.maximum(soft, dark), soft)
    alpha = np.where(reach, soft, 1.0)
    # Keep only the main object: drop detached leftovers (ground shadow, specks).
    comp = Image.fromarray(((alpha > 0.3) * 255).astype(np.uint8), "L").copy()
    label, best, best_area = 1, None, 0
    arr = np.asarray(comp)
    while True:
        seeds = np.argwhere(arr == 255)
        if not len(seeds): break
        y, x = seeds[0]
        ImageDraw.floodfill(comp, (int(x), int(y)), label, thresh=0)
        arr = np.asarray(comp)
        area = int((arr == label).sum())
        if area > best_area: best, best_area = label, area
        label += 1
        if label >= 255: break
    keep = np.asarray(Image.fromarray(((arr == best) * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(5))) > 0
    alpha = np.where(keep, alpha, 0.0)
    alpha8 = (alpha * 255).astype(np.uint8)
    a_img = Image.fromarray(alpha8, "L").filter(ImageFilter.MinFilter(3))  # shave the light fringe
    a_img = a_img.filter(ImageFilter.GaussianBlur(0.6))
    rgba = Image.merge("RGBA", (*im.split(), a_img))
    bbox = a_img.point(lambda v: 255 if v > 20 else 0).getbbox()
    rgba = rgba.crop(bbox)
    # Fit into the shared canvas with the same breathing room as kind-*.png.
    inner = CANVAS - 2 * PAD
    scale = min(inner / rgba.width, inner / rgba.height)
    rgba = rgba.resize((max(1, round(rgba.width * scale)), max(1, round(rgba.height * scale))), Image.LANCZOS)
    out = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    out.paste(rgba, ((CANVAS - rgba.width) // 2, (CANVAS - rgba.height) // 2), rgba)
    out.save(dst, optimize=True)
    print(f"{os.path.basename(src)} -> {dst} bbox={bbox} out={rgba.size}")


if __name__ == "__main__":
    for name, out in NAMES.items():
        cut(os.path.join(SRC, f"{name}.png"), os.path.join(DST, out))
