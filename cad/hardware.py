"""Fasteners: simplified but recognisable models (screws, nuts, inserts, bushings)."""
import math
from build123d import *

Z_UP = (Align.CENTER, Align.CENTER, Align.MIN)


def orient(shape, axis):
    """Turn a shape built along +Z toward the given axis ('+x', '-x', '+y', '-y', '+z', '-z')."""
    rot = {
        "+z": Rot(0, 0, 0), "-z": Rot(180, 0, 0),
        "+y": Rot(-90, 0, 0), "-y": Rot(90, 0, 0),
        "+x": Rot(0, 90, 0), "-x": Rot(0, -90, 0),
    }[axis]
    return rot * shape


def socket_cap(d, length):
    """ISO 4762 socket head cap screw: head above z=0, shank toward -z."""
    hd, hk = 1.5 * d + 0.5, d
    head = Cylinder(hd / 2, hk, align=Z_UP)
    head = fillet(head.edges().group_by(Axis.Z)[-1], 0.3 * d / 3)
    sock = Pos(0, 0, hk - 0.55 * d) * extrude(RegularPolygon(0.45 * d, 6), amount=0.6 * d)
    head -= sock
    shank = Pos(0, 0, -length) * Cylinder(d / 2 * 0.95, length, align=Z_UP)
    return head + shank


def button_head(d, length):
    """ISO 7380 button head screw."""
    hd, hk = 1.9 * d, 0.55 * d
    head = Cylinder(hd / 2, hk, align=Z_UP)
    head = fillet(head.edges().group_by(Axis.Z)[-1], hk * 0.8)
    head -= Pos(0, 0, hk - 0.4 * d) * extrude(RegularPolygon(0.35 * d, 6), amount=0.5 * d)
    shank = Pos(0, 0, -length) * Cylinder(d / 2 * 0.95, length, align=Z_UP)
    return head + shank


def countersunk(d, length):
    """ISO 10642 countersunk screw: head flush below z=0."""
    hd = 2 * d
    head = Pos(0, 0, -d * 0.6) * Cone(d / 2, hd / 2, d * 0.6, align=Z_UP)
    head -= Pos(0, 0, -0.45 * d) * extrude(RegularPolygon(0.35 * d, 6), amount=0.5 * d)
    shank = Pos(0, 0, -length) * Cylinder(d / 2 * 0.95, length - d * 0.6, align=Z_UP)
    return head + shank


def grub(d, length):
    """ISO 4027-style grub screw with a nylon tip: socket end at z=0, tip toward -z."""
    g = Pos(0, 0, -length) * Cylinder(d / 2 * 0.95, length, align=Z_UP)
    g -= Pos(0, 0, -0.45 * d) * extrude(RegularPolygon(0.3 * d, 6), amount=d)
    return g


def hex_nut(d, af=None, h=None):
    af = af or {2.5: 5.0, 3: 5.5, 4: 7.0, 5: 8.0, 6: 10.0, 8: 13.0}[d]
    h = h or 0.8 * d
    n = extrude(RegularPolygon(af / 2 / math.cos(math.pi / 6), 6), amount=h)
    n = chamfer(n.edges().filter_by(GeomType.LINE).filter_by(Axis.Z, reverse=True), 0.3)
    n -= Cylinder(d / 2, h * 3)
    return n


def washer(d, od=None, t=None):
    od = od or 2 * d + 0.5
    t = t or max(0.5, d / 6)
    return Cylinder(od / 2, t, align=Z_UP) - Cylinder(d / 2 + 0.2, t * 3)


def heat_insert(d, length=None):
    """Brass heat-set threaded insert (Ruthex / CNC Kitchen style)."""
    length = length or {2.5: 4.0, 3: 5.7, 4: 8.1}[d]
    od = {2.5: 3.6, 3: 4.6, 4: 5.6}[d]
    ins = Cylinder(od / 2, length, align=Z_UP)
    for z in (length * 0.25, length * 0.65):
        ins -= Pos(0, 0, z) * (Cylinder(od / 2 + 1, length * 0.12, align=Z_UP) - Cylinder(od / 2 - 0.3, 5))
    ins -= Pos(0, 0, -1) * Cylinder(d / 2, length + 2, align=Z_UP)
    return ins


def bushing(d, od, length):
    """Sintered bronze self-lubricating bushing."""
    return Cylinder(od / 2, length, align=Z_UP) - Pos(0, 0, -1) * Cylinder(d / 2, length + 2, align=Z_UP)


def threaded_rod(d, length):
    rod = Cylinder(d / 2 * 0.97, length, align=Z_UP)
    return chamfer(rod.edges(), 0.5)


def insert_hole(d):
    """Design hole for a heat-set insert (diameter, depth)."""
    return {2.5: (3.4, 5.0), 3: (4.0, 6.5), 4: (5.0, 9.0)}[d]
