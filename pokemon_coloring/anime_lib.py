"""Conversao de artes (corpo inteiro, fundo transparente) para contorno."""
import os
import urllib.request
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageChops, ImageDraw, ImageFont
from scipy import ndimage

UA = "coloring-book/1.0 (educational)"


def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 2000:
        return path
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r, open(path, "wb") as f:
                f.write(r.read())
            return path
        except Exception:
            if attempt == 3:
                raise
    return path


def despeckle(img, min_area=18):
    arr = np.asarray(img)
    black = arr < 128
    labeled, num = ndimage.label(black)
    if num == 0:
        return img
    sizes = ndimage.sum(np.ones_like(labeled), labeled, range(1, num + 1))
    remove = np.zeros(num + 1, dtype=bool)
    remove[1:] = sizes < min_area
    out = arr.copy()
    out[remove[labeled]] = 255
    return Image.fromarray(out)


def make_lineart(src_path, long_side=1100):
    """Gera contorno preservando proporcao. Fundo transparente -> branco."""
    img = Image.open(src_path).convert("RGBA")
    w, h = img.size
    scale = long_side / max(w, h)
    nw, nh = int(round(w * scale)), int(round(h * scale))
    img = img.resize((nw, nh), Image.LANCZOS)

    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(bg, img).convert("RGB")
    gray = comp.convert("L")

    # bordas internas (diferenca de gaussianas)
    g1 = np.asarray(gray.filter(ImageFilter.GaussianBlur(1.0)), dtype=np.float32)
    g2 = np.asarray(gray.filter(ImageFilter.GaussianBlur(2.6)), dtype=np.float32)
    dog = np.clip((g1 - g2) * 6.0, 0, 255).astype(np.uint8)
    edges = Image.fromarray(dog).point(lambda p: 255 if p > 26 else 0)

    # contorno externo via alpha
    alpha = img.split()[-1]
    mask = alpha.point(lambda p: 255 if p > 50 else 0)
    outline = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)),
                                  mask.filter(ImageFilter.MinFilter(5)))

    combined = ImageChops.lighter(edges, outline).filter(ImageFilter.MaxFilter(3))
    line = ImageOps.invert(combined)

    inside = np.asarray(mask.filter(ImageFilter.MaxFilter(5)))
    ln = np.asarray(line).copy()
    ln[inside == 0] = 255
    return despeckle(Image.fromarray(ln))


def colored_ref(src_path, box=300):
    img = Image.open(src_path).convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(bg, img).convert("RGB")
    comp.thumbnail((box, box), Image.LANCZOS)
    return comp


PAGE_W, PAGE_H = 1240, 1754
_FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_TITLE = ImageFont.truetype(_FB, 64)
F_SUB = ImageFont.truetype(_FR, 34)
F_LABEL = ImageFont.truetype(_FR, 30)


def build_page(src_path, title, subtitle=""):
    line = make_lineart(src_path)
    ref = colored_ref(src_path)

    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    draw = ImageDraw.Draw(page)

    tb = draw.textbbox((0, 0), title, font=F_TITLE)
    draw.text(((PAGE_W - (tb[2] - tb[0])) / 2, 50), title, fill="black", font=F_TITLE)
    if subtitle:
        sb = draw.textbbox((0, 0), subtitle, font=F_SUB)
        draw.text(((PAGE_W - (sb[2] - sb[0])) / 2, 125), subtitle, fill=(110, 110, 110), font=F_SUB)

    # desenho grande, centralizado na area de colorir
    area_top, area_h, area_w = 185, 1080, 1080
    lw, lh = line.size
    s = min(area_w / lw, area_h / lh)
    line = line.resize((int(lw * s), int(lh * s)), Image.LANCZOS)
    page.paste(line, ((PAGE_W - line.size[0]) // 2, area_top + (area_h - line.size[1]) // 2))

    draw.line([(120, 1300), (PAGE_W - 120, 1300)], fill=(200, 200, 200), width=2)
    lbl = "Referencia (colorido)"
    lb = draw.textbbox((0, 0), lbl, font=F_LABEL)
    draw.text(((PAGE_W - (lb[2] - lb[0])) / 2, 1325), lbl, fill=(90, 90, 90), font=F_LABEL)

    rw, rh = ref.size
    rx, ry = (PAGE_W - rw) // 2, 1375
    draw.rectangle([rx - 4, ry - 4, rx + rw + 3, ry + rh + 3], outline=(180, 180, 180), width=2)
    page.paste(ref, (rx, ry))
    return page
