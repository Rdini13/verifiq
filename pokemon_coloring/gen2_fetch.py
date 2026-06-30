"""Baixa as paginas de colorir (supercoloring) da 2a geracao (#152-#251)."""
import os
import re
import time
import json
import io
import urllib.request
import urllib.parse
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
LINE = os.path.join(BASE, "sc_line")
ART = os.path.join(BASE, "art")
os.makedirs(LINE, exist_ok=True)
os.makedirs(ART, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MD = re.compile(r'cdn\.supercoloring\.com/coloring/\d+/[a-z0-9-]+-coloring-page-md\.png')
ART_URL = ("https://raw.githubusercontent.com/PokeAPI/sprites/master/"
           "sprites/pokemon/other/official-artwork/{}.png")

NAMES = [
    "Chikorita", "Bayleef", "Meganium", "Cyndaquil", "Quilava", "Typhlosion",
    "Totodile", "Croconaw", "Feraligatr", "Sentret", "Furret", "Hoothoot",
    "Noctowl", "Ledyba", "Ledian", "Spinarak", "Ariados", "Crobat", "Chinchou",
    "Lanturn", "Pichu", "Cleffa", "Igglybuff", "Togepi", "Togetic", "Natu",
    "Xatu", "Mareep", "Flaaffy", "Ampharos", "Bellossom", "Marill", "Azumarill",
    "Sudowoodo", "Politoed", "Hoppip", "Skiploom", "Jumpluff", "Aipom",
    "Sunkern", "Sunflora", "Yanma", "Wooper", "Quagsire", "Espeon", "Umbreon",
    "Murkrow", "Slowking", "Misdreavus", "Unown", "Wobbuffet", "Girafarig",
    "Pineco", "Forretress", "Dunsparce", "Gligar", "Steelix", "Snubbull",
    "Granbull", "Qwilfish", "Scizor", "Shuckle", "Heracross", "Sneasel",
    "Teddiursa", "Ursaring", "Slugma", "Magcargo", "Swinub", "Piloswine",
    "Corsola", "Remoraid", "Octillery", "Delibird", "Mantine", "Skarmory",
    "Houndour", "Houndoom", "Kingdra", "Phanpy", "Donphan", "Porygon2",
    "Stantler", "Smeargle", "Tyrogue", "Hitmontop", "Smoochum", "Elekid",
    "Magby", "Miltank", "Blissey", "Raikou", "Entei", "Suicune", "Larvitar",
    "Pupitar", "Tyranitar", "Lugia", "Ho-Oh", "Celebi",
]  # 152..251


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")


def slugify(name):
    return name.lower().replace("'", "").replace(".", "").replace(" ", "-")


def find_md(name, dex):
    slug = slugify(name)
    pref = f"{dex:03d}-"
    for cand in [f"{slug}-pokemon", slug, f"{slug}-pokemon-1"]:
        try:
            html = get(f"https://www.supercoloring.com/coloring-pages/{cand}")
            hits = MD.findall(html)
            if hits:
                p = [h for h in hits if re.search(rf'/{pref}', h)]
                return (p or hits)[0]
        except Exception:
            pass
    try:  # busca, exigindo prefixo da dex
        html = get("https://www.supercoloring.com/search?" + urllib.parse.urlencode({"q": f"{name} pokemon"}))
        hits = MD.findall(html)
        p = [h for h in hits if re.search(rf'/{pref}', h)]
        if p:
            return p[0]
    except Exception:
        pass
    return None


def main():
    missing = []
    for i, name in enumerate(NAMES):
        dex = 152 + i
        dst = os.path.join(LINE, f"{dex:03d}.png")
        if not (os.path.exists(dst) and os.path.getsize(dst) > 3000):
            md = find_md(name, dex)
            if md:
                orig = "https://" + md.replace("-md.png", "-original.png")
                try:
                    data = urllib.request.urlopen(urllib.request.Request(orig, headers={"User-Agent": UA}), timeout=30).read()
                    open(dst, "wb").write(data)
                    print(f"  {dex} {name:12s} ok")
                except Exception as e:
                    missing.append((dex, name)); print(f"  {dex} {name}: DL FAIL {e}")
            else:
                missing.append((dex, name)); print(f"  {dex} {name}: MISSING")
            time.sleep(0.25)
        # referencia colorida
        ref = os.path.join(ART, f"{dex}.png")
        if not (os.path.exists(ref) and os.path.getsize(ref) > 1000):
            try:
                urllib.request.urlretrieve(ART_URL.format(dex), ref)
            except Exception:
                pass
    json.dump({"missing": missing}, open(os.path.join(BASE, "gen2_missing.json"), "w"))
    print(f"\nFaltando: {len(missing)} -> {missing}")


if __name__ == "__main__":
    main()
