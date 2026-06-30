"""Convert official Pokemon artwork into clean coloring-book line art."""
import sys
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageChops


def make_lineart(src_path, out_path, size=900):
    img = Image.open(src_path).convert("RGBA")
    # composite on white background
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(bg, img).convert("RGB")

    # upscale a bit for cleaner edges, then we draw at target size
    comp = comp.resize((size, size), Image.LANCZOS)

    gray = comp.convert("L")

    # --- internal edges via "pencil"/XDoG-like difference of gaussians ---
    g1 = gray.filter(ImageFilter.GaussianBlur(1.0))
    g2 = gray.filter(ImageFilter.GaussianBlur(2.6))
    a1 = np.asarray(g1, dtype=np.float32)
    a2 = np.asarray(g2, dtype=np.float32)
    dog = a1 - a2  # bright where edges are
    dog_norm = np.clip(dog * 6.0, 0, 255)
    edges = dog_norm.astype(np.uint8)
    edges_img = Image.fromarray(edges)  # white edges on black
    # threshold edges
    edges_img = edges_img.point(lambda p: 255 if p > 24 else 0)

    # --- outer silhouette outline from alpha ---
    alpha = img.resize((size, size), Image.LANCZOS).split()[-1]
    mask = alpha.point(lambda p: 255 if p > 40 else 0)
    # outline = dilation - erosion of the mask
    dil = mask.filter(ImageFilter.MaxFilter(5))
    ero = mask.filter(ImageFilter.MinFilter(5))
    outline = ImageChops.subtract(dil, ero)  # white outline on black

    # combine internal edges + silhouette outline (both white-on-black)
    combined = ImageChops.lighter(edges_img, outline)

    # thicken slightly so lines print well
    combined = combined.filter(ImageFilter.MaxFilter(3))

    # invert: black lines on white
    line = ImageOps.invert(combined)

    # only keep edges inside the silhouette (plus the outline itself)
    # so background stays clean white
    inside = mask.filter(ImageFilter.MaxFilter(5))
    inside_np = np.asarray(inside)
    line_np = np.asarray(line).copy()
    line_np[inside_np == 0] = 255  # force outside-silhouette to white
    # but keep the outline (outline already within dilated mask) -> ok
    out = Image.fromarray(line_np)
    out.save(out_path)
    return out


if __name__ == "__main__":
    for n in [1, 4, 7, 25, 150]:
        make_lineart(f"art/{n}.png", f"test/{n}_line.png")
        print("done", n)
