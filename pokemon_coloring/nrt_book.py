"""Livro de colorir do Naruto: personagens (desenhos prontos do coloringlib/
animecoloringpages) + as 9 Bestas com Cauda. Mesmo layout dos outros livros."""
import os
import glob
import img2pdf
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
LINE = os.path.join(BASE, "nrt_line")
REF = os.path.join(BASE, "nrt_ref")
PG = os.path.join(BASE, "nrt_pages")
os.makedirs(PG, exist_ok=True)

PAGE_W, PAGE_H = 1240, 1754
F_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 66)
F_SUB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
F_LABEL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)

# (nome exibido, arquivo, legenda)
CURATED = [
    ("Naruto", "Naruto", "Naruto"),
    ("Sasuke", "Sasuke", "Naruto"),
    ("Sakura", "Sakura", "Naruto"),
    ("Kakashi", "Kakashi", "Naruto"),
    ("Hinata", "Hinata", "Naruto"),
    ("Shikamaru", "Shikamaru", "Naruto"),
    ("Rock Lee", "Rock_Lee", "Naruto"),
    ("Neji", "Neji", "Naruto"),
    ("Gaara", "Gaara", "Naruto"),
    ("Jiraiya", "Jiraiya", "Naruto"),
    ("Tsunade", "Tsunade", "Naruto"),
    ("Orochimaru", "Orochimaru", "Naruto"),
    ("Itachi", "Itachi", "Naruto"),
    ("Madara", "Madara", "Naruto"),
    ("Obito", "Obito", "Naruto"),
    ("Pain", "Pain", "Naruto"),
    ("Minato", "Minato", "Naruto"),
    ("Killer B", "Killer_B", "Naruto"),
    # --- Bestas com Cauda ---
    ("Kurama", "Kurama", "Naruto • Besta de 9 Caudas"),
]


def white_bg(im):
    im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, im).convert("RGB")


def page(display, line_file, subtitle):
    p = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(p)
    tb = d.textbbox((0, 0), display, font=F_TITLE)
    d.text(((PAGE_W - (tb[2] - tb[0])) / 2, 56), display, fill="black", font=F_TITLE)
    sb = d.textbbox((0, 0), subtitle, font=F_SUB)
    d.text(((PAGE_W - (sb[2] - sb[0])) / 2, 140), subtitle, fill=(110, 110, 110), font=F_SUB)

    line = white_bg(Image.open(os.path.join(LINE, line_file + ".png")))
    box_w, box_h = 1080, 1080
    s = min(box_w / line.width, box_h / line.height)
    line = line.resize((int(line.width * s), int(line.height * s)), Image.LANCZOS)
    p.paste(line, ((PAGE_W - line.width) // 2, 210 + (box_h - line.height) // 2))

    rp = os.path.join(REF, line_file + ".png")
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
    pages = []
    for display, line_file, subtitle in CURATED:
        if not os.path.exists(os.path.join(LINE, line_file + ".png")):
            print("  FALTA:", display); continue
        out = os.path.join(PG, line_file + ".jpg")
        page(display, line_file, subtitle).save(out, "JPEG", quality=90, optimize=True)
        pages.append(out)
        print("  ", display)
    A4 = img2pdf.get_layout_fun((img2pdf.in_to_pt(8.27), img2pdf.in_to_pt(11.69)))
    out = os.path.join(BASE, "Naruto_para_colorir.pdf")
    with open(out, "wb") as f:
        f.write(img2pdf.convert(pages, layout_fun=A4))
    print("PDF:", out, round(os.path.getsize(out) / 1e6, 1), "MB", len(pages), "paginas")


if __name__ == "__main__":
    main()
