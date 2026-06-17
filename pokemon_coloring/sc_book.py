"""Monta o livro de colorir dos 151 Pokemon com o line art feito a mao
(supercoloring) + referencia colorida (arte oficial) embaixo."""
import os
import glob
import img2pdf
from PIL import Image, ImageDraw, ImageFont
from build import NAMES

BASE = os.path.dirname(os.path.abspath(__file__))
LINE = os.path.join(BASE, "sc_line")
ART = os.path.join(BASE, "art")
PG = os.path.join(BASE, "sc_pages")
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

    line = white_bg(Image.open(os.path.join(LINE, f"{dex:03d}.png")))
    box_w, box_h = 1080, 1120
    s = min(box_w / line.width, box_h / line.height)
    line = line.resize((int(line.width * s), int(line.height * s)), Image.LANCZOS)
    p.paste(line, ((PAGE_W - line.width) // 2, 170 + (box_h - line.height) // 2))

    d.line([(120, 1340), (PAGE_W - 120, 1340)], fill=(205, 205, 205), width=2)
    lbl = "Referencia (colorido)"
    lb = d.textbbox((0, 0), lbl, font=F_LABEL)
    d.text(((PAGE_W - (lb[2] - lb[0])) / 2, 1366), lbl, fill=(90, 90, 90), font=F_LABEL)

    ref = white_bg(Image.open(os.path.join(ART, f"{dex}.png"))).resize((300, 300), Image.LANCZOS)
    rx, ry = (PAGE_W - 300) // 2, 1420
    d.rectangle([rx - 4, ry - 4, rx + 303, ry + 303], outline=(180, 180, 180), width=2)
    p.paste(ref, (rx, ry))
    return p


def main():
    for dex, name in enumerate(NAMES, start=1):
        dst = os.path.join(PG, f"{dex:03d}.jpg")
        page(dex, name).save(dst, "JPEG", quality=90, optimize=True)
        print(f"  {dex:3d}/151 {name}")
    pages = sorted(glob.glob(os.path.join(PG, "*.jpg")))
    A4 = img2pdf.get_layout_fun((img2pdf.in_to_pt(8.27), img2pdf.in_to_pt(11.69)))
    out = os.path.join(BASE, "Pokemon_150_para_colorir.pdf")
    with open(out, "wb") as f:
        f.write(img2pdf.convert(pages, layout_fun=A4))
    print("PDF:", out, round(os.path.getsize(out) / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
