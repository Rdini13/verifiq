"""Baixa paginas de colorir REAIS (feitas a mao) de Dragon Ball do coloringlib,
com busca de reserva. Salva em db_line/<nome>.png."""
import os
import re
import json
import time
import urllib.request
import urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "db_line")
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# nome -> (slug coloringlib, palavra-chave no nome do arquivo)
SLUGS = {
    "Goku": ("dragon-ball-z-goku", "goku"),
    "Vegeta": ("dragon-ball-z-vegeta", "vegeta"),
    "Gohan": ("dragon-ball-z-son-gohan", "gohan"),
    "Piccolo": ("dragon-ball-z-piccolo", "piccolo"),
    "Krillin": ("dragon-ball-z-krillin", "krillin"),
    "Trunks": ("dragon-ball-z-future-trunks", "trunks"),
    "Goten": ("dragon-ball-z-goten", "goten"),
    "Master Roshi": ("dragon-ball-z-master-roshi", "roshi"),
    "Yamcha": ("dragon-ball-z-yamcha", "yamcha"),
    "Tien Shinhan": ("dragon-ball-z-tien-shinhan", "tien"),
    "Chiaotzu": ("dragon-ball-z-chiaotzu", "chiaotzu"),
    "Android 18": ("dragon-ball-z-android-18", "android-18"),
    "Android 17": ("dragon-ball-z-android-17", "android-17"),
    "Frieza": ("dragon-ball-z-frieza", "frieza"),
    "Cell": ("dragon-ball-z-cell", "cell"),
    "Majin Buu": ("dragon-ball-z-majin-boo", "boo"),
    "Broly": ("dragon-ball-z-broly", "broly"),
    "Beerus": ("beerus-from-dragon-ball", "beerus"),
    "Videl": ("dragon-ball-z-videl", "videl"),
    "Shenron": ("dragon-ball-z-shenron", "shenron"),
    "Nappa": ("dragon-ball-z-nappa", "nappa"),
}
# animecoloringpages (URL direta de imagem) - tracos bem fortes
ANIME_CP = {
    "Mestre_Kaio": "https://animecoloringpages.com/wp-content/uploads/2023/03/King-Kai-Dragon-Ball-Z.jpg",
    "Bardock": "https://animecoloringpages.com/wp-content/uploads/2021/10/bardock-3.jpg",
    "Mr_Satan": "https://animecoloringpages.com/wp-content/uploads/2021/10/mr.-satan-from-dragon-ball-z.jpg",
    "Dabura": "https://animecoloringpages.com/wp-content/uploads/2021/10/dabura-1.jpg",
}
# bouinbouin: colecao numerada. Usada para quem o coloringlib nao tem
# (Bardock, Mr. Satan) ou rotula errado (Bulma -> era a Pan no coloringlib).
# As imagens "n" trazem uma faixa de marca-dagua no rodape, que recortamos.
BOUIN = {
    "Bulma": "1710-dragon-ball-bulma",
    "Goku_Crianca": "1707-dragon-ball-young-son-goku",
}
BOUIN_URL = "https://bouinbouin.com/images/coloring/dragon-ball/n/{}-coloring-page.jpg"
IMG = re.compile(r'https://coloringlib\.com/wp-content/uploads/[^" ]*?-coloring\.(?:jpg|png|jpeg)')


def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25).read().decode("utf-8", "ignore")


def imgs_on(slug):
    html = get(f"https://coloringlib.com/dragon-ball-z/{slug}/")
    out = [i for i in IMG.findall(html) if not re.search(r"-\d+x\d+", i)]
    # paginas inexistentes devolvem a categoria inteira (muitas imagens, sem match do slug)
    return out, html


def pick(slug, kw):
    out, _ = imgs_on(slug)
    base = slug.rsplit("/", 1)[-1]
    for i in out:                                   # imagem cujo arquivo == slug
        if i.lower().endswith(base + "-coloring.jpg") or i.lower().endswith(base + "-coloring.png"):
            return i
    for i in out:                                   # senao, contem a keyword (sem grupos)
        n = i.lower()
        if kw in n and " " not in n and "-vs-" not in n and "-and-" not in n:
            return i
    return None


def search_char(name):
    kw = name.lower().replace(".", "").split()[-1]
    try:
        html = get("https://coloringlib.com/?" + urllib.parse.urlencode({"s": name + " dragon ball"}))
        slugs = re.findall(r"https://coloringlib\.com/dragon-ball-z/([a-z0-9-]+)/", html)
        for slug in dict.fromkeys(slugs):
            if kw in slug:
                u = pick(slug, kw)
                if u:
                    return u
    except Exception:
        pass
    return None


def download(name, url):
    dst = os.path.join(OUT, name.replace(" ", "_").replace(".", "") + ".png")
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
    from PIL import Image
    import io
    Image.open(io.BytesIO(data)).convert("RGB").save(dst)
    return dst


def main():
    ok, missing = [], []
    for name, (slug, kw) in SLUGS.items():
        try:
            u = pick(slug, kw)
            if u:
                download(name, u)
                ok.append(name)
                print(f"  {name:16s} ok  {u.split('/')[-1]}")
            else:
                missing.append(name)
                print(f"  {name:16s} -> sem imagem")
        except Exception as e:
            missing.append(name)
            print(f"  {name:16s} -> ERRO {e}")
        time.sleep(0.2)
    for name, idslug in BOUIN.items():
        try:
            data = urllib.request.urlopen(
                urllib.request.Request(BOUIN_URL.format(idslug), headers=UA), timeout=30).read()
            from PIL import Image
            import io
            im = Image.open(io.BytesIO(data)).convert("RGB")
            im = im.crop((0, 0, im.width, im.height - 44))  # remove marca-dagua do rodape
            im.save(os.path.join(OUT, name.replace(" ", "_").replace(".", "") + ".png"))
            ok.append(name)
            print(f"  {name:16s} ok (bouinbouin)")
        except Exception as e:
            missing.append(name)
            print(f"  {name:16s} -> ERRO bouinbouin {e}")
    for name, url in ANIME_CP.items():
        try:
            from PIL import Image
            import io
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
            Image.open(io.BytesIO(data)).convert("RGB").save(
                os.path.join(OUT, name.replace(" ", "_").replace(".", "") + ".png"))
            ok.append(name)
            print(f"  {name:16s} ok (animecoloringpages)")
        except Exception as e:
            missing.append(name)
            print(f"  {name:16s} -> ERRO {e}")

    print(f"\nOK: {len(ok)} | Sem fonte: {missing}")
    json.dump({"ok": ok, "missing": missing}, open(os.path.join(BASE, "db_status.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
