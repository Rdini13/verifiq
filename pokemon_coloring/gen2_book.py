"""Monta o livro de colorir da 2a geracao (#152-#251): line art (supercoloring/
pokemoncoloring) + referencia colorida (arte oficial PokeAPI)."""
import os
import glob
import img2pdf
from PIL import Image, ImageDraw, ImageFont
from gen2_fetch import NAMES  # 152..251

BASE = os.path.dirname(os.path.abspath(__file__))
LINE = os.path.join(BASE, "sc_line")
ART = os.path.join(BASE, "art")
PG = os.path.join(BASE, "gen2_pages")
os.makedirs(PG, exist_ok=True)

PAGE_W, PAGE_H = 1240, 1754
F_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 66)
F_LABEL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)


def white_bg(im):
    im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, im).convert("RGB")


def page(dex, name):
    p = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(p)
    title = f"#{dex:03d}  {name}"
    tb = d.textbbox((0, 0), title, font=F_TITLE)
    d.text(((PAGE_W - (tb[2] - tb[0])) / 2, 48), title, fill="black", font=F_TITLE)

    line = white_bg(Image.open(os.path.join(LINE, f"{dex}.png")))
    box_w, box_h = 1080, 1120
    s = min(box_w / line.width, box_h / line.height)
    line = line.resize((int(line.width * s), int(line.height * s)), Image.LANCZOS)
    p.paste(line, ((PAGE_W - line.width) // 2, 170 + (box_h - line.height) // 2))

    ref_path = os.path.join(ART, f"{dex}.png")
    if os.path.exists(ref_path):
        d.line([(120, 1340), (PAGE_W - 120, 1340)], fill=(205, 205, 205), width=2)
        lbl = "Referencia (colorido)"
        lb = d.textbbox((0, 0), lbl, font=F_LABEL)
        d.text(((PAGE_W - (lb[2] - lb[0])) / 2, 1366), lbl, fill=(90, 90, 90), font=F_LABEL)
        ref = white_bg(Image.open(ref_path)).resize((300, 300), Image.LANCZOS)
        rx, ry = (PAGE_W - 300) // 2, 1420
        d.rectangle([rx - 4, ry - 4, rx + 303, ry + 303], outline=(180, 180, 180), width=2)
        p.paste(ref, (rx, ry))
    return p


def main():
    pages = []
    for i, name in enumerate(NAMES):
        dex = 152 + i
        out = os.path.join(PG, f"{dex}.jpg")
        page(dex, name).save(out, "JPEG", quality=90, optimize=True)
        pages.append(out)
        print(f"  {dex} {name}")
    pages.sort(key=lambda p: int(os.path.basename(p).split(".")[0]))
    A4 = img2pdf.get_layout_fun((img2pdf.in_to_pt(8.27), img2pdf.in_to_pt(11.69)))
    out = os.path.join(BASE, "Pokemon_Gen2_para_colorir.pdf")
    with open(out, "wb") as f:
        f.write(img2pdf.convert(pages, layout_fun=A4))
    print("PDF:", out, round(os.path.getsize(out) / 1e6, 1), "MB", len(pages), "paginas")


if __name__ == "__main__":
    main()
