"""Monta os PDFs de colorir por franquia (Dragon Ball, Naruto, One Piece)."""
import json
import os
import clean_lib as C

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "anime", "src")
os.makedirs(SRC, exist_ok=True)
resolved = json.load(open(os.path.join(BASE, "resolved.json")))

DRAGONS = {
    "Shenron", "Porunga", "Super Shenron", "Black Smoke Shenron", "Syn Shenron",
    "Omega Shenron", "Nuova Shenron", "Eis Shenron", "Haze Shenron",
    "Rage Shenron", "Oceanus Shenron", "Naturon Shenron", "Icarus",
}

# (franquia, arquivo_saida, rotulo, ordem_de_nomes)
JOBS = [
    ("dragonball", "DragonBall_para_colorir.pdf", "Dragon Ball"),
    ("naruto", "Naruto_para_colorir.pdf", "Naruto"),
    ("onepiece", "OnePiece_para_colorir.pdf", "One Piece"),
]


def subtitle(wiki, label, name):
    if wiki == "dragonball" and name in DRAGONS:
        return f"{label} - Dragao"
    return label


def main():
    for wiki, out_pdf, label in JOBS:
        entries = resolved[wiki]
        # ordena: personagens primeiro, dragoes depois (so dragon ball)
        names = list(entries.keys())
        if wiki == "dragonball":
            names = [n for n in names if n not in DRAGONS] + [n for n in names if n in DRAGONS]
        pages = []
        for name in names:
            info = entries[name]
            if not info.get("url"):
                print("  pulando (sem imagem):", name)
                continue
            path = os.path.join(SRC, f"{wiki}_{name}.png".replace(" ", "_").replace("/", "_"))
            try:
                C.fetch(info["url"], path)
                pages.append(C.build_page(path, name, subtitle(wiki, label, name)))
                print(f"  [{label}] {name}")
            except Exception as e:
                print(f"  ERRO {name}: {e}")
        out = os.path.join(BASE, out_pdf)
        pages[0].save(out, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
        print(f"==> {out}  ({len(pages)} paginas)\n")


if __name__ == "__main__":
    main()
