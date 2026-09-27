"""Letter a callout render: PNG with alpha + projected points (JSON) -> JPG on white with labels.

python letter.py <out_dir> <render.png> [...]   (the JSON sits next to each PNG)
"""
import json, sys, pathlib
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/HelveticaNeue.ttc"
RED = (190, 22, 28)
INK = (40, 40, 42)
GREY = (120, 120, 124)


def font(size, bold=True):
    return ImageFont.truetype(FONT, size, index=1 if bold else 0)


def spread(labels, lo, hi, gap):
    """Push labels apart along y (sorted), keeping them inside [lo, hi]."""
    labels.sort(key=lambda l: l["y"])
    for i in range(1, len(labels)):
        labels[i]["y"] = max(labels[i]["y"], labels[i - 1]["y"] + gap)
    over = labels[-1]["y"] - hi if labels else 0
    if over > 0:
        for l in labels:
            l["y"] -= over
        for i in range(len(labels) - 2, -1, -1):
            labels[i]["y"] = min(labels[i]["y"], labels[i + 1]["y"] - gap)
    for l in labels:
        l["y"] = max(lo, l["y"])


def letter(png, out_dir):
    data = json.load(open(png.with_suffix(".json")))
    im = Image.open(png).convert("RGBA")
    W, Hh = im.size
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    x0, y0, x1, y1 = im.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    cx = (x0 + x1) / 2
    s = W / 1600
    R, gap, reach = 27 * s, 70 * s, 90 * s
    left, right = [], []
    for lab in data["labels"]:
        px = lab["px"]
        mx = sum(p[0] for p in px) / len(px)
        my = sum(p[1] for p in px) / len(px)
        l = {"t": lab["letter"], "px": px, "y": my}
        (left if mx < cx else right).append(l)
    for side, xs in ((left, max(60 * s, x0 - reach)), (right, min(W - 60 * s, x1 + reach))):
        spread(side, 110 * s, Hh - 60 * s, gap)
        for l in side:
            l["x"] = xs
    d = ImageDraw.Draw(bg)
    for l in left + right:                           # leaders: white halo, then ink
        for p in l["px"]:
            d.line([(l["x"], l["y"]), tuple(p)], fill=(255, 255, 255), width=int(7 * s))
    for l in left + right:
        for p in l["px"]:
            d.line([(l["x"], l["y"]), tuple(p)], fill=INK, width=max(2, int(2.4 * s)))
            r = 6.5 * s
            d.ellipse([p[0] - r - 2 * s, p[1] - r - 2 * s, p[0] + r + 2 * s, p[1] + r + 2 * s], fill=(255, 255, 255))
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=RED)
    f = font(int(30 * s))
    for l in left + right:
        w = max(2 * R, d.textlength(l["t"], font=f) + 26 * s)
        box = [l["x"] - w / 2, l["y"] - R, l["x"] + w / 2, l["y"] + R]
        d.rounded_rectangle(box, radius=R, fill=RED)
        d.text((l["x"], l["y"] + 1 * s), l["t"], font=f, fill=(255, 255, 255), anchor="mm")
    d.text((50 * s, 50 * s), data["title"], font=font(int(34 * s)), fill=INK, anchor="lm")
    dst = pathlib.Path(out_dir) / (png.stem.replace("cal_", "") + ".jpg")
    bg.convert("RGB").save(dst, quality=88, optimize=True, progressive=True)
    print(dst, dst.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    for p in sys.argv[2:]:
        letter(pathlib.Path(p), out)
