"""Light-seal check for the sliding interfaces.

For each pair of plates that slide face to face (body/Y plate, Y plate/lens panel) and for each
shift case, the faces are sliced just inside each part. The contact band is where both faces are
solid; light can only reach the film through the openings. The seal width is the shortest
distance from the openings to the edge of the contact band (an outer edge, a channel, a screw
counterbore...). Light has to travel at least that far along the velvet to get in.
"""
import sys
import numpy as np
import trimesh
from shapely.geometry import Point
from shapely.ops import unary_union
from params import *
import parts as P
from build123d import Pos

MIN_SEAL = 4.0


def mesh(shape):
    vs, fs = shape.tessellate(0.05, 0.2)
    return trimesh.Trimesh(np.array([(v.X, v.Y, v.Z) for v in vs]), np.array(fs), process=True)


def section(m, z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return None
    planar, to3d = s.to_2D()
    polys = [p for p in planar.polygons_full]
    # back to world XY (to_2D may translate/rotate)
    out = []
    for p in polys:
        coords = np.array(p.exterior.coords)
        pts = trimesh.transform_points(np.column_stack([coords, np.zeros(len(coords))]), to3d)[:, :2]
        holes = []
        for r in p.interiors:
            c = np.array(r.coords)
            holes.append(trimesh.transform_points(np.column_stack([c, np.zeros(len(c))]), to3d)[:, :2])
        from shapely.geometry import Polygon
        out.append(Polygon(pts, holes))
    return unary_union(out)


def opening_at(poly, cx, cy):
    """The hole of the face that contains the optical axis (the light opening)."""
    from shapely.geometry import Polygon
    for g in getattr(poly, "geoms", [poly]):
        for r in g.interiors:
            h = Polygon(r)
            if h.contains(Point(cx, cy)):
                return h
    return None


def seal_width(lower, lower_z, upper, upper_z, lower_c, upper_c):
    a = section(lower, lower_z)
    b = section(upper, upper_z)
    contact = a.intersection(b)
    light = unary_union([opening_at(a, *lower_c), opening_at(b, *upper_c)])
    region = unary_union([contact, light])
    return light.distance(region.boundary) if not light.is_empty else 0.0, contact.area


if __name__ == "__main__":
    body = mesh(P.body_part())
    # the turret is screwed tight against the plate rear, so its two screw holes are blind: filled here
    yp0 = P.y_plate_part() + P.y_turret()
    for x, y in P.Y_TURRET_SCREWS:
        yp0 = yp0 + P.cyl_z(3.1, YP_Z0, YP_Z1, x, y)
    xp0 = P.x_plate_part()
    cases = [(0, 0), (SHIFT_X, RISE), (-SHIFT_X, -FALL), (SHIFT_X, -FALL), (-SHIFT_X, RISE)]
    worst = 99.0
    for sx, sy in cases:
        yp = mesh(Pos(0, sy, 0) * yp0)
        xp = mesh(Pos(sx, sy, 0) * xp0)
        w1, _ = seal_width(body, BODY_Z1 - 0.05, yp, YP_Z0 + 0.05, (0, 0), (0, sy))
        w2, _ = seal_width(yp, YP_Z1 - 0.05, xp, XP_Z0 + 0.05, (0, sy), (sx, sy))
        worst = min(worst, w1, w2)
        print(f"shift x={sx:+.0f} y={sy:+.0f}: body/Y seal {w1:5.1f} mm, Y/lens panel seal {w2:5.1f} mm")
    print(f"narrowest seal {worst:.1f} mm (minimum {MIN_SEAL})")
    sys.exit(0 if worst >= MIN_SEAL else 1)
