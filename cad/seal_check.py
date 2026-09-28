"""Light-seal check for the two sliding interfaces, measured on the velvet.

For each interface (body / Y plate, Y plate / lens panel) the two faces are sliced just inside each
part. The seal is where both faces are solid AND the velvet lies between them (V1 is stuck on the
body, V2 on the Y plate, with two 7 mm discs over the rise-turret screws). Light reaches the film
through the openings; the seal width is the shortest distance from the openings to the edge of that
band, i.e. how far light has to creep along the velvet. The whole shift range is swept in 5 mm steps.
"""
import sys
import numpy as np
import trimesh
from shapely.geometry import Point, Polygon
from shapely.affinity import translate
from shapely.ops import unary_union
from params import *
import parts as P

MIN_SEAL = 4.6
STEP = 5


def mesh(shape):
    vs, fs = shape.tessellate(0.05, 0.2)
    return trimesh.Trimesh(np.array([(v.X, v.Y, v.Z) for v in vs]), np.array(fs), process=True)


def section(m, z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    planar, to3d = s.to_2D()
    out = []
    for p in planar.polygons_full:
        ext = trimesh.transform_points(np.column_stack([np.array(p.exterior.coords), np.zeros(len(p.exterior.coords))]), to3d)[:, :2]
        holes = [trimesh.transform_points(np.column_stack([np.array(r.coords), np.zeros(len(r.coords))]), to3d)[:, :2]
                 for r in p.interiors]
        out.append(Polygon(ext, holes))
    return unary_union(out)


def opening_at(poly, cx, cy):
    """The hole of a face that contains the optical axis (the light opening)."""
    for g in getattr(poly, "geoms", [poly]):
        for r in g.interiors:
            h = Polygon(r)
            if h.contains(Point(cx, cy)):
                return h
    raise ValueError("no opening around the axis")


def face2d(face):
    """build123d face (XY plane) to shapely."""
    polys = []
    for f in face.faces():
        outer = [(v.X, v.Y) for v in f.outer_wire().positions(np.linspace(0, 1, 400))]
        inner = [[(v.X, v.Y) for v in w.positions(np.linspace(0, 1, 200))] for w in f.inner_wires()]
        polys.append(Polygon(outer, inner))
    return unary_union(polys)


def width(contact, light):
    # close slivers left by the tessellation where two outlines meet (0.05 mm), then measure
    region = unary_union([contact, light]).buffer(0.05).buffer(-0.05)
    return light.buffer(-0.01).distance(region.boundary)


if __name__ == "__main__":
    body = section(mesh(P.body_part()), BODY_Z1 - 0.05)
    yp = P.y_plate_part() + P.y_turret()                 # the turret is screwed tight to the plate rear
    ym = mesh(yp)
    y_rear, y_front = section(ym, YP_Z0 + 0.05), section(ym, YP_Z1 - 0.05)
    # the two rise-turret counterbores are closed by the screw heads and a 7 mm velvet disc on each
    discs = unary_union([Point(x, y).buffer(3.45) for x, y in P.Y_TURRET_SCREWS])
    y_front = unary_union([y_front, discs])
    x_rear = section(mesh(P.x_plate_part()), XP_Z0 + 0.05)
    v1 = face2d(P.velvet_body_outline())
    v2 = unary_union([face2d(P.velvet_yplate_outline()), discs])
    b_open, yr_open = opening_at(body, 0, 0), opening_at(y_rear, 0, 0)
    yf_open, x_open = opening_at(y_front, 0, 0), opening_at(x_rear, 0, 0)
    v1_win, v2_win = opening_at(v1, 0, 0), opening_at(v2, 0, 0)     # inside the velvet window = inside the camera
    worst = (99.0, None)
    rng = range(-int(SHIFT_X), int(SHIFT_X) + 1, STEP)
    for sy in range(-int(FALL), int(RISE) + 1, STEP):
        for sx in rng:
            c1 = body.intersection(translate(y_rear, 0, sy)).intersection(v1)
            w1 = width(c1, unary_union([b_open, v1_win, translate(yr_open, 0, sy)]))
            c2 = translate(y_front, 0, sy).intersection(translate(x_rear, sx, sy)).intersection(translate(v2, 0, sy))
            w2 = width(c2, unary_union([translate(yf_open, 0, sy), translate(v2_win, 0, sy), translate(x_open, sx, sy)]))
            for w, name in ((w1, "body/Y plate"), (w2, "Y plate/lens panel")):
                if w < worst[0]:
                    worst = (w, f"{name} at x {sx:+d} y {sy:+d}")
    print(f"narrowest velvet seal {worst[0]:.2f} mm, {worst[1]} (minimum {MIN_SEAL}; swept every {STEP} mm)")
    sys.exit(0 if worst[0] >= MIN_SEAL else 1)
