"""Acha uma imagem-fonte melhor (render de fundo transparente) para os fracos."""
import io
import json
import urllib.parse
import urllib.request
import numpy as np
from PIL import Image

UA = "coloring-book/1.0 (educational)"
BASES = {
    "dragonball": "https://dragonball.fandom.com",
    "naruto": "https://naruto.fandom.com",
    "onepiece": "https://onepiece.fandom.com",
}
GOOD = ["artwork", "render", "burning blood", "pirate warriors", "heroes",
        "bt3", "dokkan", "legends", "tenkaichi", "xenoverse", "thousand storm",
        "figure", "kanzenban", "(game", "sparking", "transparent"]
BAD = ["anime", "manga", "infobox", "poster", "wanted", "eyecatcher", "scar",
       "baby", "color scheme", "arm", "scene", "meets", " vs ", "wedding",
       "concept", "omake", "statue", "screenshot", "card", "sticker", "logo",
       "symbol", "kanji", "eye", "face", "profile", "outfit", "as a"]


def _api(wiki, params):
    params.update({"format": "json"})
    url = f"{BASES[wiki]}/api.php?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=30))


def list_images(wiki, title, key):
    d = _api(wiki, {"action": "query", "titles": title, "prop": "images",
                    "imlimit": "500", "redirects": "1"})
    files = []
    for _, p in d.get("query", {}).get("pages", {}).items():
        for im in p.get("images", []):
            t = im["title"]
            if t.lower().endswith((".png", ".jpg", ".jpeg")):
                files.append(t)
    k = key.lower()
    files = [f for f in files if k in f.lower()]

    def score(f):
        lf = f.lower()
        s = 0
        s += sum(3 for g in GOOD if g in lf)
        s -= sum(4 for b in BAD if b in lf)
        s += 2 if lf.endswith(".png") else 0
        return s
    return sorted(files, key=score, reverse=True)


def file_url(wiki, filetitle):
    d = _api(wiki, {"action": "query", "titles": filetitle,
                    "prop": "imageinfo", "iiprop": "url|size"})
    for _, p in d.get("query", {}).get("pages", {}).items():
        ii = p.get("imageinfo")
        if ii:
            return ii[0]["url"], ii[0].get("width"), ii[0].get("height")
    return None, None, None


def best_transparent(wiki, title, key, tries=8):
    """Retorna (url,w,h) do melhor render transparente, ou None."""
    cands = list_images(wiki, title, key)[:tries]
    best = None
    for f in cands:
        url, w, h = file_url(wiki, f)
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            raw = urllib.request.urlopen(req, timeout=40).read()
            im = Image.open(io.BytesIO(raw)).convert("RGBA")
        except Exception:
            continue
        a = np.asarray(im.split()[-1])
        tf = (a < 10).mean()
        W, H = im.size
        if tf < 0.12:            # nao e recorte limpo
            continue
        if max(W, H) < 300:      # muito pequeno
            continue
        portrait = 1.0 if H >= W else 0.6
        sc = tf * portrait * min(1.0, max(W, H) / 900)
        if best is None or sc > best[0]:
            best = (sc, url, W, H, f)
    if best:
        return best[1], best[2], best[3], best[4]
    return None


if __name__ == "__main__":
    WEAK = json.load(open("weak.json"))
    resolved = json.load(open("resolved.json"))
    for wiki, items in WEAK.items():
        for name, (title, key) in items.items():
            res = best_transparent(wiki, title, key)
            if res:
                url, w, h, fn = res
                resolved[wiki][name] = {"title": title, "url": url, "w": w, "h": h}
                print(f"  [{wiki}] {name:22s} -> {w}x{h}  {fn}")
            else:
                print(f"  [{wiki}] {name:22s} -> (nenhum render limpo achado)")
    json.dump(resolved, open("resolved.json", "w"), indent=2)
    print("resolved.json atualizado")
