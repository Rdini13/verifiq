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
import urllib.parse
import json
import clean_lib as C
import upgrade

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "gt_src")
OUT = os.path.join(BASE, "db_line")
os.makedirs(SRC, exist_ok=True)
UA = {"User-Agent": "coloring/1.0"}

# 3 com arte oficial limpa na wiki principal (Budokai Tenkaichi / BT3)
GOOD = [("Omega Shenron", "Omega", "Omega_Shenron"),
        ("Syn Shenron", "Syn", "Syn_Shenron"),
        ("Nuova Shenron", "Nuova", "Nuova_Shenron")]

# os outros 5 so existem como screenshot na wiki principal; a arte HD limpa
# vem da wiki do Dokkan Battle (Card <id> artwork.png, render do personagem)
DOKKAN = {
    "Eis_Shenron": "Card 1006350 artwork.png",
    "Haze_Shenron": "Card 1006340 artwork.png",
    "Rage_Shenron": "Card 1006370 artwork.png",
    "Oceanus_Shenron": "Card 1006380 artwork.png",
    "Naturon_Shenron": "Card 1006400 artwork.png",
}
DOKKAN_WIKI = "dbz-dokkanbattle.fandom.com"


def dokkan_url(filetitle):
    p = urllib.parse.urlencode({"action": "query", "titles": "File:" + filetitle,
                                "prop": "imageinfo", "iiprop": "url", "format": "json"})
    d = json.load(urllib.request.urlopen(
        urllib.request.Request(f"https://{DOKKAN_WIKI}/api.php?{p}", headers=UA), timeout=20))
    for _, pg in d.get("query", {}).get("pages", {}).items():
        ii = pg.get("imageinfo")
        if ii:
            return ii[0]["url"]

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
        _trace_save(src, name)

    for name, filetitle in DOKKAN.items():
        src = os.path.join(SRC, name.replace("_Shenron", "") + ".png")
        if not os.path.exists(src):
            u = dokkan_url(filetitle)
            if not u:
                print(f"  {name}: sem arte dokkan"); continue
            open(src, "wb").write(urllib.request.urlopen(
                urllib.request.Request(u, headers=UA), timeout=30).read())
        # a propria arte colorida do Dokkan vira a referencia colorida
        Image.open(src).convert("RGBA").save(
            os.path.join(BASE, "anime", "src", "dragonball_" + name + ".png"))
        _trace_save(src, name)


def _trace_save(src, name):
    # modo contorno (sem preencher escuro) -> mais limpo p/ colorir
    C.ink_outline(src).save(os.path.join(OUT, name + ".png"))
    print(f"  {name}: ok")


if __name__ == "__main__":
    main()
