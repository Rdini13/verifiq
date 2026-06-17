"""Builder final: gera as paginas (Pokemon + animes) com o traco aprimorado,
salva PNGs, monta um PDF por colecao e um PDF unico com tudo."""
import json
import os
import glob
import img2pdf
import clean_lib as C
from build import NAMES as POKE_NAMES  # 151 nomes

BASE = os.path.dirname(os.path.abspath(__file__))
PNG = os.path.join(BASE, "out_png")
SRC = os.path.join(BASE, "anime", "src")
POKE_ART = os.path.join(BASE, "art")
resolved = json.load(open(os.path.join(BASE, "resolved.json")))

DRAGONS = {
    "Shenron", "Porunga", "Super Shenron", "Black Smoke Shenron", "Syn Shenron",
    "Omega Shenron", "Nuova Shenron", "Eis Shenron", "Haze Shenron",
    "Rage Shenron", "Oceanus Shenron", "Naturon Shenron", "Icarus",
}
ANIME = [
    ("dragonball", "Dragon Ball"),
    ("naruto", "Naruto"),
    ("onepiece", "One Piece"),
]


def save_page(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.convert("RGB").save(path, "PNG")


def build_pokemon():
    outdir = os.path.join(PNG, "pokemon")
    for i, name in enumerate(POKE_NAMES, start=1):
        dst = os.path.join(outdir, f"{i:03d}.png")
        if os.path.exists(dst):
            continue
        src = os.path.join(POKE_ART, f"{i}.png")
        page = C.build_page(src, f"#{i:03d}  {name}", "Pokemon")
        save_page(page, dst)
        print(f"  Pokemon {i:3d}/151 {name}")


def build_anime(wiki, label):
    entries = resolved[wiki]
    names = list(entries.keys())
    if wiki == "dragonball":
        names = [n for n in names if n not in DRAGONS] + [n for n in names if n in DRAGONS]
    outdir = os.path.join(PNG, wiki)
    for idx, name in enumerate(names, start=1):
        info = entries[name]
        if not info.get("url"):
            continue
        dst = os.path.join(outdir, f"{idx:02d}_{name}.png".replace(" ", "_").replace("/", "_"))
        if os.path.exists(dst):
            continue
        path = os.path.join(SRC, f"{wiki}_{name}.png".replace(" ", "_").replace("/", "_"))
        sub = f"{label} - Dragao" if (wiki == "dragonball" and name in DRAGONS) else label
        C.fetch(info["url"], path)
        page = C.build_page(path, name, sub)
        save_page(page, dst)
        print(f"  [{label}] {name}")


def pdf_from(pngs, out):
    with open(out, "wb") as f:
        f.write(img2pdf.convert(pngs, layout_fun=img2pdf.get_layout_fun((img2pdf.in_to_pt(8.27), img2pdf.in_to_pt(11.69)))))
    print("==>", out, f"({len(pngs)} paginas)")


def main():
    build_pokemon()
    for wiki, label in ANIME:
        build_anime(wiki, label)

    poke = sorted(glob.glob(os.path.join(PNG, "pokemon", "*.png")))
    db = sorted(glob.glob(os.path.join(PNG, "dragonball", "*.png")))
    na = sorted(glob.glob(os.path.join(PNG, "naruto", "*.png")))
    op = sorted(glob.glob(os.path.join(PNG, "onepiece", "*.png")))

    pdf_from(poke, os.path.join(BASE, "Pokemon_150_para_colorir.pdf"))
    pdf_from(db, os.path.join(BASE, "DragonBall_para_colorir.pdf"))
    pdf_from(na, os.path.join(BASE, "Naruto_para_colorir.pdf"))
    pdf_from(op, os.path.join(BASE, "OnePiece_para_colorir.pdf"))
    pdf_from(poke + db + na + op, os.path.join(BASE, "Livro_Colorir_Completo.pdf"))


if __name__ == "__main__":
    main()
