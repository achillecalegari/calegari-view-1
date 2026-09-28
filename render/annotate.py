"""Annotate a figure render: PNG with alpha + projected points (JSON next to it) -> JPG on white.

python annotate.py <out_dir> <render.png> [...]

The JSON (written by cad/figures.py, projected by render/white.py) holds:
  title
  labels  [{"text", "px": [[x, y], ...]}]   short texts (up to 3 characters) are red pills, longer ones plain
                                             words; a leader goes to each point (to the nearest one when
                                             there are more than three, the others get a dot)
  guides  [{"px": [a, b]}]                  grey dashed line from a part to where it goes
  lines   [{"px": [...], "style", "text"}]  overlays: arrow, arrow2 (both ends), dim (dimension), dash
"""
import json, math, sys, pathlib
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/HelveticaNeue.ttc"
RED = (190, 22, 28)
INK = (40, 40, 42)
GREY = (150, 150, 154)
WHITE = (255, 255, 255)


def font(size, bold=True):
    return ImageFont.truetype(FONT, int(size), index=1 if bold else 0)


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


def dashed(d, a, b, fill, width, dash, gap):
    L = math.dist(a, b)
    if L < 1:
        return
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    t = 0.0
    while t < L:
        t1 = min(L, t + dash)
        d.line([(a[0] + ux * t, a[1] + uy * t), (a[0] + ux * t1, a[1] + uy * t1)], fill=fill, width=width)
        t = t1 + gap


def head(d, a, b, size, fill):
    """Arrow head at b, pointing from a to b."""
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    p1 = (b[0] - size * math.cos(ang - 0.42), b[1] - size * math.sin(ang - 0.42))
    p2 = (b[0] - size * math.cos(ang + 0.42), b[1] - size * math.sin(ang + 0.42))
    d.polygon([b, p1, p2], fill=fill)


def annotate(png, out_dir):
    data = json.load(open(png.with_suffix(".json")))
    im = Image.open(png).convert("RGBA")
    W, Hh = im.size
    s = W / 1600
    bbox = im.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox() or (0, 0, W, Hh)
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1) / 2
    labels = data.get("labels", [])
    reach = 90 * s
    fw = font(27 * s)
    # words need room beside the object: widen the canvas on the side that needs it
    need_l = need_r = 0.0
    for lab in labels:
        t = lab["text"]
        force = t[0] if t[:1] in "<>" and len(t) > 1 else ""
        if len(t.lstrip("<>")) > 3:
            mx = sum(p[0] for p in lab["px"]) / len(lab["px"])
            w = fw.getlength(t.lstrip("<>")) + reach + 50 * s
            if force == "<" or (not force and mx < cx):
                need_l = max(need_l, w)
            else:
                need_r = max(need_r, w)
    pad_l = int(max(0, need_l - x0))
    pad_r = int(max(0, need_r - (W - x1)))
    pad_t = int(max(0, 105 * s - y0))                 # room for the title
    Hh = Hh + pad_t
    canvas = Image.new("RGBA", (W + pad_l + pad_r, Hh), WHITE + (255,))
    canvas.alpha_composite(im, (pad_l, pad_t))
    shift = lambda p: (p[0] + pad_l, p[1] + pad_t)
    x0, x1, cx = x0 + pad_l, x1 + pad_l, cx + pad_l
    CW = canvas.size[0]
    d = ImageDraw.Draw(canvas)

    for g in data.get("guides", []):                  # where each part goes
        a, b = shift(g["px"][0]), shift(g["px"][1])
        dashed(d, a, b, GREY, max(2, int(2.4 * s)), 11 * s, 8 * s)

    fl = font(24 * s)
    for ln in data.get("lines", []):                  # overlays
        pts = [shift(p) for p in ln["px"]]
        st = ln.get("style", "arrow")
        col = RED
        wdt = max(2, int((3.0 if st == "dim" else 4.5) * s))
        if st != "dash":
            d.line(pts, fill=WHITE, width=wdt + int(5 * s), joint="curve")
        if st == "dash":
            for a, b in zip(pts, pts[1:]):
                dashed(d, a, b, col, wdt, 12 * s, 9 * s)
        else:
            d.line(pts, fill=col, width=wdt, joint="curve")
        hs = (16 if st == "dim" else 24) * s
        if st in ("arrow", "arrow2", "dim"):
            head(d, pts[-2], pts[-1], hs, col)
        if st in ("arrow2", "dim"):
            head(d, pts[1], pts[0], hs, col)
        if ln.get("text"):
            i = len(pts) // 2
            mx, my = ((pts[i - 1][0] + pts[i][0]) / 2, (pts[i - 1][1] + pts[i][1]) / 2) if len(pts) % 2 == 0 else pts[i]
            ox, oy = ln.get("offset", (0, -34))
            tx, ty = mx + ox * s, my + oy * s
            tw = d.textlength(ln["text"], font=fl)
            d.rounded_rectangle([tx - tw / 2 - 10 * s, ty - 18 * s, tx + tw / 2 + 10 * s, ty + 18 * s], radius=8 * s, fill=WHITE)
            d.text((tx, ty), ln["text"], font=fl, fill=col, anchor="mm")

    R, gap = 27 * s, 70 * s
    left, right = [], []
    for lab in labels:
        px = [shift(p) for p in lab["px"]]
        mx = sum(p[0] for p in px) / len(px)
        my = sum(p[1] for p in px) / len(px)
        t = lab["text"]
        force = t[0] if t[:1] in "<>" and len(t) > 1 else ""
        t = t[1:] if force else t
        word = len(t) > 3
        l = {"t": t, "px": px, "y": my, "word": word}
        (left if (force == "<" or (not force and mx < cx)) else right).append(l)
    for side, xs in ((left, max(60 * s, x0 - reach)), (right, min(CW - 60 * s, x1 + reach))):
        spread(side, 110 * s, Hh - 50 * s, gap if not any(l["word"] for l in side) else 58 * s)
        for l in side:
            l["x"] = xs
            l["side"] = "l" if side is left else "r"
    every = left + right
    for l in every:                                   # which points get a leader
        if len(l["px"]) > 3:
            l["lead"] = [min(l["px"], key=lambda p: math.dist(p, (l["x"], l["y"])))]
        else:
            l["lead"] = l["px"]
    for l in every:                                   # leaders: white halo, then ink
        for p in l["lead"]:
            d.line([(l["x"], l["y"]), tuple(p)], fill=WHITE, width=int(7 * s))
    for l in every:
        for p in l["lead"]:
            d.line([(l["x"], l["y"]), tuple(p)], fill=INK, width=max(2, int(2.4 * s)))
        for p in l["px"]:
            r = 6.5 * s
            d.ellipse([p[0] - r - 2 * s, p[1] - r - 2 * s, p[0] + r + 2 * s, p[1] + r + 2 * s], fill=WHITE)
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=RED)
    fp = font(30 * s)
    for l in every:
        if l["word"]:
            anchor = "rm" if l["side"] == "l" else "lm"
            tx = l["x"] - 10 * s if l["side"] == "l" else l["x"] + 10 * s
            tw = d.textlength(l["t"], font=fw)
            bx0, bx1 = (tx - tw - 6 * s, tx + 6 * s) if l["side"] == "l" else (tx - 6 * s, tx + tw + 6 * s)
            d.rectangle([bx0, l["y"] - 17 * s, bx1, l["y"] + 17 * s], fill=WHITE)
            d.text((tx, l["y"]), l["t"], font=fw, fill=INK, anchor=anchor)
        else:
            w = max(2 * R, d.textlength(l["t"], font=fp) + 26 * s)
            box = [l["x"] - w / 2, l["y"] - R, l["x"] + w / 2, l["y"] + R]
            d.rounded_rectangle(box, radius=R, fill=RED)
            d.text((l["x"], l["y"] + 1 * s), l["t"], font=fp, fill=WHITE, anchor="mm")
    if data.get("title"):
        d.text((50 * s, 50 * s), data["title"], font=font(34 * s), fill=INK, anchor="lm")
    dst = pathlib.Path(out_dir) / (png.stem.replace("fig_", "") + ".jpg")
    canvas.convert("RGB").save(dst, quality=88, optimize=True, progressive=True)
    print(dst, dst.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    for p in sys.argv[2:]:
        annotate(pathlib.Path(p), out)
