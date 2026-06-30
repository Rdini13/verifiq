"""Resolve a imagem principal (render) de cada personagem no Fandom."""
import json
import urllib.parse
import urllib.request

UA = "coloring-book/1.0 (educational)"

WIKIS = {
    "dragonball": "https://dragonball.fandom.com",
    "naruto": "https://naruto.fandom.com",
    "onepiece": "https://onepiece.fandom.com",
}


def resolve(wiki, title):
    base = WIKIS[wiki]
    q = urllib.parse.urlencode({
        "action": "query", "titles": title, "prop": "pageimages",
        "piprop": "original", "format": "json", "redirects": "1",
    })
    req = urllib.request.Request(f"{base}/api.php?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    pages = data.get("query", {}).get("pages", {})
    for _, p in pages.items():
        orig = p.get("original")
        if orig and orig.get("source"):
            return orig["source"], orig.get("width"), orig.get("height")
    return None, None, None


if __name__ == "__main__":
    import sys
    targets = json.load(open(sys.argv[1]))
    out = {}
    for wiki, names in targets.items():
        out[wiki] = {}
        for disp, title in names:
            try:
                url, w, h = resolve(wiki, title)
            except Exception as e:
                url, w, h = None, None, None
            status = f"{w}x{h}" if url else "MISSING"
            print(f"  [{wiki}] {disp:24s} {status}")
            out[wiki][disp] = {"title": title, "url": url, "w": w, "h": h}
    json.dump(out, open(sys.argv[2], "w"), indent=2)
    print("saved", sys.argv[2])
