"""Vignetting check: rays from the lens exit pupil to the four corners of the 6x7 frame, through the
real parts at each shift. Exit code 1 if a case in REQUIRED is clipped.

The pupil of a symmetric wide angle sits near its rear principal plane, about FFD - 5 mm in front of
the film at infinity (z 65 here; PUPIL_Z in params.py is a looser value used only to size openings).
Every printed and bought part between the pupil and the film is sliced every 0.25 mm; a ray is lost
if it passes through solid anywhere. The result is the share of the pupil that reaches each corner.

python optics_check.py
"""
import sys
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely.prepared import prep
from params import *
from assembly import assemble

PUPIL = 65.0
CORNERS = [(sx * FILM_W / 2, sy * FILM_H / 2) for sx in (-1, 1) for sy in (-1, 1)]
SKIP = ("lens", "rb_", "velvet", "felt", "inlay", "oring", "knob", "rod", "grub", "screw", "insert", "nut", "vial",
        "bush", "plunger", "spring", "top_handle", "arca_", "way_", "gib_", "focus_ring")   # all outside the light path
# (sx, sy, f-number, pupil z, minimum share of the pupil at the worst corner)
# pupil 65 = infinity; 70 = about 5 mm of helicoid extension (about 0.9 m); 72.5 = the closest focus
# (about 0.7 m); 62 = a lens whose pupil sits 3 mm further back. The helicoid's rear stub (61 mm bore,
# 5.2 mm behind the lens panel front) is the opening that limits combined movements.
SIGNS = ((1, 1), (-1, -1), (1, -1), (-1, 1))
REQUIRED = ([(25, 0, 22, 65, 0.99), (-25, 0, 22, 65, 0.99), (0, 25, 22, 65, 0.99), (0, -25, 22, 65, 0.99),
             (25, 0, 8, 65, 0.95), (0, 25, 8, 65, 0.95), (-25, 0, 22, 62, 0.99), (0, -25, 22, 62, 0.99),
             (24, 0, 22, 70, 0.99), (-24, 0, 22, 70, 0.99), (0, 25, 22, 70, 0.99), (0, -25, 22, 70, 0.99),
             (20, 0, 22, 72.5, 0.99), (-20, 0, 22, 72.5, 0.99), (0, 24, 22, 72.5, 0.99), (0, -24, 22, 72.5, 0.99)]
            + [(a * 19, b * 19, 22, 65, 0.99) for a, b in SIGNS]
            + [(a * 17, b * 17, 8, 65, 0.95) for a, b in SIGNS]
            + [(a * 14, b * 14, 22, 70, 0.99) for a, b in SIGNS]
            + [(a * 13, b * 13, 22, 72.5, 0.99) for a, b in SIGNS])
INFO = [(20, 20, 22, 65), (18, 18, 8, 65), (16, 16, 22, 70), (14, 14, 22, 72.5), (25, 0, 22, 70), (25, 0, 22, 72.5)]


def mesh(shape):
    vs, fs = shape.tessellate(0.05, 0.2)
    return trimesh.Trimesh(np.array([(v.X, v.Y, v.Z) for v in vs]), np.array(fs), process=True)


def slices(meshes, zs):
    out = {}
    for z in zs:
        polys = []
        for m in meshes:
            if not (m.bounds[0][2] < z < m.bounds[1][2]):
                continue
            s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
            if s is None:
                continue
            planar, to3d = s.to_2D()
            try:
                for p in planar.polygons_full:
                    ext = trimesh.transform_points(np.column_stack([np.array(p.exterior.coords), np.zeros(len(p.exterior.coords))]), to3d)[:, :2]
                    holes = [trimesh.transform_points(np.column_stack([np.array(r.coords), np.zeros(len(r.coords))]), to3d)[:, :2]
                             for r in p.interiors]
                    polys.append(Polygon(ext, holes).buffer(0))
                continue
            except ValueError:
                pass
            # fallback: even-odd fill of every closed loop
            region = None
            for d in planar.discrete:
                if len(d) < 4:
                    continue
                pts = trimesh.transform_points(np.column_stack([d, np.zeros(len(d))]), to3d)[:, :2]
                loop = Polygon(pts).buffer(0)
                region = loop if region is None else region.symmetric_difference(loop)
            if region is not None and not region.is_empty:
                polys.append(region)
        out[z] = prep(unary_union(polys)) if polys else None
    return out


def pupil_points(radius, n=9):
    pts = []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = i / n * radius, j / n * radius
            if x * x + y * y <= radius * radius:
                pts.append((x, y))
    return pts


def share(sx, sy, fnum, cache, pupil=PUPIL):
    key = (sx, sy)
    if key not in cache:
        items = [i for i in assemble(sx, sy, back=False) if not i.name.startswith(SKIP)]
        zs = np.concatenate([np.arange(1.01, 34.0, 1.0), np.arange(34.01, 36.1, 0.25), np.arange(36.11, 39.0, 0.1),
                             np.arange(39.01, 47.0, 0.25), np.arange(47.01, 62.0, 1.0)])   # off the flat faces
        cache[key] = (slices([mesh(i.shape) for i in items], zs), zs)
    sl, zs = cache[key]
    pts = pupil_points(F_LENS / fnum / 2)
    worst = 1.0
    for cx, cy in CORNERS:
        ok = 0
        for px, py in pts:
            x0, y0 = sx + px, sy + py
            clear = True
            for z in zs:
                if z >= pupil:
                    break
                g = sl[z]
                if g is None:
                    continue
                t = z / pupil
                x, y = cx + (x0 - cx) * t, cy + (y0 - cy) * t
                if g.contains(Point(x, y)):
                    clear = False
                    break
            ok += clear
        worst = min(worst, ok / len(pts))
    return worst


if __name__ == "__main__":
    cache, fails = {}, 0
    for sx, sy, fnum, pz, need in REQUIRED:
        w = share(sx, sy, fnum, cache, pz)
        flag = "ok" if w >= need else "CLIPPED"
        fails += w < need
        print(f"shift x={sx:+3d} y={sy:+3d} f/{fnum:<2d} pupil z {pz:4.1f}: worst corner gets {w * 100:5.1f} % of the pupil  {flag}")
    for sx, sy, fnum, pz in INFO:
        w = share(sx, sy, fnum, cache, pz)
        print(f"(info) shift x={sx:+3d} y={sy:+3d} f/{fnum:<2d} pupil z {pz:4.1f}: worst corner {w * 100:5.1f} %")
    sys.exit(1 if fails else 0)
