"""Dragoes das Sombras de Dragon Ball GT.

Nao existem como pagina de colorir pronta em nenhum site. Aqui baixamos a arte
oficial mais limpa de cada um (renders de jogo: Budokai Tenkaichi, Dokkan, etc.)
e geramos o tracado com clean_lib.ink_lineart (extracao das linhas de tinta).

Saida boa: Omega, Syn, Nuova (tem arte oficial limpa).
Saida ruim: Eis, Haze, Rage, Oceanus, Naturon (so existe screenshot) -> ficam
de fora do livro por enquanto.
"""
import io
import os
import urllib.request
import numpy as np
from PIL import Image
from scipy import ndimage
import clean_lib as C
import upgrade

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "gt_src")
OUT = os.path.join(BASE, "db_line")
os.makedirs(SRC, exist_ok=True)
UA = {"User-Agent": "coloring/1.0"}

# os 3 com arte oficial limpa o suficiente para um bom tracado
GOOD = [("Omega Shenron", "Omega", "Omega_Shenron"),
        ("Syn Shenron", "Syn", "Syn_Shenron"),
        ("Nuova Shenron", "Nuova", "Nuova_Shenron")]

KW = {"artwork": 6, "tenkaichi": 5, "dokkan": 4, "render": 3, "profile": 3, "legends": 3}
BAD = ["ep.", " vs", "and ", "&", "screenshot", "mission", "trailer", "saga ",
       "blast", "wave", "smirk", "transforma"]


def best_art(title, key):
    cands = upgrade.list_images("dragonball", title, key)

    def score(f):
        l = f.lower()
        return (sum(v for k, v in KW.items() if k in l)
                - sum(4 for b in BAD if b in l) + (1 if l.endswith(".png") else 0))
    for f in sorted(cands, key=score, reverse=True)[:8]:
        u, w, h = upgrade.file_url("dragonball", f)
        if u and w and max(w, h) >= 300:
            try:
                return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read()
            except Exception:
                pass
    return None


def main():
    for title, key, name in GOOD:
        src = os.path.join(SRC, f"{key}.png")
        if not os.path.exists(src):
            raw = best_art(title, key)
            if not raw:
                print(f"  {name}: sem arte"); continue
            open(src, "wb").write(raw)
        line = C.ink_lineart(src)
        # engrossa levemente para um traco mais firme
        a = ndimage.binary_dilation(np.asarray(line.convert("L")) < 128, iterations=1)
        Image.fromarray(np.where(a, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name + ".png"))
        print(f"  {name}: ok")


if __name__ == "__main__":
    main()
