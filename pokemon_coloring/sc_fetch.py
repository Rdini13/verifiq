"""Resolve e baixa as paginas de colorir (line art feito a mao) do supercoloring
para os 151 Pokemon da 1a geracao."""
import os
import re
import time
import json
import urllib.request
import urllib.parse
from build import NAMES  # 151 nomes na ordem da Pokedex

BASE = os.path.dirname(os.path.abspath(__file__))
LINE = os.path.join(BASE, "sc_line")
os.makedirs(LINE, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MD = re.compile(r'cdn\.supercoloring\.com/coloring/\d+/[a-z0-9-]+-coloring-page-md\.png')


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")


def slugify(name):
    s = name.lower().replace("'", "").replace(".", "")
    s = s.replace(" ", "-")
    return s


# Pokemon ausentes do conjunto numerado do supercoloring -> fonte alternativa
# (URL direta de uma pagina de colorir limpa e correta)
OVERRIDES = {
    80: "https://coloriez-les-tous.s3.eu-west-3.amazonaws.com/coloring/slowbro/slowbro-002.jpg",
    # #130: a pagina tem Gyarados normal E Mega Gyarados; fixa o normal
    130: "https://cdn.supercoloring.com/coloring/361793/130-gyarados-coloring-page-original.png",
}


def find_md(name, dex):
    slug = slugify(name)
    # 1) pagina individual <slug>-pokemon
    for cand in [f"{slug}-pokemon", slug]:
        try:
            html = get(f"https://www.supercoloring.com/coloring-pages/{cand}")
            # prefere a imagem cujo slug comeca com o numero da dex (conjunto numerado)
            hits = MD.findall(html)
            if hits:
                pref = [h for h in hits if re.search(rf'/{dex:03d}-', h)]
                return (pref or hits)[0]
        except Exception:
            pass
    # 2) busca no site
    try:
        q = urllib.parse.urlencode({"q": f"{name} pokemon"})
        html = get(f"https://www.supercoloring.com/search?{q}")
        hits = MD.findall(html)
        pref = [h for h in hits if re.search(rf'/{dex:03d}-', h)]
        if pref:
            return pref[0]
        # senao, primeiro resultado que contenha o nome no slug
        nm = slugify(name).split("-")[0]
        named = [h for h in hits if nm in h]
        if named:
            return named[0]
        if hits:
            return hits[0]
    except Exception:
        pass
    return None


def main():
    resolved = {}
    missing = []
    for dex, name in enumerate(NAMES, start=1):
        dst = os.path.join(LINE, f"{dex:03d}.png")
        if os.path.exists(dst) and os.path.getsize(dst) > 3000:
            resolved[dex] = name
            continue
        if dex in OVERRIDES:
            try:
                req = urllib.request.Request(OVERRIDES[dex], headers={"User-Agent": UA})
                from PIL import Image
                import io
                Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB").save(dst)
                resolved[dex] = name
                print(f"  {dex:3d} {name:14s} ok (override)")
                continue
            except Exception as e:
                print(f"  {dex:3d} {name:14s} override FAIL {e}")
        md = find_md(name, dex)
        if not md:
            missing.append((dex, name))
            print(f"  {dex:3d} {name:14s} -> MISSING")
            continue
        orig = "https://" + md.replace("-md.png", "-original.png")
        try:
            req = urllib.request.Request(orig, headers={"User-Agent": UA})
            data = urllib.request.urlopen(req, timeout=30).read()
            with open(dst, "wb") as f:
                f.write(data)
            resolved[dex] = name
            print(f"  {dex:3d} {name:14s} ok ({len(data)//1024} KB)")
        except Exception as e:
            missing.append((dex, name))
            print(f"  {dex:3d} {name:14s} -> DL FAIL {e}")
        time.sleep(0.3)
    json.dump({"missing": missing}, open(os.path.join(BASE, "sc_missing.json"), "w"), indent=2)
    print(f"\nResolvidos: {len(resolved)}/151  | Faltando: {len(missing)}")
    if missing:
        print("Faltando:", ", ".join(f"{d:03d} {n}" for d, n in missing))


if __name__ == "__main__":
    main()
