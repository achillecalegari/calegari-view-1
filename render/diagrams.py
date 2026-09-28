"""Flat diagrams for docs/calibration.md, in the style of the rendered figures.

python diagrams.py   writes docs/img/cal/c_film_plane.jpg, c_tape_test.jpg, c_limits.jpg
"""
import math, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "img" / "cal"
OUT.mkdir(parents=True, exist_ok=True)
FONT = "/System/Library/Fonts/HelveticaNeue.ttc"
font_manager.fontManager.addfont(FONT)
plt.rcParams.update({"font.family": font_manager.FontProperties(fname=FONT).get_name(), "font.size": 15,
                     "font.weight": "bold", "axes.edgecolor": "#28282a", "text.color": "#28282a"})
RED, INK, GREY, LIGHT = "#be161c", "#28282a", "#96969a", "#e6e6e8"


def canvas(title, w=16, h=12):
    f = plt.figure(figsize=(w / 2, h / 2), dpi=200)
    f.text(0.03, 0.955, title, fontsize=17, weight="bold", color=INK, va="center")
    return f


def arrow(ax, a, b, col=INK, both=True, lw=1.6):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="<|-|>" if both else "-|>", mutation_scale=14, color=col, lw=lw,
                                 shrinkA=0, shrinkB=0))


def save(f, name):
    p = OUT / name
    f.savefig(p, dpi=200, facecolor="white", pil_kwargs={"quality": 88, "optimize": True, "progressive": True})
    plt.close(f)
    print(p)


def film_plane():
    f = canvas("The film and the ground glass must sit at the same depth")
    for i, (title, film) in enumerate((("Film back, in section", True), ("Ground glass, in section", False))):
        ax = f.add_axes([0.06 + i * 0.48, 0.08, 0.42, 0.78])
        ax.set_xlim(-6, 16); ax.set_ylim(-2, 26); ax.axis("off")
        ax.text(5, 25, title, ha="center", fontsize=15, color=INK)
        # nose face: the reference plane, on the camera's seat
        ax.add_patch(Rectangle((-4, 2), 4, 20, color="#3a3a3c"))
        ax.plot([0, 0], [0, 24], color=RED, lw=1.4, ls=(0, (6, 4)))
        ax.text(0.4, 0.4, "nose face = camera seat", ha="left", fontsize=12, color=RED)
        ax.text(-2, 12, "camera", ha="center", va="center", rotation=90, fontsize=12, color="white")
        if film:
            ax.add_patch(Rectangle((0, 3), 6.2, 2.2, color=GREY))                  # outer rails
            ax.add_patch(Rectangle((0, 18.8), 6.2, 2.2, color=GREY))
            ax.add_patch(Rectangle((0, 5.6), 4.75, 1.2, color="#5a5a5e"))          # inner rails
            ax.add_patch(Rectangle((0, 17.2), 4.75, 1.2, color="#5a5a5e"))
            ax.plot([4.75, 4.75], [5.6, 18.4], color=INK, lw=3.0)                  # emulsion
            ax.add_patch(Rectangle((4.9, 5.0), 0.5, 14.0, color="#b8b8bc"))        # film and paper
            ax.add_patch(Rectangle((6.4, 3), 1.2, 18, color=LIGHT))                # pressure plate
            ax.text(8.2, 12, "film, emulsion\nagainst the inner rails", fontsize=12, va="center")
            ax.text(8.2, 4.1, "outer rails: paper", fontsize=12, color=GREY, va="center")
        else:
            ax.add_patch(Rectangle((0, 3), 4.75, 18, color=LIGHT))
            ax.plot([4.75, 4.75], [3, 21], color=INK, lw=3.0)
            for y in [4 + k * 0.8 for k in range(21)]:
                ax.plot([4.75, 5.15], [y, y + 0.4], color=INK, lw=0.8)
            ax.text(5.8, 12, "frosted surface", fontsize=12, va="center")
        arrow(ax, (0, 23), (4.75, 23))
        ax.text(2.4, 23.6, "4.75 mm", ha="center", fontsize=13)
    f.text(0.5, 0.03, "Measure both with the caliper's depth rod from the nose face: they must agree within 0.05 mm.",
           ha="center", fontsize=12, weight="normal", color=INK)
    save(f, "c_film_plane.jpg")


def tape_test():
    f = canvas("The tape measure test, seen from above")
    ax = f.add_axes([0.05, 0.05, 0.9, 0.85]); ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-70, 70); ax.set_ylim(-18, 128)
    ax.add_patch(Rectangle((-9, -12), 18, 12, color="#2a2a2c"))                    # camera
    ax.add_patch(Rectangle((-4, 0), 8, 5, color="#2a2a2c"))                        # lens
    ax.text(12, -7, "camera, level, lens at its widest aperture", fontsize=12, va="center")
    ax.plot([0, 0], [5, 125], color=GREY, lw=1.0, ls=(0, (5, 4)))
    ax.text(1.5, 30, "lens axis", fontsize=11, color=GREY)
    c, s = math.cos(math.radians(45)), math.sin(math.radians(45))
    L = 40
    ax.add_patch(Polygon([(-L * c - 1.2 * s, 100 - L * s + 1.2 * c), (L * c - 1.2 * s, 100 + L * s + 1.2 * c),
                          (L * c + 1.2 * s, 100 + L * s - 1.2 * c), (-L * c + 1.2 * s, 100 - L * s - 1.2 * c)], color=LIGHT))
    for k in range(-L, L + 1, 5):
        x, y = k * c, 100 + k * s
        big = k % 10 == 0
        ax.plot([x - (2.2 if big else 1.2) * s, x], [y + (2.2 if big else 1.2) * c, y], color=INK, lw=1.2 if big else 0.8)
        if big:
            ax.text(x - 4.6 * s, y + 4.6 * c, f"{100 + k}", fontsize=10, ha="center", va="center", rotation=45, weight="normal")
    ax.plot([0], [100], "o", color=RED, ms=9)
    ax.annotate("focus here on the ground glass:\nthe 100 cm mark, 1 m from the lens", (0, 100), (18, 68),
                fontsize=12, arrowprops=dict(arrowstyle="-", color=INK, lw=1.2))
    arrow(ax, (-30, 5), (-30, 100))
    ax.text(-32, 52, "1 m", ha="right", fontsize=13, va="center")
    ax.text(-58, 118, "tape measure at 45 degrees", fontsize=12)
    save(f, "c_tape_test.jpg")


def limits():
    f = canvas("How far the lens can move, with the corners clean")
    ax = f.add_axes([0.02, 0.1, 0.58, 0.8]); ax.set_aspect("equal")
    ax.set_xlim(-30, 30); ax.set_ylim(-30, 30)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_position(("data", 0)); ax.spines["bottom"].set_position(("data", 0))
    ax.set_xticks([-25, -10, 10, 25]); ax.set_yticks([-25, -10, 10, 25])
    ax.tick_params(labelsize=10, colors=INK)
    ax.add_patch(Rectangle((-25, -25), 50, 50, facecolor="white", edgecolor=GREY, hatch="///", lw=0.8))
    ax.add_patch(Rectangle((-22, -22), 44, 44, facecolor=LIGHT, edgecolor=INK, lw=1.6))
    ax.add_patch(Rectangle((-20, -20), 40, 40, facecolor="none", edgecolor=RED, lw=1.6, ls=(0, (6, 4))))
    ax.plot([-25, 25], [0, 0], color=INK, lw=5, solid_capstyle="butt")
    ax.plot([0, 0], [-25, 25], color=INK, lw=5, solid_capstyle="butt")
    ax.text(26, 1.2, "shift", fontsize=12); ax.text(1.0, 27, "rise", fontsize=12)
    ax.text(-19.2, -18.8, "20 + 20", fontsize=10, color=RED); ax.text(-21.2, -21.2, "22 + 22", fontsize=10, color=INK)
    kw = dict(fontsize=12, va="center")
    f.text(0.62, 0.78, "One movement at a time:\nclean to 25 mm, at f/8 and f/22,\nfrom infinity to about 0.9 m", **kw)
    f.text(0.62, 0.6, "Grey square: rise and shift\ntogether, clean at infinity, f/22", **kw)
    f.text(0.62, 0.45, "Red dashed square: the same\nat f/8", color=RED, **kw)
    f.text(0.62, 0.3, "Hatched corners: check them\non the ground glass (focusing\ncloser makes them worse)", color=INK, **kw)
    f.text(0.03, 0.03, "Ray trace of the camera's own openings (cad/optics_check.py). The lens's image circle can be the tighter limit.",
           fontsize=11, weight="normal")
    save(f, "c_limits.jpg")


if __name__ == "__main__":
    film_plane()
    tape_test()
    limits()
