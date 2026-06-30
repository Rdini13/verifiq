"""Junta a 1a e a 2a geracao (#001-#251) num PDF unico.
Gera uma versao leve (~12 MB) redimensionando as paginas, facil de baixar."""
import glob
import os
import img2pdf
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
LITE = os.path.join(BASE, "combo_lite")
os.makedirs(LITE, exist_ok=True)


def main():
    pages = glob.glob(os.path.join(BASE, "sc_pages", "*.jpg")) + \
        glob.glob(os.path.join(BASE, "gen2_pages", "*.jpg"))
    pages.sort(key=lambda p: int(os.path.basename(p).split(".")[0]))

    lite = []
    for p in pages:
        dst = os.path.join(LITE, os.path.basename(p))
        if not os.path.exists(dst):
            im = Image.open(p).convert("RGB")
            w, h = im.size
            im.resize((int(w * 1000 / h), 1000), Image.LANCZOS).save(dst, "JPEG", quality=80, optimize=True)
        lite.append(dst)

    A4 = img2pdf.get_layout_fun((img2pdf.in_to_pt(8.27), img2pdf.in_to_pt(11.69)))
    out = os.path.join(BASE, "Pokemon_Gen1_Gen2_completo.pdf")
    with open(out, "wb") as f:
        f.write(img2pdf.convert(lite, layout_fun=A4))
    print("PDF:", out, round(os.path.getsize(out) / 1e6, 1), "MB", len(lite), "paginas")


if __name__ == "__main__":
    main()
