from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter, ImageMorph

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "img" / "library"
ASSETS = Path(r"C:\Users\Andre\.cursor\projects\c-Users-Andre-OneDrive-Desktop\assets")

FILES = {
    "book-journal-chroma.png": "book-journal.png",
    "book-items-chroma.png": "book-items.png",
    "book-craft-chroma.png": "book-craft.png",
    "book-prices-chroma.png": "book-prices.png",
}


def is_chroma(r: int, g: int, b: int) -> bool:
    return g >= 70 and g > r + 18 and g > b + 18 and (g - max(r, b)) >= 15


def is_soft_chroma(r: int, g: int, b: int) -> bool:
    return g >= 45 and g > r + 8 and g > b + 8 and g >= (r + b) * 0.55


def chroma_key(img: Image.Image) -> Image.Image:
    src = img.convert("RGBA")
    w, h = src.size
    px = src.load()

    alpha = Image.new("L", (w, h), 255)
    ap = alpha.load()
    rgb = src.convert("RGB")
    rp = rgb.load()

    for y in range(h):
        for x in range(w):
            r, g, b = rp[x, y]
            if is_chroma(r, g, b):
                ap[x, y] = 0
            elif is_soft_chroma(r, g, b):
                # partial: stronger green → more transparent
                dominance = min(1.0, (g - max(r, b)) / 80)
                ap[x, y] = int(255 * (1.0 - 0.85 * dominance - 0.15))
            else:
                ap[x, y] = 255

    # kill residual green pixels that sit next to already-clear pixels
    for _ in range(2):
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if ap[x, y] == 0:
                    continue
                r, g, b = rp[x, y]
                if not (g > r + 5 and g > b + 5):
                    continue
                near_clear = any(ap[x + dx, y + dy] == 0 for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                if near_clear and is_soft_chroma(r, g, b):
                    ap[x, y] = 0

    # despill remaining edge greens into neutral
    for y in range(h):
        for x in range(w):
            a = ap[x, y]
            if a == 0:
                continue
            r, g, b = rp[x, y]
            if g > r + 6 and g > b + 6:
                ng = min(g, max(r, b) + 4)
                # also pull toward average of R/B
                ng = (ng + (r + b) // 2) // 2
                rp[x, y] = (r, ng, b)

    # clean 1px jagged matte
    alpha = alpha.filter(ImageFilter.MinFilter(3))  # erode
    alpha = alpha.filter(ImageFilter.MaxFilter(3))  # dilate back
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.7))
    ap = alpha.load()
    for y in range(h):
        for x in range(w):
            v = ap[x, y]
            if v < 35:
                ap[x, y] = 0
            elif v > 225:
                ap[x, y] = 255

    out = Image.new("RGBA", (w, h))
    out.paste(rgb, (0, 0))
    out.putalpha(alpha)

    bbox = alpha.getbbox()
    if bbox:
        pad = 8
        l, t, r, b = bbox
        out = out.crop((max(0, l - pad), max(0, t - pad), min(w, r + pad), min(h, b + pad)))
    return out


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for src_name, dest_name in FILES.items():
        out = chroma_key(Image.open(ASSETS / src_name))
        dest = DEST / dest_name
        out.save(dest, "PNG")
        a = out.getchannel("A")
        # count leftover greenish opaque pixels
        px = out.load()
        greenish = 0
        for y in range(out.height):
            for x in range(out.width):
                r, g, b, al = px[x, y]
                if al > 40 and g > r + 20 and g > b + 20:
                    greenish += 1
        print(f"{dest_name}: {out.size} greenish={greenish} cornerA={px[0,0][3]}")


if __name__ == "__main__":
    main()
