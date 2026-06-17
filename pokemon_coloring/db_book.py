"""Monta o livro de colorir de Dragon Ball com line art REAL (db_line/)
+ referencia colorida (render do wiki em anime/src)."""
import os
import glob
import json
import img2pdf
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
LINE = os.path.join(BASE, "db_line")
SRC = os.path.join(BASE, "anime", "src")
PG = os.path.join(BASE, "db_pages")
os.makedirs(PG, exist_ok=True)
resolved = json.load(open(os.path.join(BASE, "resolved.json")))

PAGE_W, PAGE_H = 1240, 1754
F_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 66)
F_SUB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
F_LABEL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)


def white_bg(im):
    im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, im).convert("RGB")


def fname(name):
    return name.replace(" ", "_").replace(".", "")


def page(name):
    p = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(p)
    tb = d.textbbox((0, 0), name, font=F_TITLE)
    d.text(((PAGE_W - (tb[2] - tb[0])) / 2, 56), name, fill="black", font=F_TITLE)
    sub = "Dragon Ball"
    sb = d.textbbox((0, 0), sub, font=F_SUB)
    d.text(((PAGE_W - (sb[2] - sb[0])) / 2, 138), sub, fill=(110, 110, 110), font=F_SUB)

    line = white_bg(Image.open(os.path.join(LINE, fname(name) + ".png")))
    box_w, box_h = 1080, 1080
    s = min(box_w / line.width, box_h / line.height)
    line = line.resize((int(line.width * s), int(line.height * s)), Image.LANCZOS)
    p.paste(line, ((PAGE_W - line.width) // 2, 210 + (box_h - line.height) // 2))

    # referencia colorida (se houver render do wiki)
    ref_path = os.path.join(SRC, "dragonball_" + fname(name).replace("_", "_") + ".png")
    ref_path2 = os.path.join(SRC, "dragonball_" + name.replace(" ", "_").replace("/", "_") + ".png")
    rp = ref_path2 if os.path.exists(ref_path2) else ref_path
    if os.path.exists(rp):
        d.line([(120, 1340), (PAGE_W - 120, 1340)], fill=(205, 205, 205), width=2)
        lbl = "Referencia (colorido)"
        lb = d.textbbox((0, 0), lbl, font=F_LABEL)
        d.text(((PAGE_W - (lb[2] - lb[0])) / 2, 1366), lbl, fill=(90, 90, 90), font=F_LABEL)
        ref = white_bg(Image.open(rp))
        rs = min(300 / ref.width, 300 / ref.height)
        ref = ref.resize((int(ref.width * rs), int(ref.height * rs)), Image.LANCZOS)
        rx, ry = (PAGE_W - ref.width) // 2, 1420
        d.rectangle([rx - 4, ry - 4, rx + ref.width + 3, ry + ref.height + 3], outline=(180, 180, 180), width=2)
        p.paste(ref, (rx, ry))
    return p


def main():
    order = [n for n in resolved["dragonball"] if os.path.exists(os.path.join(LINE, fname(n) + ".png"))]
    for name in order:
        page(name).save(os.path.join(PG, fname(name) + ".jpg"), "JPEG", quality=90, optimize=True)
        print("  ", name)
    pages = [os.path.join(PG, fname(n) + ".jpg") for n in order]
    A4 = img2pdf.get_layout_fun((img2pdf.in_to_pt(8.27), img2pdf.in_to_pt(11.69)))
    out = os.path.join(BASE, "DragonBall_para_colorir.pdf")
    with open(out, "wb") as f:
        f.write(img2pdf.convert(pages, layout_fun=A4))
    print("PDF:", out, round(os.path.getsize(out) / 1e6, 1), "MB", len(pages), "paginas")


if __name__ == "__main__":
    main()
