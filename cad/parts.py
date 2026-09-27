"""Calegari View 1: printed parts and bought-part envelopes.

Every function returns a build123d solid already placed in camera coordinates
(see params.py). Printed parts are built at the home position (no shift);
assembly.py moves them.
"""
import math
from build123d import *
from params import *
import hardware as hw
from hardware import Z_UP, orient

try:
    from bd_warehouse.thread import IsoThread
except Exception:  # pragma: no cover
    IsoThread = None

H = BODY / 2  # 74


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def sfillet(shape, edges, r):
    try:
        return fillet(edges, r)
    except Exception:
        return shape


def schamfer(shape, edges, r):
    try:
        return chamfer(edges, r)
    except Exception:
        return shape


def box_at(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))


def cyl_x(r, x0, x1, y, z):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, abs(x1 - x0))


def cyl_y(r, y0, y1, x, z):
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(r, abs(y1 - y0))


def cyl_z(r, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, min(z0, z1)) * Cylinder(r, abs(z1 - z0), align=Z_UP)


def slab(w, h, z0, z1, r=CORNER_R, edge=EDGE):
    s = extrude(Pos(0, 0, z0) * RectangleRounded(w, h, r), amount=z1 - z0)
    return sfillet(s, s.edges().filter_by(Plane.XY), edge)


def rect_loft(z0, half0, z1, half1, r=2.0):
    a = Pos(0, 0, z0) * RectangleRounded(2 * half0[0], 2 * half0[1], r)
    b = Pos(0, 0, z1) * RectangleRounded(2 * half1[0], 2 * half1[1], r)
    return loft([a, b])


DOT_LIFT = 0.3


def dot(d, depth, axis="+z", lift=None):
    """Recessed dot (built along +Z, face at z=0, then oriented)."""
    lift = DOT_LIFT if lift is None else lift
    return orient(Pos(0, 0, -depth) * Cylinder(d / 2, depth + lift, align=Z_UP), axis)


def insert_hole(x, y, z_face, axis, depth=3.8, d=4.3):
    """Hole for an M3 x 3 x 5 heat-set insert (3 mm long, 5 mm OD), going into the part from a face."""
    return Pos(x, y, z_face) * dot(d, depth, axis, lift=0.2)


def hexagon(af):
    return RegularPolygon(af / 2 / math.cos(math.pi / 6), 6)


# --------------------------------------------------------------------------
# BODY: one print, front face on the bed
# --------------------------------------------------------------------------
GF_HALF = 65.0                      # Graflok module is 130 x 130
GF_SCREWS = ((-52.0, -58.0), (46.0, -58.0), (-52.0, 58.0), (46.0, 58.0))
Y_CHAN = (-(FALL + 10.3), RISE + 10.3)   # screw channel = hard stops for the nut turret (+/-10)
Y_DETENT = (48.0, -10.0)
Y_RAIL_SCREWS = (RAIL_Y_OFFSET - 50.0, RAIL_Y_OFFSET + 50.0)   # only holes outside the dark-slide band; rail also bonded
PADS_YREAR = ((48.0, -50.0), (48.0, 20.0))   # hard pads on the Y plate rear, sliding on the body
TOP_POSTS_X = (TOP_HANDLE_X[0] + HANDLE_POST / 2, TOP_HANDLE_X[1] - HANDLE_POST / 2)
SIDE_POSTS_Y = (SIDE_HANDLE_Y[0] + HANDLE_POST / 2, SIDE_HANDLE_Y[1] - HANDLE_POST / 2)
HANDLE_INSERT_Z_TOP = 7.0
HANDLE_INSERT_Z_SIDE = 10.0


def body_part():
    b = slab(BODY, BODY, BODY_Z0, BODY_Z1)

    # Graflok module recess; the seat is the floor of this recess (z = SEAT_Z)
    b -= box_at(-GF_HALF - 0.2, GF_HALF + 0.2, -GF_HALF - 0.2, GF_HALF + 0.2, BODY_Z0 - 1, SEAT_Z)
    # light-trap groove in the seat, closed at both ends
    b -= box_at(TRAP_X[0], TRAP_X[1], TRAP_Y[0], TRAP_Y[1], SEAT_Z - 0.01, SEAT_Z + TRAP_D)
    # dark-slide handle relief: open to the photographer's right side
    b -= box_at(-H - 1, SLIDE_RELIEF_X, -SLIDE_RELIEF_Y, SLIDE_RELIEF_Y, BODY_Z0 - 1, SLIDE_RELIEF_Z)

    # gate, stepped against flare
    h0 = opening_body(SEAT_Z)
    h0 = (max(h0[0], GATE_W / 2), max(h0[1], GATE_H / 2))
    b -= rect_loft(SEAT_Z - 0.5, h0, BODY_Z1 + 0.5, opening_body(BODY_Z1))
    for z in (8.5, 12.5, 16.5):
        hz = opening_body(z)
        b -= box_at(-hz[0] - 1.6, hz[0] + 1.6, -hz[1] - 1.6, hz[1] + 1.6, z, z + 2.0)

    # vertical guide channel (photographer's right): carriage top flush with the Y plate rear
    floor = YP_Z0 - BLOCK_H
    y_r0, y_r1 = RAIL_Y_OFFSET - RAIL_LEN_Y / 2, RAIL_Y_OFFSET + RAIL_LEN_Y / 2
    b -= box_at(Y_RAIL_X - BLOCK_W / 2 - 0.5, Y_RAIL_X + BLOCK_W / 2 + 0.5, y_r0 - 1, y_r1 + 1, floor, BODY_Z1 + 1)
    # rail seat: two locating ribs, 2 screws outside the dark-slide band (rail also bonded)
    for s in (-1, 1):
        b += box_at(Y_RAIL_X + s * (RAIL_W / 2 + 0.1), Y_RAIL_X + s * (RAIL_W / 2 + 1.1), y_r0, y_r1,
                    floor - 0.01, floor + 1.0)
    for yy in Y_RAIL_SCREWS:
        b -= insert_hole(Y_RAIL_X, yy, floor, "+z")

    # vertical screw channel (photographer's left); its ends are the hard stops
    b -= box_at(Y_SCREW_X - CHAN_W / 2, Y_SCREW_X + CHAN_W / 2, Y_CHAN[0], Y_CHAN[1], CHAN_FLOOR_Y, BODY_Z1 + 1)
    b -= cyl_y(BUSH_OD / 2 + 0.05, Y_CHAN[1] - 0.1, Y_CHAN[1] + BUSH_L, Y_SCREW_X, Y_SCREW_Z)
    b -= cyl_y(BUSH_OD / 2 + 0.05, Y_CHAN[0] - BUSH_L, Y_CHAN[0] + 0.1, Y_SCREW_X, Y_SCREW_Z)
    b -= cyl_y(ROD_D / 2 + 0.4, Y_CHAN[1], H + 1, Y_SCREW_X, Y_SCREW_Z)
    b -= cyl_y(ROD_D / 2 + 0.4, -H - 1, Y_CHAN[0], Y_SCREW_X, Y_SCREW_Z)
    b -= cyl_y(7.2, H - ORING_T, H + 1, Y_SCREW_X, Y_SCREW_Z)            # O-ring + washer seat, top
    b -= cyl_y(7.0, -H - 1, -H + 6.0, Y_SCREW_X, Y_SCREW_Z)              # nut pair recess, bottom

    # zero detent (M5 ball plunger)
    b -= Pos(*Y_DETENT, BODY_Z1) * dot(4.2, 11.0, "+z")

    # Graflok module screws (short inserts in the seat plane)
    for x, y in GF_SCREWS:
        b -= insert_hole(x, y, SEAT_Z, "-z")

    # handle inserts (M4)
    for x in TOP_POSTS_X:
        b -= Pos(x, H, HANDLE_INSERT_Z_TOP) * dot(5.0, 8.5, "+y", lift=0.2)
    for y in SIDE_POSTS_Y:
        b -= Pos(H, y, HANDLE_INSERT_Z_SIDE) * dot(5.0, 8.5, "+x", lift=0.2)

    # bottom plinth with the Arca plate pocket and two 1/4"-20 inserts
    pl = box_at(-ARCA_L / 2 - 6, ARCA_L / 2 + 6, -H - PLINTH, -H + 0.5, ARCA_ZC - ARCA_W / 2 - 3, BODY_Z1 - 0.01)
    pl = sfillet(pl, pl.edges().filter_by(Axis.Y), 3.0)
    b += pl
    b -= box_at(-ARCA_L / 2 - 0.15, ARCA_L / 2 + 0.15, -H - PLINTH - 1, -H - PLINTH + ARCA_POCKET,
                ARCA_ZC - ARCA_W / 2 - 0.15, ARCA_ZC + ARCA_W / 2 + 0.15)
    for x in (-15.0, 15.0):
        b -= Pos(x, -H - PLINTH + ARCA_POCKET, ARCA_ZC) * dot(8.2, 10.0, "-y", lift=0.2)

    # portrait level: tubular vial on the photographer's right side face, above the dark-slide band
    b -= box_at(-H - 1, -H + 7.2, 46.0, 72.0, 2.0, 9.2)
    # Y scale index (red dot) on the right side face
    b -= Pos(-H, 0.0, BODY_Z1 - 2.5) * dot(2.6, 0.6, "-x")
    return b


def body_vial():
    """Tubular spirit vial 7 x 25 (glass envelope, for render)."""
    return Pos(-H + 3.6, 59.0, 5.6) * Rot(90, 0, 0) * Cylinder(3.4, 25.0)


def body_index_inlay():
    return Pos(-H, 0.0, BODY_Z1 - 2.5) * dot(2.6, 0.6, "-x", lift=0)


# --------------------------------------------------------------------------
# GRAFLOK MODULE: pocket, bottom hinge rail (releases the Pro-S slide interlock),
# top clamp blade with two tongues. Print it first and fit it on your back.
# --------------------------------------------------------------------------
BLADE_TRAVEL = 4.5
BLADE_Y0 = 40.6                     # blade bottom edge (locked)
BLADE_W = 16.2
TONGUE_X = (-26.0, 26.0)
WHEEL_XY = (0.0, 48.0)
BLADE_GUIDES_X = (-37.0, 37.0)


def graflok_module():
    z0, z1 = GF_Z0, SEAT_Z
    g = extrude(Pos(0, 0, z0) * RectangleRounded(2 * GF_HALF, 2 * GF_HALF, 6), amount=z1 - z0)
    g = sfillet(g, g.edges().group_by(Axis.Z)[0], 0.8)
    # nose pocket, open toward the dark slide
    g -= box_at(-GF_HALF - 1, POCKET_WALL_X, POCKET_Y0, POCKET_Y1, z0 - 1, z1 + 1)
    g -= box_at(-GF_HALF - 1, SLIDE_RELIEF_X, -SLIDE_RELIEF_Y, SLIDE_RELIEF_Y, z0 - 1, z1 + 1)
    # reliefs for the back's top and bottom lips
    for s in (1, -1):
        g -= box_at(-LIP_RELIEF_X, LIP_RELIEF_X, s * LIP_RELIEF_Y[0], s * LIP_RELIEF_Y[1], z0 - 1, z0 + LIP_RELIEF_D)
    # bottom hinge rail: engages the back's bottom lip and presses the dark-slide interlock
    rail = box_at(-56.0, 47.0, -43.0, POCKET_Y0, SEAT_Z - 6.6, z0 + 0.01)
    rail += box_at(-56.0, 47.0, -51.0, -43.0, SEAT_Z - 8.4, z0 + 0.01)
    rail = sfillet(rail, rail.edges().filter_by(Axis.X).group_by(Axis.Z)[0], 0.8)
    g += rail
    # top blade: guide screws and the clamp wheel stud (M3 inserts, 3 mm)
    for x in BLADE_GUIDES_X:
        g -= insert_hole(x, BLADE_Y0 + 4.0, z0, "-z", depth=3.6)
    g -= insert_hole(*WHEEL_XY, z0, "-z", depth=3.6)
    # module screws (countersunk from the rear face)
    for x, y in GF_SCREWS:
        g -= cyl_z(1.7, z0 - 1, z1 + 1, x, y)
        g -= Pos(x, y, z0 - 0.01) * Cone(3.2, 1.7, 1.6, align=Z_UP)
    return g


def graflok_blade(locked=True):
    """Top clamp blade, 2.2 mm, on the module rear face. Slides up (+Y) to lock: its two
    wedge tongues enter the slots in the back's top lip. Clamped by a thumbwheel."""
    z0 = GF_Z0 - 2.2
    oy = 0.0 if locked else -BLADE_TRAVEL
    y0 = BLADE_Y0
    pts = [(-42.4, y0 + 3.0), (-39.4, y0), (39.4, y0), (42.4, y0 + 3.0), (42.4, y0 + BLADE_W), (-42.4, y0 + BLADE_W)]
    blade = Pos(0, 0, z0) * extrude(make_face(Polyline(*pts, close=True)), amount=2.2)
    for tx in TONGUE_X:
        tng = make_face(Polyline((tx - 7, y0 + BLADE_W - 0.01), (tx + 7, y0 + BLADE_W - 0.01),
                                 (tx + 5.5, y0 + BLADE_W + 3.9), (tx - 5.5, y0 + BLADE_W + 3.9), close=True))
        blade += Pos(0, 0, z0) * extrude(tng, amount=2.2)
    # U-slot for the wheel stud
    blade -= Pos(WHEEL_XY[0], WHEEL_XY[1] + BLADE_TRAVEL / 2, z0 - 1) * extrude(
        SlotCenterToCenter(BLADE_TRAVEL + 0.4, 3.4, rotation=90), amount=5)
    # guide slots for two countersunk M3 screws
    for x in BLADE_GUIDES_X:
        c = (x, BLADE_Y0 + 4.0 + BLADE_TRAVEL / 2)
        blade -= Pos(*c, z0 - 1) * extrude(SlotCenterToCenter(BLADE_TRAVEL, 3.4, rotation=90), amount=5)
        blade -= Pos(*c, z0 - 0.01) * extrude(SlotCenterToCenter(BLADE_TRAVEL, 6.0, rotation=90), amount=1.2)
    blade = sfillet(blade, blade.edges().filter_by(Axis.Z), 0.6)
    return Pos(0, oy, 0) * blade


def graflok_wheel():
    """Knurled thumbwheel that clamps the blade (M3 screw into the module insert)."""
    z1 = GF_Z0 - 2.2
    w = cyl_z(7.0, z1 - 3.0, z1)
    for i in range(24):
        w -= Rot(0, 0, i * 15) * Pos(7.3, 0, z1 - 1.5) * Cylinder(0.7, 4)
    w -= cyl_z(1.7, z1 - 4, z1 + 1)
    w -= cyl_z(2.9, z1 - 4, z1 - 1.3)
    return Pos(*WHEEL_XY, 0) * w


# --------------------------------------------------------------------------
# Y PLATE (rise and fall), front face on the bed
# --------------------------------------------------------------------------
Y_BLOCK_Y = (-BLOCK_PITCH / 2, BLOCK_PITCH / 2)
Y_BLOCK_CB = 5.0                      # counterbore depth for M3x12 (2.5 mm into the carriage)
X_CHAN = (-(SHIFT_X + 9.3), SHIFT_X + 9.3)   # turret travel = hard stops
X_DETENT = (0.0, 45.0)
PADS_Y = ((-40.0, 44.0), (40.0, 44.0))


def y_plate_part():
    p = slab(PLATE, PLATE, YP_Z0, YP_Z1)
    h0, h1 = opening_yplate(YP_Z0), opening_yplate(YP_Z1)
    p -= rect_loft(YP_Z0 - 0.5, h0, YP_Z1 + 0.5, (h1[0], max(h1[1], 33.0)))
    for z in (25.0, 29.0):
        hz = opening_yplate(z)
        p -= box_at(-hz[0] - 1.4, hz[0] + 1.4, -hz[1] - 1.4, hz[1] + 1.4, z, z + 2.0)

    # vertical carriages: 4 x M3 each, counterbored from the front
    for yy in Y_BLOCK_Y:
        for dx in (-BLOCK_HOLES[0] / 2, BLOCK_HOLES[0] / 2):
            for dy in (-BLOCK_HOLES[1] / 2, BLOCK_HOLES[1] / 2):
                x, y = Y_RAIL_X + dx, yy + dy
                p -= cyl_z(1.7, YP_Z0 - 1, YP_Z1 + 1, x, y)
                p -= cyl_z(3.1, YP_Z1 - Y_BLOCK_CB, YP_Z1 + 1, x, y)

    # nut turret (rear) into the body screw channel; the nut floats 0.5 mm and cannot turn
    t = box_at(Y_SCREW_X - CHAN_W / 2 + 1, Y_SCREW_X + CHAN_W / 2 - 1, -10, 10, CHAN_FLOOR_Y + 0.8, YP_Z0 + 0.5)
    t = sfillet(t, t.edges().filter_by(Axis.Y), 1.0)
    t -= cyl_y(ROD_D / 2 + 0.8, -11, 11, Y_SCREW_X, Y_SCREW_Z)
    nut_r = (NUT_AF + 2 * NUT_FLOAT) / 2 / math.cos(math.pi / 6)
    t -= Pos(Y_SCREW_X, -NUT_T / 2 - 0.15, Y_SCREW_Z) * Rot(-90, 0, 0) * Rot(0, 0, 90) * extrude(
        RegularPolygon(nut_r, 6), amount=NUT_T + 0.3)
    # side entry slot (flats vertical) from the +X face
    t -= box_at(Y_SCREW_X, Y_SCREW_X + CHAN_W, -NUT_T / 2 - 0.15, NUT_T / 2 + 0.15,
                Y_SCREW_Z - NUT_AF / 2 - NUT_FLOAT, Y_SCREW_Z + NUT_AF / 2 + NUT_FLOAT)
    p += t

    # rear relief for the rise knob (top-left corner) at full rise
    kr = KNOB_D / 2 + 0.8
    p -= box_at(Y_SCREW_X - kr, H + 1, H - RISE - 2, H + 1, YP_Z0 - 1, Y_SCREW_Z + kr)
    # rear detent dimple and hard pads (set the gap on the non-rail side)
    p -= Pos(*Y_DETENT, YP_Z0) * Sphere(1.6)
    for x, y in PADS_YREAR:
        p += box_at(x - 3, x + 3, y - 5, y + 5, YP_Z0 - GAP, YP_Z0 + 0.01)

    # horizontal guide channel (bottom): carriage top flush with the lens panel rear
    floor = XP_Z0 - BLOCK_H
    p -= box_at(-RAIL_LEN_X / 2 - 1, RAIL_LEN_X / 2 + 1, X_RAIL_Y - BLOCK_W / 2 - 0.5, X_RAIL_Y + BLOCK_W / 2 + 0.5,
                floor, YP_Z1 + 1)
    for s in (-1, 1):
        p += box_at(-RAIL_LEN_X / 2, RAIL_LEN_X / 2, X_RAIL_Y + s * (RAIL_W / 2 + 0.1), X_RAIL_Y + s * (RAIL_W / 2 + 1.1),
                    floor - 0.01, floor + 1.0)
    for xx in rail_holes(RAIL_LEN_X):
        p -= insert_hole(xx, X_RAIL_Y, floor, "+z")

    # horizontal screw channel (top), bushings, knob exit on the right, nut pair pocket on the left
    sfloor = X_SCREW_Z - BUSH_OD / 2
    p -= box_at(X_CHAN[0], X_CHAN[1], X_SCREW_Y - CHAN_W / 2, X_SCREW_Y + CHAN_W / 2, sfloor, YP_Z1 + 1)
    p -= cyl_x(BUSH_OD / 2 + 0.05, X_CHAN[0] - BUSH_L, X_CHAN[0] + 0.1, X_SCREW_Y, X_SCREW_Z)
    p -= cyl_x(BUSH_OD / 2 + 0.05, X_CHAN[1] - 0.1, X_CHAN[1] + BUSH_L, X_SCREW_Y, X_SCREW_Z)
    p -= cyl_x(ROD_D / 2 + 0.4, -H - 1, X_CHAN[0], X_SCREW_Y, X_SCREW_Z)
    p -= box_at(X_CHAN[1] + BUSH_L, X_CHAN[1] + BUSH_L + 12, X_SCREW_Y - 7, X_SCREW_Y + 7, sfloor, YP_Z1 + 1)
    p -= cyl_x(7.2, -H - 1, -H + ORING_T, X_SCREW_Y, X_SCREW_Z)

    # front: detent plunger and pockets for the two press-in pads that carry the lens panel
    p -= Pos(*X_DETENT, YP_Z1) * dot(4.2, 11.0, "+z")
    for x, y in PADS_Y:
        p -= box_at(x - 5.05, x + 5.05, y - 3.05, y + 3.05, YP_Z1 - 1.5, YP_Z1 + 1)

    # X scale index on the top edge, Y scale dots on the right edge
    p -= Pos(0.0, H, YP_Z1 - 2.5) * dot(2.6, 0.6, "+y")
    for mm in range(-5, 26, 5):
        p -= Pos(-H, mm, YP_Z0 + 4.0) * dot(3.2 if mm == 0 else 2.0, 0.6, "-x")
    return p


def y_plate_pads():
    """Press-in pads (1.5 mm in the pocket, 0.8 mm proud): the lens panel slides on them."""
    return [box_at(x - 5.1, x + 5.1, y - 3.1, y + 3.1, YP_Z1 - 1.5, YP_Z1 + GAP) for x, y in PADS_Y]


def y_plate_plugs():
    """Flush plugs over the carriage screw heads (press fit): keep the Y plate front face continuous."""
    out = []
    for yy in Y_BLOCK_Y:
        for dx in (-BLOCK_HOLES[0] / 2, BLOCK_HOLES[0] / 2):
            for dy in (-BLOCK_HOLES[1] / 2, BLOCK_HOLES[1] / 2):
                out.append(cyl_z(3.2, YP_Z1 - Y_BLOCK_CB + 3.1, YP_Z1, Y_RAIL_X + dx, yy + dy))   # press fit
    return out


def y_plate_inlays():
    """Zero dot and X index red, other dots white (separate bodies for multi-material)."""
    red = Compound([Pos(-H, 0, YP_Z0 + 4.0) * dot(3.2, 0.6, "-x", lift=0),
                    Pos(0.0, H, YP_Z1 - 2.5) * dot(2.6, 0.6, "+y", lift=0)])
    white = Compound([Pos(-H, mm, YP_Z0 + 4.0) * dot(2.0, 0.6, "-x", lift=0) for mm in range(-5, 26, 5) if mm])
    return red, white


# --------------------------------------------------------------------------
# LENS PANEL (X plate): back face on the bed; metal M65 flange flush with the front
# --------------------------------------------------------------------------
X_BLOCK_X = (-BLOCK_PITCH / 2, BLOCK_PITCH / 2)
STOP_PIN = (0.0, -64.5)
TURRET_SCREWS = ((-5.5, X_SCREW_Y + 5.0), (5.5, X_SCREW_Y + 5.0))


def x_plate_outline():
    nx, ny = XP_NOTCH
    pts = [(-H, -H), (H, -H), (H, ny), (nx, ny), (nx, H), (-nx, H), (-nx, ny), (-H, ny)]
    return make_face(Polyline(*pts, close=True))


def x_plate_part():
    z0, z1 = XP_Z0, XP_Z1
    p = Pos(0, 0, z0) * extrude(x_plate_outline(), amount=z1 - z0)
    p = sfillet(p, p.edges().filter_by(Axis.Z), CORNER_R)
    p = sfillet(p, p.edges().filter_by(Plane.XY), EDGE)
    # metal flange pocket, flush with the front; bore behind it
    p -= cyl_z(FLANGE_D / 2 + 0.2, z1 - FLANGE_T, z1 + 1)
    p -= cyl_z(31.5, z0 - 1, z1)
    # flange screws: 4 x M3 countersunk from the rear, into the flange's M3 holes
    for a in (0, 90, 180, 270):
        x, y = FLANGE_PCD / 2 * math.cos(math.radians(a)), FLANGE_PCD / 2 * math.sin(math.radians(a))
        p -= cyl_z(1.7, z0 - 1, z1, x, y)
        p -= Pos(x, y, z0 - 0.01) * Cone(3.2, 1.7, 1.6, align=Z_UP)
    # horizontal carriages: 4 x M3 countersunk from the front
    for xx in X_BLOCK_X:
        for dx in (-BLOCK_HOLES[1] / 2, BLOCK_HOLES[1] / 2):
            for dy in (-BLOCK_HOLES[0] / 2, BLOCK_HOLES[0] / 2):
                x, y = xx + dx, X_RAIL_Y + dy
                p -= cyl_z(1.7, z0 - 1, z1 + 1, x, y)
                p -= Pos(x, y, z1 - 1.61) * Cone(1.7, 3.2, 1.62, align=Z_UP)
    # turret screws (inserts in the rear face)
    for x, y in TURRET_SCREWS:
        p -= insert_hole(x, y, z0, "-z", depth=3.8)
    # rear detent dimple
    p -= Pos(*X_DETENT, z0) * Sphere(1.6)
    # infinity stop pin (M3 screw standing on the front)
    p -= insert_hole(*STOP_PIN, z1, "+z", depth=4.5)
    # depth-of-field dots (f/11 small, f/22 large) and the focus index (red) above the ring
    r = FOCUS_OD / 2 + 4.0
    p -= Pos(0, r, z1) * dot(3.4, 0.6)
    for n, dd in ((11, 1.8), (22, 2.6)):
        for s in (-1, 1):
            p -= Rot(0, 0, s * dof_angle(n)) * (Pos(0, r, z1) * dot(dd, 0.6))
    # X scale dots on the top edge (zero larger)
    for mm in range(-25, 26, 5):
        p -= Pos(mm, H, (z0 + z1) / 2) * dot(3.2 if mm == 0 else 2.0, 0.6, "+y")
    return p


def x_plate_inlays():
    r = FOCUS_OD / 2 + 4.0
    red = [Pos(0, r, XP_Z1) * dot(3.4, 0.6, lift=0), Pos(0, H, (XP_Z0 + XP_Z1) / 2) * dot(3.2, 0.6, "+y", lift=0)]
    white = []
    for n, dd in ((11, 1.8), (22, 2.6)):
        for s in (-1, 1):
            white.append(Rot(0, 0, s * dof_angle(n)) * (Pos(0, r, XP_Z1) * dot(dd, 0.6, lift=0)))
    for mm in range(-25, 26, 5):
        if mm:
            white.append(Pos(mm, H, (XP_Z0 + XP_Z1) / 2) * dot(2.0, 0.6, "+y", lift=0))
    return Compound(red), Compound(white)


def x_turret():
    """Nut turret, screwed to the lens panel rear; runs in the Y plate screw channel."""
    zt = XP_Z0
    zb = X_SCREW_Z - BUSH_OD / 2 + 0.5
    t = box_at(-9, 9, X_SCREW_Y - CHAN_W / 2 + 1, X_SCREW_Y + CHAN_W / 2 - 1, zb, zt)
    t = sfillet(t, t.edges().filter_by(Axis.X), 1.0)
    t -= cyl_x(ROD_D / 2 + 0.8, -10, 10, X_SCREW_Y, X_SCREW_Z)
    nut_r = (NUT_AF + 2 * NUT_FLOAT) / 2 / math.cos(math.pi / 6)
    t -= Pos(-NUT_T / 2 - 0.15, X_SCREW_Y, X_SCREW_Z) * Rot(0, 90, 0) * Rot(0, 0, 90) * extrude(
        RegularPolygon(nut_r, 6), amount=NUT_T + 0.3)
    t -= box_at(-NUT_T / 2 - 0.15, NUT_T / 2 + 0.15, X_SCREW_Y - NUT_AF / 2 - NUT_FLOAT,
                X_SCREW_Y + NUT_AF / 2 + NUT_FLOAT, zb - 1, X_SCREW_Z)
    for x, y in TURRET_SCREWS:
        t -= cyl_z(1.7, zb - 1, zt + 1, x, y)
        t -= cyl_z(2.9, zb - 1, zb + 3.5, x, y)
    return t


# --------------------------------------------------------------------------
# FOCUS RING (front face on the bed), infinity stop, dots on the rim
# --------------------------------------------------------------------------
FOCUS_DIST = (("inf", 0.0), ("5", 5), ("3", 3), ("2", 2), ("1.5", 1.5), ("1", 1), ("0.7", 0.7))
LEVER_ANG = -95.0
STOP_TAB_ANG = 172.0          # the tab touches the stop pin (at 180 deg) at infinity


def focus_ring_part():
    z0 = HELI_Z0 + HELI_GRIP_Z[0]
    r = FOCUS_OD / 2
    ring = cyl_z(r, z0, z0 + FOCUS_W) - cyl_z(HELI_OD / 2 + 0.2, z0 - 1, z0 + FOCUS_W + 1)
    ring = sfillet(ring, [e for e in ring.edges().filter_by(GeomType.CIRCLE) if e.radius > 60], EDGE)
    # grip: flutes except on the scale sector
    for i in range(0, 360, 10):
        a = ((i + 180) % 360) - 180
        if -10 < a < 175:
            continue
        ring -= Rot(0, 0, -i) * (Pos(0, r + 0.4, z0 + FOCUS_W / 2) * Box(2.0, 2.0, FOCUS_W - 3))
    # finger lever (starts 2 mm up: clears the lens panel)
    lever = Rot(0, 0, -LEVER_ANG) * (Pos(0, r + 4, z0 + 2 + (FOCUS_W - 2) / 2) * Box(12, 10, FOCUS_W - 2))
    ring += sfillet(lever, lever.edges().filter_by(Axis.Z), 2.5)
    # stop tab on the rear face with a tangential M3 stop screw (adjust infinity per lens)
    ring += Rot(0, 0, -STOP_TAB_ANG) * (Pos(0, r - 3.0, z0 - 0.65) * Box(10, 6, 1.5))
    ring -= Rot(0, 0, -STOP_TAB_ANG) * (Pos(0, r - 3.0, z0 - 0.3) * Rot(0, 90, 0) * Cylinder(1.25, 12))
    # 4 radial M3 nylon-tip grub screws (2.5 mm holes, tap M3)
    for a in (45, 135, 225, 315):
        ring -= Rot(0, 0, a) * (Pos(0, (r + HELI_OD / 2) / 2, z0 + FOCUS_W / 2) * Rot(90, 0, 0) * Cylinder(1.25, r))
    for m in focus_ring_marks():
        ring -= m
    return ring


def focus_ring_marks(depth=0.6, lift=None):
    """Distance dots on the rim, readable from above and behind (infinity larger)."""
    zc = HELI_Z0 + HELI_GRIP_Z[0] + FOCUS_W - 2.5
    out = []
    for txt, d in FOCUS_DIST:
        ang = 0.0 if d == 0 else focus_angle(d)
        out.append(Rot(0, 0, -ang) * (Pos(0, FOCUS_OD / 2, zc) * dot(3.4 if d == 0 else 2.2, depth, "+y", lift=lift)))
    return out


# --------------------------------------------------------------------------
# BOARD HOLDER (back face on the bed) and M65 ADAPTER RING (flange on the bed)
# --------------------------------------------------------------------------
HOLDER_W, HOLDER_H = BOARD_W + 18, BOARD_H + 37
ADAPTER_SCREW_R = 40.0
STUB_L = 5.5
LATCH_ENGAGE = 4.0


def holder_part():
    z0, z1 = HOLDER_Z0, BOARD_Z1
    h = extrude(Pos(0, 9.5, z0) * RectangleRounded(HOLDER_W, HOLDER_H, CORNER_R), amount=z1 - z0)
    h = sfillet(h, h.edges().group_by(Axis.Z)[-1], EDGE)
    h -= box_at(-BOARD_W / 2 - 0.2, BOARD_W / 2 + 0.2, -BOARD_H / 2 - 0.2, BOARD_H / 2 + 0.2, BOARD_Z0, z1 + 1)
    h -= cyl_z(REAR_CLEAR_D / 2, z0 - 1, z1 + 1)
    h -= cyl_z(REAR_CLEAR_D / 2 + 3.5, BOARD_Z0 - 1.6, BOARD_Z0 + 0.1)        # board light-trap ring
    h -= cyl_z(45.0, BOARD_Z0 - 0.6, BOARD_Z0 + 0.1)                          # felt ring seat
    # groove for a 1 mm felt ring against the adapter flange (light seal of the arc slots)
    h -= cyl_z(35.0, z0 - 0.1, z0 + 0.8) - cyl_z(30.5, z0 - 1, z0 + 2)
    # adapter inserts, 1.2 mm skin under the board seat
    for a in (45, 135, 225, 315):
        x, y = ADAPTER_SCREW_R * math.cos(math.radians(a)), ADAPTER_SCREW_R * math.sin(math.radians(a))
        h -= insert_hole(x, y, z0, "-z", depth=3.3)
    # bottom lips, anchored on the frame, overhanging the board by 2 mm
    for sx_ in (-1, 1):
        h += box_at(sx_ * 30 - 9, sx_ * 30 + 9, -BOARD_H / 2 - 4, -BOARD_H / 2 - 0.2, z1 - 0.01, z1 + 1.6)
        h += box_at(sx_ * 30 - 9, sx_ * 30 + 9, -BOARD_H / 2 - 0.5, -BOARD_H / 2 + 2.0, z1 + 0.1, z1 + 1.6)
    # spring latch: guide rails above the frame face, two M2.5 screws, spring bore
    for s in (-1, 1):
        h += box_at(s * 15.2, s * 18.0, BOARD_H / 2 - 0.2, BOARD_H / 2 + 26.0, z1 - 0.01, z1 + 2.6)
    for x in (-9.0, 9.0):
        h -= cyl_z(1.05, z1 - 4.5, z1 + 0.1, x, LATCH_SCREW_Y)
    h += box_at(-4.0, 4.0, BOARD_H / 2 + 22.0, BOARD_H / 2 + 26.0, z1 - 0.01, z1 + 2.6)   # spring abutment
    return h


LATCH_LEN = 14.0
LATCH_SCREW_Y = BOARD_H / 2 + 11.0


def holder_latch(locked=True):
    """Spring slider: pull up to release, a spring (4 x 10) pushes it back with 4 mm engagement."""
    z0 = BOARD_Z1 + 0.05
    oy = 0.0 if locked else LATCH_ENGAGE + 1.0
    y0, y1 = BOARD_H / 2 - LATCH_ENGAGE, BOARD_H / 2 - LATCH_ENGAGE + LATCH_LEN
    l = box_at(-15, 15, y0, y1, z0, z0 + 2.4)
    l = sfillet(l, l.edges().filter_by(Axis.Z), 1.0)
    travel = LATCH_ENGAGE + 1.0
    for x in (-9.0, 9.0):
        l -= Pos(x, LATCH_SCREW_Y - travel / 2, z0 - 1) * extrude(SlotCenterToCenter(travel, 2.8, rotation=90), amount=5)
    grip = box_at(-8, 8, y1 - 4.0, y1, z0 + 2.39, z0 + 4.4)
    l += sfillet(grip, grip.edges().filter_by(Axis.X), 0.8)
    return Pos(0, oy, 0) * l


def adapter_part(with_thread=True, flange_t=ADAPTER_T):
    """Printed M65 adapter: male stub into the helicoid, flange screwed to the holder through arc
    slots (square the board, then tighten). It is the calibration part: every 0.5 mm less of
    flange is 0.5 mm more helicoid travel past infinity."""
    z1 = HOLDER_Z0
    z0 = z1 - flange_t
    f = cyl_z(ADAPTER_SCREW_R + 4.5, z0, z1) - cyl_z(REAR_CLEAR_D / 2, z0 - 1, z1 + 1)
    for a in (45, 135, 225, 315):
        for da in range(-40, 41, 4):
            aa = math.radians(a + da)
            f -= cyl_z(1.7, z0 - 1, z1 + 1, ADAPTER_SCREW_R * math.cos(aa), ADAPTER_SCREW_R * math.sin(aa))
    stub = cyl_z(M65 / 2 - (0.6 if with_thread else 0.0), z0 - STUB_L, z0 + 0.1) - cyl_z(REAR_CLEAR_D / 2, z0 - STUB_L - 1, z0 + 1)
    if with_thread and IsoThread is not None:
        th = IsoThread(major_diameter=M65 - 0.25, pitch=1.0, length=STUB_L - 0.8, external=True,
                       end_finishes=("fade", "square"))
        stub += Pos(0, 0, z0 - STUB_L + 0.3) * th
    return f + stub


# --------------------------------------------------------------------------
# KNOBS (base on the bed)
# --------------------------------------------------------------------------
def knob_part():
    d, h = KNOB_D, KNOB_H
    k = Cylinder(d / 2, h, align=Z_UP)
    for i in range(30):
        k -= Rot(0, 0, i * 12) * Pos(d / 2 + 0.35, 0, h / 2 + 0.8) * Cylinder(0.8, h - 3.0)
    k = sfillet(k, k.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1], 1.0)
    k -= Pos(0, 3.5, h + 1.8) * Sphere(3.2)                                   # spinner dimple
    k -= Pos(0, 0, -0.1) * extrude(hexagon(NUT_AF + 0.3), amount=NUT_T + 0.3)
    k -= cyl_z(ROD_D / 2 + 0.25, -1, h - 1.5)
    k -= Pos(0, 0, NUT_T + 3.0) * Rot(0, 90, 0) * Cylinder(1.25, d)          # M3 grub
    k -= cyl_z(5.5, -0.1, 0.9) - cyl_z(3.4, -1, 2)                           # O-ring groove
    k -= Pos(0, -(d / 2 - 3.6), h) * dot(2.4, 0.6)
    index = Pos(0, -(d / 2 - 3.6), h) * dot(2.4, 0.6, lift=0)
    return k, index


# --------------------------------------------------------------------------
# HANDLES (printed on their side, bolted with M4 x 50 through the posts)
# --------------------------------------------------------------------------
def handle_loop(length, z0, z1, height=HANDLE_H, bar=HANDLE_BAR, post=HANDLE_POST):
    outer = Pos(0, height / 2, 0) * Rectangle(length, height)
    inner = Pos(0, (height - bar) / 2 - 1, 0) * Rectangle(length - 2 * post, height - bar + 2)
    h = Pos(0, 0, z0) * extrude(outer - inner, amount=z1 - z0)
    h = sfillet(h, h.edges().filter_by(Axis.Z).group_by(Axis.Y)[-1], CORNER_R)
    h = sfillet(h, [e for e in h.edges().filter_by(Axis.Z) if abs(e.center().Y - (height - bar)) < 0.2], 4.0)
    h = sfillet(h, [e for e in h.edges().filter_by(Plane.XY) if e.center().Y > 0.5], 1.6)
    return h


def handle_screw_holes(length, zc, height=HANDLE_H, post=HANDLE_POST):
    out = []
    for sx_ in (-1, 1):
        x = sx_ * (length / 2 - post / 2)
        out.append(Pos(x, -1, zc) * Rot(-90, 0, 0) * Cylinder(2.2, height + 2, align=Z_UP))
        out.append(Pos(x, height - 4.5, zc) * Rot(-90, 0, 0) * Cylinder(3.8, 6, align=Z_UP))
    return out


def top_handle():
    x0, x1 = TOP_HANDLE_X
    z0, z1 = TOP_HANDLE_Z
    h = handle_loop(x1 - x0, z0, z1)
    for c in handle_screw_holes(x1 - x0, HANDLE_INSERT_Z_TOP):
        h -= c
    # landscape level: tubular vial along X in the bar, read from behind
    h -= box_at(-14, 14, HANDLE_H - HANDLE_BAR / 2 - 3.6, HANDLE_H - HANDLE_BAR / 2 + 3.6, z0 - 1, z0 + 7.5)
    return Pos((x0 + x1) / 2, H, 0) * h


def top_vial():
    x0, x1 = TOP_HANDLE_X
    z0, _ = TOP_HANDLE_Z
    return Pos((x0 + x1) / 2, H + HANDLE_H - HANDLE_BAR / 2, z0 + 3.5) * Rot(0, 90, 0) * Cylinder(3.4, 25.0)


def side_handle():
    """Photographer's left. Its outer bar carries the portrait Arca plate."""
    y0, y1 = SIDE_HANDLE_Y
    z0, z1 = SIDE_HANDLE_Z
    h = handle_loop(y1 - y0, z0, z1)
    for c in handle_screw_holes(y1 - y0, HANDLE_INSERT_Z_SIDE):
        h -= c
    zc = ARCA_ZC
    h -= box_at(-ARCA_L / 2 - 0.15, ARCA_L / 2 + 0.15, HANDLE_H - ARCA_POCKET, HANDLE_H + 1,
                zc - ARCA_W / 2 - 0.15, zc + ARCA_W / 2 + 0.15)
    for x in (-15.0, 15.0):
        h -= Pos(x, HANDLE_H - ARCA_POCKET, zc) * dot(8.2, 10.0, "+y", lift=0.2)
    return Pos(H, (y0 + y1) / 2, 0) * Rot(0, 0, -90) * h


def arca_plate():
    """Arca-Swiss plate 60 x 38 x 10 lying along X, clamp face at -Y (bottom plate position)."""
    zc = ARCA_ZC
    y_top = -H - PLINTH + ARCA_POCKET
    y_bot = y_top - ARCA_T
    hw_, land, bev = ARCA_W / 2, 1.0, 4.0
    prof = [(y_bot, zc - hw_), (y_bot, zc + hw_), (y_bot + land, zc + hw_), (y_bot + land + bev, zc + hw_ - bev),
            (y_top, zc + hw_ - bev), (y_top, zc - hw_ + bev), (y_bot + land + bev, zc - hw_ + bev), (y_bot + land, zc - hw_)]
    plate = extrude(make_face(Plane.YZ * Polyline(*prof, close=True)), amount=ARCA_L / 2, both=True)
    plate = sfillet(plate, plate.edges().filter_by(Axis.Y), 1.0)
    for x in (-15.0, 15.0):
        plate -= cyl_y(3.3, y_bot - 1, y_top + 1, x, zc)
        plate -= cyl_y(5.5, y_bot - 1, y_bot + 6.5, x, zc)
    return plate


def side_arca_plate():
    """Same plate on the side handle's outer face (portrait)."""
    base = arca_plate()
    y_top = -H - PLINTH + ARCA_POCKET
    # move from the bottom-plate frame to the side handle's outer face
    x_face = H + HANDLE_H - ARCA_POCKET
    yc = sum(SIDE_HANDLE_Y) / 2
    return Pos(x_face, yc, 0) * Rot(0, 0, 90) * Pos(0, -y_top, 0) * base


# --------------------------------------------------------------------------
# BOUGHT PARTS (envelopes)
# --------------------------------------------------------------------------
def rail_holes(length):
    """Hole positions (symmetric, 20 mm pitch) along a rail of this length, centred on 0."""
    n = int((length - 8) // RAIL_HOLE_PITCH) + 1
    return [(i - (n - 1) / 2) * RAIL_HOLE_PITCH for i in range(n)]


def mgn9_rail(length):
    r = Box(length, RAIL_W, RAIL_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for s in (-1, 1):
        r -= Pos(0, s * RAIL_W / 2, 4.2) * Box(length + 2, 1.6, 1.6)
    for xx in rail_holes(length):
        r -= Pos(xx, 0, 0) * Cylinder(1.75, 20)
        r -= Pos(xx, 0, RAIL_H - 3.0) * Cylinder(3.0, 4, align=Z_UP)
    return r


def mgn9_block():
    b = Box(BLOCK_L - 6, BLOCK_W, BLOCK_H - BLOCK_UNDER, align=(Align.CENTER, Align.CENTER, Align.MIN))
    b -= Pos(0, 0, -1) * Box(BLOCK_L, RAIL_W + 0.4, RAIL_H - BLOCK_UNDER + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    b = sfillet(b, b.edges().filter_by(Axis.X).group_by(Axis.Z)[-1], 0.6)
    for dx in (-BLOCK_HOLES[1] / 2, BLOCK_HOLES[1] / 2):
        for dy in (-BLOCK_HOLES[0] / 2, BLOCK_HOLES[0] / 2):
            b -= Pos(dx, dy, BLOCK_H - BLOCK_UNDER - 3) * Cylinder(1.25, 4, align=Z_UP)
    seals = Box(BLOCK_L, BLOCK_W - 1, BLOCK_H - BLOCK_UNDER - 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    seals -= Box(BLOCK_L - 6, BLOCK_W + 2, 30)
    seals -= Pos(0, 0, -1) * Box(BLOCK_L + 2, RAIL_W + 0.4, RAIL_H - BLOCK_UNDER + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return b, seals


def helicoid_part(length):
    z0 = HELI_Z0
    core = cyl_z(HELI_OD / 2 - 4, z0, z0 + length) - cyl_z(HELI_BORE / 2, z0 - 1, z0 + length + 1)
    grip = cyl_z(HELI_OD / 2, z0 + HELI_GRIP_Z[0], z0 + HELI_GRIP_Z[1]) - cyl_z(HELI_OD / 2 - 5, z0, z0 + 13)
    for i in range(72):
        grip -= Rot(0, 0, i * 5) * Pos(HELI_OD / 2 + 0.35, 0, z0 + 6.5) * Cylinder(0.8, 8.6)
    return core + grip


def flange_part():
    """RafCamera M65x1 female lens flange, 79 x 5 mm."""
    z1 = XP_Z1
    f = cyl_z(FLANGE_D / 2, z1 - FLANGE_T, z1) - cyl_z(M65 / 2 - 0.5, z1 - FLANGE_T - 1, z1 + 1)
    for a in range(0, 360, 45):
        x, y = FLANGE_PCD / 2 * math.cos(math.radians(a)), FLANGE_PCD / 2 * math.sin(math.radians(a))
        f -= cyl_z(1.25 if a % 90 == 0 else 1.0, z1 - FLANGE_T - 1, z1 + 1, x, y)
    return f


def lensboard_part():
    b = box_at(-BOARD_W / 2, BOARD_W / 2, -BOARD_H / 2, BOARD_H / 2, BOARD_Z0, BOARD_Z1)
    b = schamfer(b, b.edges().filter_by(Axis.Z).group_by(Axis.Y)[0], 6.0)
    b -= cyl_z(34.8 / 2, BOARD_Z0 - 1, BOARD_Z1 + 1)
    ring = cyl_z(REAR_CLEAR_D / 2 + 3.0, BOARD_Z0 - 1.2, BOARD_Z0 + 0.1) - cyl_z(REAR_CLEAR_D / 2 + 0.5, BOARD_Z0 - 2, BOARD_Z0 + 1)
    return b + ring


def lens_part():
    """Schneider Super-Angulon 65/8 in Copal 0 (envelope)."""
    z = BOARD_Z1
    rear = cyl_z(21, z - 21, z - 1)
    ring = cyl_z(21.5, BOARD_Z0 - 3, BOARD_Z0) - cyl_z(16, BOARD_Z0 - 4, BOARD_Z0 + 1)
    sh = cyl_z(31.5, z, z + 19)
    shutter = sfillet(sh, sh.edges(), 1.5)
    scale_ring = cyl_z(32.3, z + 6, z + 11)
    lever = Pos(24, 20, z + 9) * Rot(0, 0, 35) * Box(16, 4, 3)
    cock = Pos(-26, 18, z + 14) * Rot(0, 0, -30) * Box(12, 4, 3)
    front = cyl_z(28, z + 19, z + 42) - cyl_z(24.8, z + 36, z + 43)
    glass = (Pos(0, 0, z + 30) * Sphere(27)) & cyl_z(24.8, z + 19, z + 41)
    return rear + ring + shutter + scale_ring + lever + cock + front, glass


def rb67_back():
    """Mamiya RB67 Pro-S 120 back (envelope). Dark slide exits on the photographer's right (-X);
    film advance lever on top near the front right corner."""
    zf = GF_Z0 - 0.5
    nose = box_at(-61.0, POCKET_WALL_X - 0.3, POCKET_Y0 + 0.3, POCKET_Y1 - 0.3, zf, SEAT_Z)
    shell = Pos(0, 0, zf - 24) * Box(122, 108, 48)
    shell = sfillet(shell, shell.edges().filter_by(Axis.Z), 5.0)
    shell = sfillet(shell, shell.edges().group_by(Axis.Z)[0], 3.0)
    slide_handle = box_at(-66.0, -61.0, -36.0, 36.0, zf - 10.0, zf + 2.0)
    counter = box_at(-30, 30, 54, 58, zf - 40, zf - 8)
    lever = Pos(-44, 60, zf - 8) * Box(40, 5, 8)
    window = box_at(-20, 20, -56, -52, zf - 30, zf - 18)
    return nose + shell + slide_handle + counter, window, lever
