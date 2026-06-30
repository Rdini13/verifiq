"""Gera paginas de colorir para os 150 primeiros Pokemon.

Para cada Pokemon: uma pagina A4 com numero+nome no topo, o desenho grande
em contorno (para colorir) e, embaixo, a arte colorida pequena como referencia.
Saida: PDF com 150 paginas + PNGs individuais.
"""
import os
import urllib.request
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageChops, ImageDraw, ImageFont
from scipy import ndimage

BASE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(BASE, "art")
PAGES = os.path.join(BASE, "pages")
os.makedirs(ART, exist_ok=True)
os.makedirs(PAGES, exist_ok=True)

NAMES = [
    "Bulbasaur", "Ivysaur", "Venusaur", "Charmander", "Charmeleon", "Charizard",
    "Squirtle", "Wartortle", "Blastoise", "Caterpie", "Metapod", "Butterfree",
    "Weedle", "Kakuna", "Beedrill", "Pidgey", "Pidgeotto", "Pidgeot", "Rattata",
    "Raticate", "Spearow", "Fearow", "Ekans", "Arbok", "Pikachu", "Raichu",
    "Sandshrew", "Sandslash", "Nidoran-F", "Nidorina", "Nidoqueen", "Nidoran-M",
    "Nidorino", "Nidoking", "Clefairy", "Clefable", "Vulpix", "Ninetales",
    "Jigglypuff", "Wigglytuff", "Zubat", "Golbat", "Oddish", "Gloom", "Vileplume",
    "Paras", "Parasect", "Venonat", "Venomoth", "Diglett", "Dugtrio", "Meowth",
    "Persian", "Psyduck", "Golduck", "Mankey", "Primeape", "Growlithe", "Arcanine",
    "Poliwag", "Poliwhirl", "Poliwrath", "Abra", "Kadabra", "Alakazam", "Machop",
    "Machoke", "Machamp", "Bellsprout", "Weepinbell", "Victreebel", "Tentacool",
    "Tentacruel", "Geodude", "Graveler", "Golem", "Ponyta", "Rapidash", "Slowpoke",
    "Slowbro", "Magnemite", "Magneton", "Farfetchd", "Doduo", "Dodrio", "Seel",
    "Dewgong", "Grimer", "Muk", "Shellder", "Cloyster", "Gastly", "Haunter",
    "Gengar", "Onix", "Drowzee", "Hypno", "Krabby", "Kingler", "Voltorb",
    "Electrode", "Exeggcute", "Exeggutor", "Cubone", "Marowak", "Hitmonlee",
    "Hitmonchan", "Lickitung", "Koffing", "Weezing", "Rhyhorn", "Rhydon",
    "Chansey", "Tangela", "Kangaskhan", "Horsea", "Seadra", "Goldeen", "Seaking",
    "Staryu", "Starmie", "Mr-Mime", "Scyther", "Jynx", "Electabuzz", "Magmar",
    "Pinsir", "Tauros", "Magikarp", "Gyarados", "Lapras", "Ditto", "Eevee",
    "Vaporeon", "Jolteon", "Flareon", "Porygon", "Omanyte", "Omastar", "Kabuto",
    "Kabutops", "Aerodactyl", "Snorlax", "Articuno", "Zapdos", "Moltres",
    "Dratini", "Dragonair", "Dragonite", "Mewtwo", "Mew",
]

ART_URL = ("https://raw.githubusercontent.com/PokeAPI/sprites/master/"
           "sprites/pokemon/other/official-artwork/{}.png")


def download(n):
    path = os.path.join(ART, f"{n}.png")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    for attempt in range(4):
        try:
            urllib.request.urlretrieve(ART_URL.format(n), path)
            return path
        except Exception as e:
            if attempt == 3:
                raise
    return path


def despeckle(line_img, min_area=14):
    """Remove pequenas manchas pretas isoladas (ruido)."""
    arr = np.asarray(line_img)
    black = arr < 128
    labeled, num = ndimage.label(black)
    if num == 0:
        return line_img
    sizes = ndimage.sum(np.ones_like(labeled), labeled, range(1, num + 1))
    remove = np.zeros(num + 1, dtype=bool)
    remove[1:] = sizes < min_area
    mask = remove[labeled]
    out = arr.copy()
    out[mask] = 255
    return Image.fromarray(out)


def make_lineart(src_path, size=1000):
    img = Image.open(src_path).convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(bg, img).convert("RGB").resize((size, size), Image.LANCZOS)
    gray = comp.convert("L")

    # bordas internas (diferenca de gaussianas)
    g1 = np.asarray(gray.filter(ImageFilter.GaussianBlur(1.0)), dtype=np.float32)
    g2 = np.asarray(gray.filter(ImageFilter.GaussianBlur(2.6)), dtype=np.float32)
    dog = np.clip((g1 - g2) * 6.0, 0, 255).astype(np.uint8)
    edges = Image.fromarray(dog).point(lambda p: 255 if p > 24 else 0)

    # contorno externo (silhueta a partir do alpha)
    alpha = img.resize((size, size), Image.LANCZOS).split()[-1]
    mask = alpha.point(lambda p: 255 if p > 40 else 0)
    outline = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)),
                                  mask.filter(ImageFilter.MinFilter(5)))

    combined = ImageChops.lighter(edges, outline).filter(ImageFilter.MaxFilter(3))
    line = ImageOps.invert(combined)

    inside = np.asarray(mask.filter(ImageFilter.MaxFilter(5)))
    line_np = np.asarray(line).copy()
    line_np[inside == 0] = 255
    line = Image.fromarray(line_np)
    return despeckle(line)


def colored_ref(src_path, size=300):
    img = Image.open(src_path).convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(bg, img).convert("RGB")
    return comp.resize((size, size), Image.LANCZOS)


# A4 a 150 DPI
PAGE_W, PAGE_H = 1240, 1754
F_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
F_LABEL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)


def build_page(n, name):
    src = download(n)
    line = make_lineart(src, size=1000)
    ref = colored_ref(src, size=300)

    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    draw = ImageDraw.Draw(page)

    # titulo: #001 Nome
    title = f"#{n:03d}  {name}"
    tb = draw.textbbox((0, 0), title, font=F_TITLE)
    draw.text(((PAGE_W - (tb[2] - tb[0])) / 2, 60), title, fill="black", font=F_TITLE)

    # desenho grande para colorir
    lw = 1050
    line_big = line.resize((lw, lw), Image.LANCZOS)
    page.paste(line_big, ((PAGE_W - lw) // 2, 200))

    # linha separadora
    draw.line([(120, 1300), (PAGE_W - 120, 1300)], fill=(200, 200, 200), width=2)

    # rotulo referencia
    lbl = "Referencia (colorido)"
    lb = draw.textbbox((0, 0), lbl, font=F_LABEL)
    draw.text(((PAGE_W - (lb[2] - lb[0])) / 2, 1330), lbl, fill=(90, 90, 90), font=F_LABEL)

    # referencia colorida pequena, com moldura
    rx = (PAGE_W - 300) // 2
    ry = 1390
    draw.rectangle([rx - 4, ry - 4, rx + 303, ry + 303], outline=(180, 180, 180), width=2)
    page.paste(ref, (rx, ry))

    page.save(os.path.join(PAGES, f"{n:03d}_{name}.png"))
    return page


def main():
    pages = []
    for i, name in enumerate(NAMES, start=1):
        pages.append(build_page(i, name))
        print(f"{i:3d}/150  {name}")
    out_pdf = os.path.join(BASE, "Pokemon_150_para_colorir.pdf")
    pages[0].save(out_pdf, "PDF", resolution=150.0, save_all=True,
                  append_images=pages[1:])
    print("PDF salvo em:", out_pdf)


if __name__ == "__main__":
    main()
