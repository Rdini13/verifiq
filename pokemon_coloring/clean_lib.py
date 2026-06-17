"""Contorno limpo e grosso (estilo livro de colorir para criancas).

Tecnica: remove o fundo (rembg) e extrai linhas pelas FRONTEIRAS entre
regioes de cor achatadas (posterizacao), em vez de deteccao de bordas. Isso
ignora o sombreado interno e produz tracos fechados e limpos.
"""
import os
import urllib.request
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageChops, ImageDraw, ImageFont
from scipy import ndimage

UA = "coloring-book/1.0 (educational)"
_SESSIONS = {}


def _session(name="isnet-anime"):
    if name not in _SESSIONS:
        from rembg import new_session
        _SESSIONS[name] = new_session(name)
    return _SESSIONS[name]


def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 2000:
        return path
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r, open(path, "wb") as f:
                f.write(r.read())
            return path
        except Exception:
            if attempt == 3:
                raise
    return path


def cutout(src_path, long_side=1100):
    """Devolve RGBA (corpo recortado), proporcao preservada.

    Se a arte ja tem fundo transparente (ex.: artwork de Pokemon), usa direto.
    Caso contrario, remove o fundo com rembg. Se o recorte ficar pequeno
    demais (rembg falhou), volta para a imagem original.
    """
    from rembg import remove
    img = Image.open(src_path).convert("RGBA")
    a = np.asarray(img.split()[-1])
    transparent_frac = (a < 10).mean()

    if transparent_frac > 0.05:
        out = img  # ja tem fundo transparente
    else:
        out = remove(img, session=_session("isnet-anime"))
        oa = np.asarray(out.split()[-1])
        cover = (oa > 60).mean()
        if cover < 0.02 or cover > 0.82:
            # modelo anime falhou (apagou tudo OU nao removeu fundo de cena);
            # tenta modelo de uso geral com alpha matting
            alt = remove(img, session=_session("isnet-general-use"),
                         alpha_matting=True, alpha_matting_foreground_threshold=240,
                         alpha_matting_background_threshold=15)
            aa = np.asarray(alt.split()[-1])
            ac = (aa > 60).mean()
            if 0.02 < ac < cover:   # removeu mais fundo e sobrou sujeito
                out = alt
            elif cover < 0.02:      # anime apagou tudo: usa geral ou original
                out = alt if ac > 0.05 else img
    w, h = out.size
    s = long_side / max(w, h)
    return out.resize((int(round(w * s)), int(round(h * s))), Image.LANCZOS)


def _clean_mask(alpha, min_hole=400):
    m = np.asarray(alpha.point(lambda p: 255 if p > 90 else 0)) > 0
    m = ndimage.binary_fill_holes(m)
    # mantem so o maior componente (corpo)
    lbl, n = ndimage.label(m)
    if n > 1:
        sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
        m = lbl == (1 + int(np.argmax(sizes)))
    return m


# niveis de simplificacao: do mais detalhado (0) ao mais simples (5)
# (posterize, median, blur, min_region)
LEVELS = [
    (11, 3, 0.8, 120),
    (9, 5, 1.1, 250),
    (7, 5, 1.4, 450),
    (6, 7, 1.8, 750),
    (5, 7, 2.3, 1200),
    (4, 9, 2.8, 1800),
]


def _lineart_level(comp, mask, level, thickness=3):
    posterize, median, blur, min_region = LEVELS[level]
    sm = comp.filter(ImageFilter.MedianFilter(median)).filter(ImageFilter.GaussianBlur(blur))
    q = sm.quantize(colors=posterize, method=Image.MEDIANCUT, dither=Image.NONE)
    labels = np.asarray(q).astype(np.int32)
    labels[~mask] = -1

    diff = np.zeros(labels.shape, dtype=bool)
    diff[:, :-1] |= labels[:, :-1] != labels[:, 1:]
    diff[:-1, :] |= labels[:-1, :] != labels[1:, :]
    diff &= mask

    # apaga fronteiras que cercam regioes minusculas (ruido de sombreado)
    reg_lbl, rn = ndimage.label(mask & (labels >= 0))
    if rn:
        sizes = ndimage.sum(np.ones_like(reg_lbl), reg_lbl, range(1, rn + 1))
        small = np.zeros(rn + 1, dtype=bool)
        small[1:] = sizes < min_region
        small_px = small[reg_lbl]
        diff &= ~small_px

    line_bool = diff
    sil = ndimage.binary_dilation(mask, iterations=1) & ~ndimage.binary_erosion(mask, iterations=2)
    line_bool |= sil
    line_bool = ndimage.binary_dilation(line_bool, iterations=max(1, thickness // 2))

    lbl, n = ndimage.label(line_bool)
    if n:
        sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
        keep = np.zeros(n + 1, dtype=bool)
        keep[1:] = sizes >= 50
        line_bool = keep[lbl]
    return line_bool


def lineart(rgba, thickness=3):
    """Traco adaptativo: ajusta a simplificacao para uma densidade de tinta
    confortavel (nem carregado demais, nem vazio). Simplifica imagens muito
    detalhadas e adiciona detalhe nas que ficariam vazias."""
    bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(bg, rgba).convert("RGB")
    mask = _clean_mask(rgba.split()[-1])
    mask_area = max(1, int(mask.sum()))

    LOW, HIGH = 0.045, 0.115  # faixa-alvo de densidade de tinta interna
    level = 2
    best = None
    for _ in range(5):
        line_bool = _lineart_level(comp, mask, level, thickness)
        interior = ndimage.binary_erosion(mask, iterations=3)
        ink = (line_bool & interior).sum() / max(1, int(interior.sum()))
        # guarda o melhor (mais perto do centro da faixa)
        center = (LOW + HIGH) / 2
        score = abs(ink - center)
        if best is None or score < best[0]:
            best = (score, line_bool)
        if ink > HIGH and level < len(LEVELS) - 1:
            level += 1
        elif ink < LOW and level > 0:
            level -= 1
        else:
            break
    line_bool = best[1]
    out = np.where(line_bool, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def colored_ref(rgba, box=300):
    bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(bg, rgba).convert("RGB")
    comp.thumbnail((box, box), Image.LANCZOS)
    return comp


PAGE_W, PAGE_H = 1240, 1754
_FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_TITLE = ImageFont.truetype(_FB, 66)
F_SUB = ImageFont.truetype(_FR, 34)
F_LABEL = ImageFont.truetype(_FR, 30)


def build_page(src_path, title, subtitle=""):
    rgba = cutout(src_path)
    line = lineart(rgba)
    ref = colored_ref(rgba)

    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    draw = ImageDraw.Draw(page)
    tb = draw.textbbox((0, 0), title, font=F_TITLE)
    draw.text(((PAGE_W - (tb[2] - tb[0])) / 2, 50), title, fill="black", font=F_TITLE)
    if subtitle:
        sb = draw.textbbox((0, 0), subtitle, font=F_SUB)
        draw.text(((PAGE_W - (sb[2] - sb[0])) / 2, 128), subtitle, fill=(110, 110, 110), font=F_SUB)

    area_top, area_h, area_w = 190, 1070, 1080
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
