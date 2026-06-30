"""Audita: confirma que cada Pokemon resolve para a imagem numerada correta
(slug com o numero da Pokedex). Lista os que falham."""
import re
import urllib.request
import urllib.parse
from build import NAMES

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MD = re.compile(r'cdn\.supercoloring\.com/coloring/\d+/([a-z0-9-]+)-coloring-page-md\.png')


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")


def slugify(name):
    return name.lower().replace("'", "").replace(".", "").replace(" ", "-")


def resolve(name, dex):
    """Retorna (url_md, slug) exigindo prefixo do numero da dex. Senao None."""
    slug = slugify(name)
    pref = f"{dex:03d}-"
    for cand in [f"{slug}-pokemon", slug, f"{slug}-pokemon-1"]:
        try:
            html = get(f"https://www.supercoloring.com/coloring-pages/{cand}")
            for full in re.finditer(
                    r'(cdn\.supercoloring\.com/coloring/\d+/(' + pref + r'[a-z0-9-]+)-coloring-page)-md\.png', html):
                return "https://" + full.group(1) + "-original.png", full.group(2)
        except Exception:
            pass
    # busca exigindo prefixo da dex
    try:
        html = get("https://www.supercoloring.com/search?" + urllib.parse.urlencode({"q": f"{name} pokemon"}))
        for full in re.finditer(
                r'(cdn\.supercoloring\.com/coloring/\d+/(' + pref + r'[a-z0-9-]+)-coloring-page)-md\.png', html):
            return "https://" + full.group(1) + "-original.png", full.group(2)
    except Exception:
        pass
    return None, None


if __name__ == "__main__":
    bad = []
    for dex, name in enumerate(NAMES, start=1):
        url, slug = resolve(name, dex)
        if not url:
            bad.append((dex, name))
            print(f"  {dex:3d} {name:14s} -> SEM NUMERADO")
    print(f"\nFalham (precisam de outra fonte): {len(bad)}")
    print(", ".join(f"{d:03d} {n}" for d, n in bad))
