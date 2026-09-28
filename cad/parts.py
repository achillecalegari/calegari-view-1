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
FIT = 0.3     # clearance per side on bought parts that drop into a pocket (board, flange, Arca plates)


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
GF_SCREWS = ((-52.0, -58.0), (47.5, -58.0), (-52.0, 58.0), (47.5, 58.0))
Y_CHAN = (-(FALL + 10.3), RISE + 10.3)   # screw channel = hard stops for the nut turret (+/-10)
Y_DETENT = (-52.0, -10.0)
TOP_POSTS_X = (TOP_HANDLE_X[0] + HANDLE_POST / 2 + 1.5, TOP_HANDLE_X[1] - HANDLE_POST / 2 - 1.5)
HANDLE_INSERT_Z_TOP = 10.0


def body_part():
    b = slab(BODY, BODY, BODY_Z0, BODY_Z1)
    # L bracket first: every cut below goes through it too
    b += l_bracket()

    # Graflok module recess; the seat is the floor of this recess (z = SEAT_Z)
    b -= box_at(-GF_HALF - 0.2, GF_HALF + 0.2, -GF_HALF - 0.2, GF_HALF + 0.2, BODY_Z0 - 1, SEAT_Z)
    # light-trap groove in the seat, closed at both ends (it takes the back's ridge)
    b -= box_at(TRAP_X[0], TRAP_X[1], TRAP_Y[0], TRAP_Y[1], SEAT_Z - 0.01, SEAT_Z + TRAP_D)
    # and a closed loop around the gate: light that creeps along the seat has to turn two corners
    loop = (Rectangle(2 * LOOP_X + 1.2, 2 * LOOP_Y + 1.2) - Rectangle(2 * LOOP_X - 1.2, 2 * LOOP_Y - 1.2))
    b -= Pos(0, 0, SEAT_Z - 0.01) * extrude(loop, amount=1.0)
    # dark-slide handle relief: open to the photographer's right side
    b -= box_at(-H - 1, SLIDE_RELIEF_X, -SLIDE_RELIEF_Y, SLIDE_RELIEF_Y, BODY_Z0 - 1, SLIDE_RELIEF_Z)

    # gate, stepped against flare
    h0 = opening_body(SEAT_Z)
    h0 = (max(h0[0], GATE_W / 2), max(h0[1], GATE_H / 2))
    b -= rect_loft(SEAT_Z - 0.5, h0, BODY_Z1 + 0.5, opening_body(BODY_Z1))
    for z in (8.5, 12.5, 16.5):
        hz = opening_body(z)
        b -= box_at(-hz[0] - 1.6, hz[0] + 1.6, -hz[1] - 1.6, hz[1] + 1.6, z, z + 2.0)

    # dovetail ways: two printed rails along the side edges of the front face, countersunk screws
    # from the front into inserts (the rails go on first, the Y plate slides in from the top like a drawer)
    for s in (-1, 1):
        for yy in Y_WAY_SCREWS[s]:
            b -= insert_hole(s * WAY_SCREW_U, yy, BODY_Z1, "+z", depth=6.0, d=3.3)     # M2.5

    # vertical screw channel (photographer's left); its ends are the hard stops
    b -= box_at(Y_SCREW_X - CHAN_W / 2, Y_SCREW_X + CHAN_W / 2, Y_CHAN[0], Y_CHAN[1], CHAN_FLOOR_Y, BODY_Z1 + 1)
    b -= cyl_y(BUSH_OD / 2 + 0.05, Y_CHAN[1] - 0.1, Y_CHAN[1] + BUSH_L, Y_SCREW_X, Y_SCREW_Z)
    b -= cyl_y(BUSH_OD / 2 + 0.05, Y_CHAN[0] - BUSH_L, Y_CHAN[0] + 0.1, Y_SCREW_X, Y_SCREW_Z)
    b -= cyl_y(ROD_D / 2 + 0.4, Y_CHAN[1], H + 1, Y_SCREW_X, Y_SCREW_Z)
    b -= cyl_y(ROD_D / 2 + 0.4, -H - 1, Y_CHAN[0], Y_SCREW_X, Y_SCREW_Z)
    b -= cyl_y(4.6, H - ORING_SEAT, H + 1, Y_SCREW_X, Y_SCREW_Z)         # O-ring seat, top
    b -= cyl_y(6.3, -H - PLINTH - 1, Y_CAP_TOP, Y_SCREW_X, Y_SCREW_Z)    # cap nut recess (11.05 over corners)

    # zero detent (M5 ball plunger): a through hole, so the plunger can be set from behind
    b -= Pos(*Y_DETENT, BODY_Z1) * dot(4.2, BODY_Z1 - SEAT_Z + 1.0, "+z")

    # Graflok module screws (short inserts in the seat plane)
    for x, y in GF_SCREWS:
        b -= insert_hole(x, y, SEAT_Z, "-z", depth=6.5)

    # handle inserts (M4)
    for x in TOP_POSTS_X:
        b -= Pos(x, H, HANDLE_INSERT_Z_TOP) * dot(5.6, 9.1, "+y", lift=0.2)       # ruthex M4 x 8.1

    # Arca pockets in the L bracket: bottom (landscape) and side leg (portrait)
    b -= box_at(-ARCA_L / 2 - FIT, ARCA_L / 2 + FIT, -H - PLINTH - 1, -H - PLINTH + ARCA_POCKET,
                ARCA_ZC - ARCA_W / 2 - FIT, ARCA_ZC + ARCA_W / 2 + FIT)
    for x in (-15.0, 15.0):
        b -= Pos(x, -H - PLINTH + ARCA_POCKET, ARCA_ZC) * dot(8.2, 10.0, "-y", lift=0.2)
    xf = H + SIDE_T
    b -= box_at(xf - ARCA_POCKET, xf + 1, SIDE_ARCA_YC - ARCA_L / 2 - FIT, SIDE_ARCA_YC + ARCA_L / 2 + FIT,
                ARCA_ZC - ARCA_W / 2 - FIT, ARCA_ZC + ARCA_W / 2 + FIT)
    for y in (-15.0, 15.0):
        b -= Pos(xf - ARCA_POCKET, SIDE_ARCA_YC + y, ARCA_ZC) * dot(8.2, 10.0, "+x", lift=0.2)

    # portrait level: bull's-eye vial in the photographer's right side face (reads both axes)
    b -= level_pocket((-H, SIDE_LEVEL[0], SIDE_LEVEL[1]), "-x", depth=LEVEL_H - 0.4)
    # Y scale index (red dot) on the right side face
    b -= Pos(-H, 0.0, BODY_Z1 - 2.5) * dot(2.6, 0.6, "-x")
    # grip texture on the side leg, above and below the Arca plate: fine flutes along the depth.
    # They print as walls (the body lies on its front), so they come out crisp, no extra parts.
    flutes = []
    for y0, y1 in GRIP_Y:
        n = int((y1 - y0 - GRIP_W) / GRIP_PITCH) + 1
        off = (y1 - y0 - GRIP_W - (n - 1) * GRIP_PITCH) / 2
        for i in range(n):
            yc = y0 + off + GRIP_W / 2 + i * GRIP_PITCH
            flutes.append(box_at(H + SIDE_T - GRIP_D, H + SIDE_T + 1, yc - GRIP_W / 2, yc + GRIP_W / 2, *GRIP_Z))
    b -= Compound(flutes)
    return b


GRIP_Y = ((34.0, 71.0), (-93.0, -34.0))
GRIP_Z = (L_Z0 + 4.0, BODY_Z1 - 4.0)
GRIP_W, GRIP_PITCH, GRIP_D = 1.0, 2.2, 0.6


LOOP_X, LOOP_Y = 43.0, 34.5            # light-trap loop in the seat (inside the back's nose)
Y_CAP_TOP = -62.5                      # the rise rod's cap nut sits under this shoulder
SIDE_LEVEL = (55.0, 10.0)              # (y, z) of the portrait level on the -X face


def level_pocket(c, axis, depth=None):
    """Pocket for a 15 x 8 mm bull's-eye vial, entering a face. Its roof is a teardrop pointing to the
    camera's rear, which is up when the part prints face down, so the round hole prints without sag."""
    r, d = LEVEL_D / 2, (depth or LEVEL_H)
    if axis == "-x":            # face at -X, pocket goes +X; local +X ends up at camera -Z
        dv, rot = (1.0, 0.0), Rot(0, 90, 0)
    else:                       # "+y": top face, pocket goes -Y; local -Y ends up at camera -Z
        dv, rot = (0.0, -1.0), Rot(90, 0, 0)
    def turn(v, a):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        return (v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca)
    p1 = (dv[0] * r * 1.414, dv[1] * r * 1.414)
    p2, p3 = [(q[0] * r, q[1] * r) for q in (turn(dv, 45), turn(dv, -45))]
    face = Circle(r) + Polygon((0, 0), p2, p1, p3, align=None)
    keep = Pos(dv[0] * (r + 1.0 - 20), dv[1] * (r + 1.0 - 20)) * Rectangle(40, 40)
    face = face & keep
    sol = Compound([extrude(f, amount=d + 1, dir=(0, 0, 1)) for f in face.faces()])
    return Pos(*c) * rot * (Pos(0, 0, -1) * sol)


def l_bracket():
    """Bottom plinth + side leg as one L around the body, same R9 corners as the body."""
    x0, x1 = -H, H + SIDE_T
    y0, y1 = -H - PLINTH, H
    outer = Pos((x0 + x1) / 2, (y0 + y1) / 2) * RectangleRounded(x1 - x0, y1 - y0, CORNER_R)
    inner = Pos((x0 - 1 + H - 0.5) / 2, (-H + 0.5 + y1 + 1) / 2) * Rectangle(H - 0.5 - (x0 - 1), y1 + 1 - (-H + 0.5))
    band = Pos(0, 0, L_Z0) * extrude(outer - inner, amount=BODY_Z1 - L_Z0)
    band = sfillet(band, band.edges().filter_by(Plane.XY), EDGE)
    # fill the body's rounded corners where they meet the L (no cusps)
    for cx, cy in ((H - CORNER_R, -H + CORNER_R), (-H + CORNER_R, -H + CORNER_R), (H - CORNER_R, H - CORNER_R)):
        sx = 1 if cx > 0 else -1
        sy = 1 if cy > 0 else -1
        band += box_at(cx, cx + sx * CORNER_R, cy, cy + sy * CORNER_R, BODY_Z0, BODY_Z1)
    return band


WORDMARK = "CALEGARI VIEW 1"
WORDMARK_X = (TOP_HANDLE_X[0] + TOP_HANDLE_X[1]) / 2
WORDMARK_Y = H + HANDLE_H - HANDLE_BAR / 2   # engraved on the front of the handle bar, like a top plate
BRAND_DOT_D = 3.2


def wordmark(depth=0.5, size=5.0, tracking=1.1):
    """Spaced capitals, engraved into the front face of the base (prints on the bed: sharp)."""
    letters, x = [], 0.0
    for ch in WORDMARK:
        if ch == " ":
            x += size * 0.55
            continue
        t = Text(ch, font_size=size, font="Helvetica Neue", font_style=FontStyle.BOLD,
                 align=(Align.MIN, Align.CENTER))
        w = t.bounding_box().size.X
        letters.append(Pos(x, 0) * t)
        x += w + tracking
    width = x - tracking
    x0 = -width / 2 + (BRAND_DOT_D + 3.0) / 2
    x0 += WORDMARK_X
    face = Compound([Pos(x0, WORDMARK_Y) * l for l in letters])
    text = Pos(0, 0, BODY_Z1 - depth) * extrude(face, amount=depth + 0.3)
    dot_x = x0 - 3.0 - BRAND_DOT_D / 2
    return text, dot_x


def brand_dot(lift=None):
    _, dx = wordmark()
    return Pos(dx, WORDMARK_Y, BODY_Z1) * dot(BRAND_DOT_D, 0.6, lift=lift)


def body_vial():
    """Bull's-eye vial in the -X face (portrait level)."""
    return bullseye((-H, SIDE_LEVEL[0], SIDE_LEVEL[1]), "-x")


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
    for x in BLADE_GUIDES_X:                         # M3 x 5 countersunk, Loctite 222 into the brass
        g -= insert_hole(x, BLADE_Y0 + 4.0, z0, "-z", depth=3.6)
    g -= insert_hole(*WHEEL_XY, z0, "-z", depth=3.6)
    # module screws (countersunk from the rear face)
    for x, y in GF_SCREWS:
        g -= cyl_z(1.7, z0 - 1, z1 + 1, x, y)
        g -= Pos(x, y, z0 - 0.01) * Cone(3.45, 1.7, 1.75, align=Z_UP)
    # 0.3 mm chamfer on the seat-face edges (they print on the bed: no elephant foot where the back seats)
    g = schamfer(g, [e for e in g.edges() if abs(e.center().Z - z1) < 0.01], 0.3)
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
        top = Pos(c[0], c[1], z0 - 0.01) * SlotCenterToCenter(BLADE_TRAVEL, 6.9, rotation=90)
        bot = Pos(c[0], c[1], z0 + 1.75) * SlotCenterToCenter(BLADE_TRAVEL, 3.4, rotation=90)
        blade -= loft([top, bot])
    blade = sfillet(blade, blade.edges().filter_by(Axis.Z), 0.6)
    return Pos(0, oy, 0) * blade


def graflok_wheel():
    """Knurled thumbwheel that clamps the blade (M3 screw into the module insert)."""
    z1 = GF_Z0 - 2.2
    w = cyl_z(7.0, z1 - 3.0, z1)
    for i in range(24):
        w -= Rot(0, 0, i * 15) * Pos(7.3, 0, z1 - 1.5) * Cylinder(0.7, 4)
    w -= cyl_z(1.7, z1 - 4, z1 + 1)
    # hex pocket for an M3 x 6 hex-head bolt (DIN 933): turning the wheel turns the bolt and clamps the blade
    w -= Pos(0, 0, z1 - 3.1) * extrude(hexagon(5.5 + 0.2), amount=2.1)
    w -= Pos(0, 0, z1 - 3.01) * Cone(3.65, 3.3, 0.35, align=Z_UP)                  # lead-in (bed face)
    return Pos(*WHEEL_XY, 0) * w


# --------------------------------------------------------------------------
# Y PLATE (rise and fall), front face on the bed
# --------------------------------------------------------------------------
X_CHAN = (-(SHIFT_X + 9.3) - X_THRUST, SHIFT_X + 9.3)   # turret travel = hard stops (the thrust nut on the right)
X_FLOOR = X_SCREW_Z - NUT_AF / 2 - NUT_FLOAT - 0.8   # channel floor: 0.8 under the drive nut
X_DETENT = (-50.0, -52.0)            # off to the side: its through hole stays outside both velvets
Y_TURRET_SCREWS = ((Y_SCREW_X, -6.5), (Y_SCREW_X, 6.5))


# --------------------------------------------------------------------------
# DOVETAIL WAYS. Profiles in (u, w): u outward from the axis of travel, w above the face the rail
# sits on. The rails print lying on their outer face, so the flanks are perimeters, not layers.
# --------------------------------------------------------------------------
def way_run(lip):
    return lip / math.tan(math.radians(WAY_ANG))


def gib_wall(stage):
    """u of the wall behind the gib strip (the grubs come through it)."""
    lip = Y_LIP if stage == "y" else X_LIP
    return WAY_UI + way_run(lip) + GIB_T[stage] + GIB_BACK


def way_profile(lip, h, gib, stage="y"):
    r, ui, uo, fl, fi = way_run(lip), WAY_UI, WAY_UO, WAY_FL, WAY_FL_IN
    if not gib:
        return [(fi, 0), (uo, 0), (uo, h), (ui, h), (ui, fl + lip), (ui + r, fl), (fi, fl)]
    uw = gib_wall(stage)
    return [(fi, 0), (uo, 0), (uo, h), (ui, h), (ui, fl + lip + 0.1), (uw, fl + lip + 0.1), (uw, fl), (fi, fl)]


def gib_profile(lip, stage):
    r, ui, fl, g = way_run(lip), WAY_UI, WAY_FL, GIB_T[stage]
    # the acute edge at the top of the flank is cut back 0.3 mm (it prints on the bed: no bead on the flank)
    return [(ui + r, fl), (ui + r + g, fl), (ui + r + g, fl + lip), (ui + 0.35, fl + lip),
            (ui + 0.3 / math.tan(math.radians(WAY_ANG)), fl + lip - 0.3)]


def lip_cut_profile(lip, top):
    """What is removed along a plate edge, leaving the dovetail lip (plate rear at w = WAY_FL)."""
    r, ui, uo, fl = way_run(lip), WAY_UI, WAY_UO, WAY_FL
    c = FLANK_C / math.sin(math.radians(WAY_ANG))
    ch = 0.4                                          # chamfer on the lip's bottom edge (elephant foot)
    return [(ui + r - c - ch, fl - 2), (uo + 2, fl - 2), (uo + 2, top), (ui - EDGE_C, top), (ui - EDGE_C, fl + lip),
            (ui - c, fl + lip), (ui + r - c - ch / math.tan(math.radians(WAY_ANG)), fl + ch), (ui + r - c - ch, fl)]


def prism(pts, stage, side, z0, a0, a1):
    """Extrude a (u, w) profile along the travel: stage 'y' runs along Y with u = side * X,
    stage 'x' runs along X with u = side * Y; w is measured from z0."""
    if stage == "y":
        face = make_face(Polyline(*[(side * u, a0, z0 + w) for u, w in pts], close=True))
        return extrude(face, amount=a1 - a0, dir=(0, 1, 0))
    face = make_face(Polyline(*[(a0, side * u, z0 + w) for u, w in pts], close=True))
    return extrude(face, amount=a1 - a0, dir=(1, 0, 0))


def way_stage(stage):
    return (Y_LIP, Y_WAY_H, BODY_Z1) if stage == "y" else (X_LIP, XP_Z1 - YP_Z1, YP_Z1)


def way_rail(stage, side, gib):
    """Y stage: +X rail fixed, -X rail with the gib. X stage: bottom rail fixed, top rail with the gib."""
    lip, h, z0 = way_stage(stage)
    r = prism(way_profile(lip, h, gib, stage), stage, side, z0, -H, H)
    su = side * WAY_SCREW_U
    if stage == "y":                                  # M2.5 countersunk from the top into the body inserts
        for yy in Y_WAY_SCREWS[side]:
            r -= cyl_z(1.45, z0 - 1, z0 + h + 1, su, yy)
            r -= Pos(su, yy, z0 + h - 1.25) * Cone(1.4, 2.65, 1.26, align=Z_UP)
    else:                                             # M2.5 inserts in the base, screws from the Y plate rear
        for xx in X_WAY_SCREWS:
            r -= insert_hole(xx, side * X_WAY_SCREW_U, z0, "-z", depth=6.2, d=3.3)
    if gib:                                           # three cone-point grubs push the gib strip
        uw = gib_wall(stage)
        zc = z0 + WAY_FL + lip / 2
        for a in GIB_GRUBS[stage]:
            if stage == "y":
                r -= cyl_x(1.25, side * (uw - 0.5), side * (WAY_UO + 1), a, zc)
            else:
                r -= cyl_y(1.25, side * (uw - 0.5), side * (WAY_UO + 1), a, zc)
    # round the outer ends where the part they sit on is rounded
    ends = []
    for e in r.edges().filter_by(Axis.Z):
        c = e.center()
        u_ = abs(c.X) if stage == "y" else abs(c.Y)
        a_ = c.Y if stage == "y" else c.X
        if abs(u_ - WAY_UO) < 0.01 and abs(abs(a_) - H) < 0.01:
            if stage == "x" or (side < 0 and a_ > 0):
                ends.append(e)
    if ends:
        r = sfillet(r, ends, CORNER_R)
    if stage == "y":                                  # clearance for the shift knob and the cap-nut washer
        cham = [(WAY_UO - 1.2, h + 0.01), (WAY_UO + 0.01, h + 0.01), (WAY_UO + 0.01, h - 1.2)]
        r -= prism(cham, "y", side, z0, -H - 1, H + 1)
    if stage == "x" and not gib:                      # shift index, read against the dots of the lens panel
        r -= Pos(*X_INDEX, z0 + h) * dot(2.6, 0.6)
    return r


def way_x_index_inlay():
    return Pos(*X_INDEX, XP_Z1) * dot(2.6, 0.6, lift=0)


def gib_strip(stage, side):
    """Gib strip with a dimple under each grub: the cone points keep it from walking endwise."""
    lip, _, z0 = way_stage(stage)
    g = prism(gib_profile(lip, stage), stage, side, z0, -H + 0.5, H - 0.5)
    ub = WAY_UI + way_run(lip) + GIB_T[stage]          # back face of the strip
    zc = z0 + WAY_FL + lip / 2
    for a in GIB_GRUBS[stage]:
        tip = Cone(1.3, 0.3, 0.7, align=Z_UP)            # conical dimple for the cone-point grub
        if stage == "y":
            g -= Pos(side * (ub + 0.01), a, zc) * orient(tip, "-x" if side > 0 else "+x")
        else:
            g -= Pos(a, side * (ub + 0.01), zc) * orient(tip, "-y" if side > 0 else "+y")
    return g


def y_plate_part():
    p = slab(PLATE, PLATE, YP_Z0, YP_Z1)
    h0, h1 = opening_yplate(YP_Z0), opening_yplate(YP_Z1)
    p -= rect_loft(YP_Z0 - 0.5, h0, YP_Z1 + 0.5, (h1[0], max(h1[1], 33.0)))
    for z in (25.0, 29.0):
        hz = opening_yplate(z)
        p -= box_at(-hz[0] - 1.4, hz[0] + 1.4, -hz[1] - 1.4, hz[1] + 1.4, z, z + 2.0)
    # dovetail lips on both side edges; the front part overhangs the rails
    for s_ in (-1, 1):
        p -= prism(lip_cut_profile(Y_LIP, Y_WAY_H + EDGE_C), "y", s_, BODY_Z1, -H - 1, H + 1)

    # nut turret: a separate part in the body channel, pulled against the plate rear by two screws
    for x, y in Y_TURRET_SCREWS:
        p -= cyl_z(1.7, YP_Z0 - 1, YP_Z1 + 1, x, y)
        p -= cyl_z(3.0, YP_Z1 - 3.3, YP_Z1 + 1, x, y)
    # rear relief for the rise knob (top-left corner) at full rise: the knob's own cylinder + 0.8
    p -= cyl_y(KNOB_D / 2 + 0.8, H - RISE - 2, H + 1, Y_SCREW_X, Y_SCREW_Z)
    # lead-in on the rear top and bottom edges: the plate slides over the body velvet without lifting it
    for sy_ in (-1, 1):
        lead = make_face(Polyline((-H - 1, sy_ * (H + 0.01), YP_Z0 - 0.01), (-H - 1, sy_ * (H - 2.0), YP_Z0 - 0.01),
                                  (-H - 1, sy_ * (H + 0.01), YP_Z0 + 1.15), close=True))
        p -= extrude(lead, amount=2 * H + 2, dir=(1, 0, 0))
    # rear detent dimple
    p -= Pos(*Y_DETENT, YP_Z0 - 0.01) * Cone(0.9, 0.25, 0.37, align=Z_UP)   # 0.35 deep conical seat for the ball
    # the horizontal rails are screwed from the rear (M2.5 x 16; 3.8 mm holes on the gib side: it floats)
    for s_ in (-1, 1):
        for xx in X_WAY_SCREWS:
            p -= cyl_z(1.45 if s_ < 0 else 1.9, YP_Z0 - 1, YP_Z1 + 1, xx, s_ * X_WAY_SCREW_U)
            p -= cyl_z(2.45, YP_Z0 - 1, YP_Z0 + 3.5, xx, s_ * X_WAY_SCREW_U)

    # horizontal screw channel (top): the floor clears the drive nut by 0.8 mm; bushings in the end walls;
    # the rod enters from the knob side (photographer's right) and ends in a blind seat on the left:
    # nothing shows on the left edge
    p -= box_at(X_CHAN[0], X_CHAN[1], X_SCREW_Y - CHAN_W / 2, X_SCREW_Y + CHAN_W / 2, X_FLOOR, YP_Z1 + 1)
    p -= cyl_x(BUSH_OD / 2 + 0.05, X_CHAN[0] - BUSH_L, X_CHAN[0] + 0.1, X_SCREW_Y, X_SCREW_Z)
    p -= cyl_x(BUSH_OD / 2 + 0.05, X_CHAN[1] - 0.1, X_CHAN[1] + BUSH_L, X_SCREW_Y, X_SCREW_Z)
    p -= cyl_x(ROD_D / 2 + 0.4, X_CHAN[1] + BUSH_L - 0.1, X_CHAN[1] + BUSH_L + 1.5, X_SCREW_Y, X_SCREW_Z)   # room for the rod tip
    p -= cyl_x(ROD_D / 2 + 0.4, -H - 1, X_CHAN[0], X_SCREW_Y, X_SCREW_Z)
    p -= cyl_x(4.6, -H - 1, -H + ORING_SEAT, X_SCREW_Y, X_SCREW_Z)

    # front: detent plunger for the lens panel, a through hole (set it from behind)
    p -= Pos(*X_DETENT, YP_Z1) * dot(4.2, YP_T + 1.0, "+z")

    # Y scale dots on the right edge
    # (the dot that stands at the body's index reads the shift: 10 mm below zero = 10 mm of rise)
    for mm in range(-int(RISE), int(FALL) + 1, 5):
        p -= Pos(-H, mm, YP_Z1 - 4.5) * dot(3.2 if mm == 0 else 2.0, 0.6, "-x")
    return p


def y_turret():
    """Nut turret of the rise screw: runs in the body channel, screwed to the Y plate from the front."""
    t = box_at(Y_SCREW_X - CHAN_W / 2 + 1, Y_SCREW_X + CHAN_W / 2 - 1, -10, 10, CHAN_FLOOR_Y + 0.8, YP_Z0)
    t = sfillet(t, t.edges().filter_by(Axis.Y), 1.0)
    t -= cyl_y(ROD_D / 2 + 0.8, -11, 11, Y_SCREW_X, Y_SCREW_Z)
    nut_r = (NUT_AF + 2 * NUT_FLOAT) / 2 / math.cos(math.pi / 6)
    t -= Pos(Y_SCREW_X, -NUT_T / 2 - 0.15, Y_SCREW_Z) * Rot(-90, 0, 0) * Rot(0, 0, 90) * extrude(
        RegularPolygon(nut_r, 6), amount=NUT_T + 0.3)
    t -= box_at(Y_SCREW_X, Y_SCREW_X + CHAN_W, -NUT_T / 2 - 0.15, NUT_T / 2 + 0.15,
                CHAN_FLOOR_Y - 1.0, Y_SCREW_Z + NUT_AF / 2 + NUT_FLOAT)      # open through the bottom: no film
    t -= box_at(Y_SCREW_X - 6.5, Y_SCREW_X + 6.5, -NUT_T / 2 - 0.15, NUT_T / 2 + 0.15, CHAN_FLOOR_Y - 1.0, Y_SCREW_Z - 4.0)
    for x, y in Y_TURRET_SCREWS:
        t -= insert_hole(x, y, YP_Z0, "+z")
    return t


def y_plate_inlays():
    """Zero dot and X index red, other dots white (separate bodies for multi-material)."""
    red = Compound([Pos(-H, 0, YP_Z1 - 4.5) * dot(3.2, 0.6, "-x", lift=0)])
    white = Compound([Pos(-H, mm, YP_Z1 - 4.5) * dot(2.0, 0.6, "-x", lift=0)
                      for mm in range(-int(RISE), int(FALL) + 1, 5) if mm])
    return red, white


# --------------------------------------------------------------------------
# LENS PANEL (X plate): back face on the bed; metal M65 flange flush with the front
# --------------------------------------------------------------------------
TURRET_KEY = 2.5                      # depth of the shift-turret pocket in the lens panel rear
STOP_R = 52.0                         # the stop pin runs in a groove under the focus ring: nothing shows
STOP_PIN = (-STOP_R * math.sqrt(0.5), -STOP_R * math.sqrt(0.5))   # at 225 deg
INDEX_R = FOCUS_OD / 2 + 2.2          # focus index and depth-of-field dots
X_SCALE_Y = -61.0                     # shift dots on the lens panel front; the index is on the bottom rail
X_INDEX = (0.0, -68.5)
TURRET_SCREWS = ((-5.5, X_SCREW_Y + 5.0), (5.5, X_SCREW_Y + 5.0))


def x_plate_outline():
    """Lens panel: full width where it seals the light path and over the guide; the two top
    corners are cut so the shift knob can pass at full travel."""
    nx, ny = XP_NOTCH
    pts = [(-H, -H), (H, -H), (H, ny), (nx, ny), (nx, H), (-nx, H), (-nx, ny), (-H, ny)]
    return make_face(Polyline(*pts, close=True))


def x_plate_part():
    z0, z1 = XP_Z0, XP_Z1
    p = Pos(0, 0, z0) * extrude(x_plate_outline(), amount=z1 - z0)
    p = sfillet(p, p.edges().filter_by(Axis.Z), CORNER_R)
    p = sfillet(p, p.edges().filter_by(Plane.XY), EDGE)
    # metal flange pocket, flush with the front; bore behind it
    p -= cyl_z(FLANGE_D / 2 + FIT, z1 - FLANGE_T, z1 + 1)
    p -= cyl_z(31.5, z0 - 1, z1)
    # light trap: a groove in the pocket floor just inside the flange edge
    p -= cyl_z(38.6, z1 - FLANGE_T - 0.8, z1 - FLANGE_T + 0.01) - cyl_z(37.4, z1 - FLANGE_T - 1, z1)
    # flare lobes on the diagonals, between the flange screws: the corner rays at large combined shifts
    # (and the bore reads as a knife-edge baffle instead of a flat wall)
    zf = z1 - FLANGE_T
    # cone from r37.5 at the rear face, stopped 0.6 mm under the flange seat and finished with a short
    # cylinder, so the seat keeps a real edge (no feather that curls up under the flange)
    zc_ = zf - 0.6
    r_c = 32.3 + 0.6 * (37.5 - 32.3) / (zf - z0)
    lobe = Pos(0, 0, z0 - 0.01) * Cone(37.5, r_c, zc_ - z0 + 0.01, align=Z_UP) + cyl_z(r_c, zc_ - 0.01, zf + 0.01)
    for a in (45, 135, 225, 315):
        wedge = Rot(0, 0, a) * extrude(make_face(Polyline((0, 0), (60 * math.cos(math.radians(-30)), 60 * math.sin(math.radians(-30))),
                                                            (60 * math.cos(math.radians(30)), 60 * math.sin(math.radians(30))), close=True)),
                                       amount=40)
        p -= lobe & (Pos(0, 0, z0 - 5) * wedge)
    # flange screws: 4 x M3 countersunk from the rear, into the flange's M3 holes
    for a in (0, 90, 180, 270):
        x, y = FLANGE_PCD / 2 * math.cos(math.radians(a)), FLANGE_PCD / 2 * math.sin(math.radians(a))
        p -= cyl_z(1.7, z0 - 1, z1, x, y)
        p -= Pos(x, y, z0 - 0.01) * Cone(3.45, 1.7, 1.75, align=Z_UP)
    # dovetail lips top and bottom, between the two horizontal rails
    for s_ in (-1, 1):
        p -= prism(lip_cut_profile(X_LIP, XP_Z1 - YP_Z1 + 2), "x", s_, YP_Z1, -H - 1, H + 1)
    # the nut turret sits 2.5 mm deep in a pocket (the hard stops bear on its walls, not on the glue),
    # bonded with epoxy and located by two pegs
    p -= box_at(-9.15, 9.15, X_SCREW_Y - CHAN_W / 2 + 0.85, X_SCREW_Y + CHAN_W / 2 - 0.85, z0 - 1, z0 + TURRET_KEY)
    p -= box_at(-9.45, 9.45, X_SCREW_Y - CHAN_W / 2 + 0.55, X_SCREW_Y + CHAN_W / 2 - 0.55, z0 - 1, z0 + 0.3)   # lead-in
    for x, y in TURRET_SCREWS:
        p -= cyl_z(2.05, z0 + TURRET_KEY - 0.01, z0 + TURRET_KEY + 2.3, x, y)
    # 0.5 mm relief over the shift rod: the thrust washer and nut turn under the panel's right half
    p -= box_at(X_CHAN[0] - SHIFT_X - 0.8, -9.0, X_SCREW_Y - 3.0, X_SCREW_Y + 3.0, z0 - 1, z0 + 0.5)
    # rear detent dimple
    p -= Pos(*X_DETENT, z0 - 0.01) * Cone(0.9, 0.25, 0.37, align=Z_UP)
    # infinity stop pin (M3 x 4 socket screw standing on the front)
    p -= insert_hole(*STOP_PIN, z1, "+z", depth=5.5)
    # depth-of-field dots (f/11 small, f/22 large) and the focus index (red) above the ring
    r = INDEX_R
    p -= Pos(0, r, z1) * dot(3.4, 0.6)
    for n, dd in ((11, 1.8), (22, 2.6)):
        for s in (-1, 1):
            p -= Rot(0, 0, s * dof_angle(n)) * (Pos(0, r, z1) * dot(dd, 0.6))
    # X scale on the front, along the bottom rail (its index is on the rail)
    for mm in range(-25, 26, 5):
        p -= Pos(mm, X_SCALE_Y, z1) * dot(3.2 if mm == 0 else 2.0, 0.6)
    return p


def x_plate_inlays():
    r = INDEX_R
    red = [Pos(0, r, XP_Z1) * dot(3.4, 0.6, lift=0), Pos(0, X_SCALE_Y, XP_Z1) * dot(3.2, 0.6, lift=0)]
    white = []
    for n, dd in ((11, 1.8), (22, 2.6)):
        for s in (-1, 1):
            white.append(Rot(0, 0, s * dof_angle(n)) * (Pos(0, r, XP_Z1) * dot(dd, 0.6, lift=0)))
    for mm in range(-25, 26, 5):
        if mm:
            white.append(Pos(mm, X_SCALE_Y, XP_Z1) * dot(2.0, 0.6, lift=0))
    return Compound(red), Compound(white)


def x_turret():
    """Nut turret of the shift screw, bonded to the lens panel rear; runs in the Y plate channel.
    The nut goes in from below (the panel lies face down on the bench when it is fitted)."""
    zt = XP_Z0 + TURRET_KEY
    zb = X_FLOOR + 0.8
    t = box_at(-9, 9, X_SCREW_Y - CHAN_W / 2 + 1, X_SCREW_Y + CHAN_W / 2 - 1, zb, zt)
    t = sfillet(t, t.edges().filter_by(Axis.X), 1.0)
    t -= cyl_x(ROD_D / 2 + 0.8, -10, 10, X_SCREW_Y, X_SCREW_Z)
    nut_r = (NUT_AF + 2 * NUT_FLOAT) / 2 / math.cos(math.pi / 6)
    t -= Pos(-NUT_T / 2 - 0.15, X_SCREW_Y, X_SCREW_Z) * Rot(0, 90, 0) * Rot(0, 0, 90) * extrude(
        RegularPolygon(nut_r, 6), amount=NUT_T + 0.3)
    t -= box_at(-NUT_T / 2 - 0.15, NUT_T / 2 + 0.15, X_SCREW_Y - NUT_AF / 2 - NUT_FLOAT,
                X_SCREW_Y + NUT_AF / 2 + NUT_FLOAT, zb - 1, X_SCREW_Z)
    for x, y in TURRET_SCREWS:                        # two locating pegs for the bond
        t += cyl_z(1.9, zt - 0.01, zt + 2.0, x, y)
    return t


# --------------------------------------------------------------------------
# FOCUS RING (front face on the bed), infinity stop, dots on the rim
# --------------------------------------------------------------------------
FOCUS_DIST = (("inf", 0.0), ("5", 5), ("3", 3), ("2", 2), ("1.5", 1.5), ("1", 1), ("0.7", 0.7))
LEVER_ANG = -95.0
STOP_TAB_ANG = 225.0 - 6.0 * FOCUS_DIR   # the block meets the stop pin (at 225 deg) at infinity


def focus_ring_part():
    z0 = HELI_Z0 + HELI_GRIP_Z[0]
    r = FOCUS_OD / 2
    ring = cyl_z(r, z0, z0 + FOCUS_W) - cyl_z(HELI_OD / 2 + 0.2, z0 - 1, z0 + FOCUS_W + 1)
    ring = sfillet(ring, [e for e in ring.edges().filter_by(GeomType.CIRCLE) if e.radius > 55], EDGE)
    # the bore edge on the front face prints on the bed: chamfer it (elephant foot on a 0.2 mm fit)
    ring = schamfer(ring, [e for e in ring.edges().filter_by(GeomType.CIRCLE)
                           if e.radius < 40 and abs(e.center().Z - (z0 + FOCUS_W)) < 0.01], 0.4)
    # grip: flutes except on the scale sector
    for i in range(0, 360, 10):
        a = (((i + 180) % 360) - 180) * FOCUS_DIR
        if -10 < a < 175:
            continue
        ring -= Rot(0, 0, -i) * (Pos(0, r + 0.4, z0 + FOCUS_W / 2) * Box(2.0, 2.0, FOCUS_W - 3))
    # focusing tab, Leica style: a round nub (starts 2 mm up: clears the lens panel)
    zt0 = z0 + 2.0
    nub = Pos(0, r + 3.0, zt0) * Cylinder(6.0, FOCUS_W - 2.0, align=Z_UP) + Pos(0, r - 1.0, zt0 + (FOCUS_W - 2) / 2) * Box(12, 8, FOCUS_W - 2)
    nub = sfillet(nub, [e for e in nub.edges() if e.center().Z > zt0 + FOCUS_W - 2.5], 1.5)
    ring += Rot(0, 0, -LEVER_ANG) * nub
    # infinity stop, hidden: a groove in the rear face with one solid block; the pin on the lens panel
    # runs in the groove and meets the block at infinity (set by turning the ring on the helicoid)
    groove = cyl_z(STOP_R + 4.0, z0 - 1, z0 + 2.5) - cyl_z(STOP_R - 4.0, z0 - 2, z0 + 3)
    block = Rot(0, 0, -STOP_TAB_ANG) * (Pos(0, STOP_R, z0 + 1) * Box(5.0, 8.4, 5.0))
    ring -= groove - block
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
ADAPTER_SCREW_R = 48.5                 # holder-to-adapter screws: from the front, under the board
ADAPTER_BOSSES = tuple(range(0, 360, 45))   # 8 inserts in the adapter
HOLDER_SLOTS = (45, 135, 225, 315)         # 4 arc slots in the holder, +/-25 deg: always an insert under each
STUB_L = 5.5
ADAPTER_BOSS = 5.5                     # flange + boss depth at the inserts (the flange can be reprinted thinner)
LATCH_ENGAGE = 4.0


def holder_part():
    z0, z1 = HOLDER_Z0, BOARD_Z1
    h = extrude(Pos(0, 9.5, z0) * RectangleRounded(HOLDER_W, HOLDER_H, CORNER_R), amount=z1 - z0)
    h = sfillet(h, h.edges().group_by(Axis.Z)[-1], EDGE)
    h -= box_at(-BOARD_W / 2 - FIT, BOARD_W / 2 + FIT, -BOARD_H / 2 - FIT, BOARD_H / 2 + FIT, BOARD_Z0, z1 + 1)
    h -= cyl_z(REAR_CLEAR_D / 2, z0 - 1, z1 + 1)
    h -= cyl_z(REAR_CLEAR_D / 2 + 3.5, BOARD_Z0 - 1.6, BOARD_Z0 + 0.1)        # board light-trap ring
    h -= cyl_z(45.6, BOARD_Z0 - 0.9, BOARD_Z0 + 0.1)                          # seat of a 1 mm felt ring (V4)
    # groove for a 1 mm felt ring against the adapter flange (V3)
    h -= cyl_z(37.0, z0 - 0.1, z0 + 0.8) - cyl_z(31.0, z0 - 1, z0 + 2)
    # four arc slots through the board seat (screws from the front, heads under the board): the holder
    # turns +/-25 deg on the adapter, and with eight inserts in the adapter every slot always finds one
    for a in HOLDER_SLOTS:
        h -= arc_slot(ADAPTER_SCREW_R, a, 25.0, 1.7, z0 - 1, BOARD_Z0 + 1)
        h -= arc_slot(ADAPTER_SCREW_R, a, 25.0, 3.1, BOARD_Z0 - 2.0, BOARD_Z0 + 1)
    # bottom lips, anchored on the frame, 0.3 mm over the board, chamfered underneath (print without sag)
    for sx_ in (-1, 1):
        h += box_at(sx_ * 30 - 9, sx_ * 30 + 9, -BOARD_H / 2 - 4, -BOARD_H / 2 - 0.2, z1 - 0.01, z1 + 1.8)
        lip = box_at(sx_ * 30 - 9, sx_ * 30 + 9, -BOARD_H / 2 - 0.5, -BOARD_H / 2 + 2.0, z1 + 0.3, z1 + 1.8)
        lip = schamfer(lip, [e for e in lip.edges().filter_by(Axis.X)
                             if e.center().Y > -BOARD_H / 2 + 1.9 and e.center().Z < z1 + 0.4], 1.4)
        h += lip
    # spring latch, no hardware in sight: the latch slides in a 45 degree dovetail between two rails, the
    # spring sits under a hood, and two M2.5 screws from the rear stand 1 mm proud of the front face as
    # pins in two blind grooves under the latch (the groove ends are its stops, both ways)
    for s in (-1, 1):
        prof = [(s * 18.0, z1 - 0.01), (s * 15.6, z1 - 0.01), (s * 12.95, z1 + 2.65), (s * 12.95, z1 + 4.0), (s * 18.0, z1 + 4.0)]
        face = make_face(Polyline(*[(x, BOARD_H / 2 - 0.2, z) for x, z in prof], close=True))
        h += extrude(face, amount=26.2, dir=(0, 1, 0))
    for x in (-9.0, 9.0):
        h -= cyl_z(1.05, z0 - 1, z1 + 0.1, x, LATCH_SCREW_Y)                 # the screw forms its thread
        h -= cyl_z(2.6, z0 - 0.1, z0 + 1.6, x, LATCH_SCREW_Y)                # head flush with the rear
    h -= cyl_y(2.2, BOARD_H / 2 + 9.0, BOARD_H / 2 + 22.5, 0.0, z1 + 1.3)                # spring channel
    h += box_at(-4.0, 4.0, BOARD_H / 2 + 22.0, BOARD_H / 2 + 26.0, z1 - 0.01, z1 + 4.0)   # spring abutment
    # hood over the spring, rail to rail: it starts 1 mm over the top of the closed latch, so the spring
    # never shows, and the latch slides under it when it is pulled up
    hood = box_at(-18.0, 18.0, BOARD_H / 2 + 9.0, BOARD_H / 2 + 26.0, z1 + 4.0, z1 + 5.2)
    hood = sfillet(hood, hood.edges().filter_by(Axis.Y), 0.6)
    h += hood
    return h


def arc_slot(r, a, half, w, z0, z1):
    """Slot of half-width w along a circle of radius r, centred at angle a, +/-half degrees."""
    ring = Circle(r + w) - Circle(r - w)
    sector = make_face(Polyline((0, 0), *[(3 * r * math.cos(math.radians(a + t)), 3 * r * math.sin(math.radians(a + t)))
                                          for t in (-half, -half / 2, 0, half / 2, half)], close=True))
    face = ring & sector
    for t in (-half, half):
        face += Pos(r * math.cos(math.radians(a + t)), r * math.sin(math.radians(a + t))) * Circle(w)
    return Compound([extrude(f, amount=z1 - z0, dir=(0, 0, 1)) for f in (Pos(0, 0, z0) * face).faces()])


LATCH_LEN = 14.0
LATCH_SCREW_Y = BOARD_H / 2 + 7.0        # under the latch: the groove ends are its stops, both ways


def holder_latch(locked=True):
    """Spring slider: pull up to release, a spring (4 x 15) pushes it back with 4 mm engagement. The lower
    front edge is chamfered: a board pressed in pushes the latch up and it snaps back over it."""
    z0 = BOARD_Z1 + 0.05
    oy = 0.0 if locked else LATCH_ENGAGE + 1.0
    y0, y1 = BOARD_H / 2 - LATCH_ENGAGE, BOARD_H / 2 - LATCH_ENGAGE + LATCH_LEN
    prof = [(-15.0, z0), (15.0, z0), (15.0, z0 + 0.2), (12.8, z0 + 2.4), (-12.8, z0 + 2.4), (-15.0, z0 + 0.2)]
    l = extrude(make_face(Polyline(*[(x, y0, z) for x, z in prof], close=True)), amount=y1 - y0, dir=(0, 1, 0))
    travel = LATCH_ENGAGE + 1.0
    for x in (-9.0, 9.0):                     # blind grooves in the rear face: the pins of the two screws
        l -= Pos(x, LATCH_SCREW_Y - travel / 2, z0 - 1) * extrude(SlotCenterToCenter(travel, 2.9, rotation=90), amount=1 + 1.8)
    l = schamfer(l, [e for e in l.edges().filter_by(Axis.X)
                     if abs(e.center().Y - y0) < 0.01 and abs(e.center().Z - (z0 + 2.4)) < 0.01], 1.2)
    grip = box_at(-5.5, 5.5, y0 + 2.0, y0 + 6.0, z0 + 2.39, z0 + 4.4)
    l += sfillet(grip, grip.edges().filter_by(Axis.X), 0.8)
    return Pos(0, oy, 0) * l


def adapter_part(with_thread=True, flange_t=ADAPTER_T):
    """Printed M65 adapter: male stub into the helicoid; the board holder is screwed to it from the front
    through arc slots (square the board, then tighten). It is the calibration part: every 0.5 mm less of
    flange is 0.5 mm more helicoid travel past infinity."""
    z1 = HOLDER_Z0
    z0 = z1 - flange_t
    f = cyl_z(ADAPTER_SCREW_R + 4.0, z0, z1) - cyl_z(REAR_CLEAR_D / 2, z0 - 1, z1 + 1)
    # eight bosses on the rear carry M3 inserts, set from the front face
    for a in ADAPTER_BOSSES:
        x, y = ADAPTER_SCREW_R * math.cos(math.radians(a)), ADAPTER_SCREW_R * math.sin(math.radians(a))
        f += cyl_z(3.6, z1 - ADAPTER_BOSS, z0 + 0.01, x, y)
        f -= insert_hole(x, y, z1, "+z", depth=4.8)
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
    """Leica-style: fine straight knurl, a smooth chamfered crown, one red dot."""
    d, h = KNOB_D, KNOB_H
    crown = 3.4
    k = Cylinder(d / 2, h, align=Z_UP)
    k = schamfer(k, k.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1], 1.0)
    k = schamfer(k, k.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[0], 0.4)
    L = h - crown - 1.2
    for i in range(36):                               # 36 flutes 0.5 deep: crisp with a 0.4 nozzle
        k -= Rot(0, 0, i * 10) * Pos(d / 2 + 0.25, 0, 0.8 + L / 2) * Cylinder(0.75, L)
    k -= cyl_z(d / 2 + 1, h - crown - 0.5, h - crown) - cyl_z(d / 2 - 0.35, h - crown - 1, h)   # hairline
    k -= Pos(0, 0, -0.1) * extrude(hexagon(NUT_AF + 0.3), amount=NUT_T + 0.3)
    k -= Pos(0, 0, -0.01) * Cone(NUT_AF / 2 / math.cos(math.pi / 6) + 0.6, NUT_AF / 2 / math.cos(math.pi / 6) + 0.15,
                                 0.45, align=Z_UP)     # lead-in chamfer on the nut pocket (it is the bed face)
    k -= cyl_z(ROD_D / 2 + 0.25, -1, h - 1.5)
    k -= Pos(0, 0, NUT_T + 3.0) * Rot(0, 90, 0) * Cylinder(1.25, d)          # M3 x 6 cone-point grub (steel)
    k -= cyl_z(d / 2 + 1, -0.1, 0.8) - cyl_z(7.0, -1, 2)                     # only the centre bears on the O-ring
    k -= Pos(0, -(d / 2 - 4.2), h) * dot(2.4, 0.6)
    index = Pos(0, -(d / 2 - 4.2), h) * dot(2.4, 0.6, lift=0)
    return k, index


# --------------------------------------------------------------------------
# HANDLES (printed on their side, bolted with M4 x 50 through the posts)
# --------------------------------------------------------------------------
def handle_loop(length, z0, z1, height=HANDLE_H, bar=HANDLE_BAR, post=HANDLE_POST, flare=HANDLE_FLARE):
    """Loop handle, profile in XY (u = X, protrusion +Y), extruded along Z. The feet flare into the
    body with concave fillets, so the handle reads as part of the camera."""
    outer = Pos(0, height / 2, 0) * Rectangle(length, height)
    inner = Pos(0, (height - bar) / 2 - 1, 0) * Rectangle(length - 2 * post, height - bar + 2)
    prof = outer - inner
    land = 0.8                                # the flares end in a flat, not a knife edge

    def flare_face(x_face, d):
        """Concave foot on a post face at x_face, flaring in direction d (+1/-1), as a faceted polygon."""
        cx, cy = x_face + d * flare, flare + land
        arc = [(cx - d * flare * math.cos(t), cy - flare * math.sin(t)) for t in [i * math.pi / 2 / 16 for i in range(17)]]
        pts = [(x_face, 0.0), (x_face + d * flare, 0.0)] + arc[::-1]
        return make_face(Polyline(*pts, close=True))

    for s in (-1, 1):
        prof += flare_face(s * length / 2, s)                 # outside of the post
        prof += flare_face(s * (length / 2 - post), -s)       # inside of the post
    h = Pos(0, 0, z0) * extrude(prof, amount=z1 - z0)
    h = sfillet(h, h.edges().filter_by(Axis.Z).group_by(Axis.Y)[-1], 6.0)
    h = sfillet(h, [e for e in h.edges().filter_by(Axis.Z) if abs(e.center().Y - (height - bar)) < 0.2], 4.0)
    h = sfillet(h, [e for e in h.edges().filter_by(Plane.XY) if e.center().Y > flare + 1.5], EDGE)
    return h


def handle_screw_holes(length, zc, height=HANDLE_H, post=HANDLE_POST):
    out = []
    for sx_ in (-1, 1):
        x = sx_ * (length / 2 - post / 2 - 1.5)
        out.append(Pos(x, -1, zc) * Rot(-90, 0, 0) * Cylinder(2.2, height + 2, align=Z_UP))
        out.append(Pos(x, height - 6.0, zc) * Rot(-90, 0, 0) * Cylinder(3.8, 8, align=Z_UP))
    return out


def top_handle():
    x0, x1 = TOP_HANDLE_X
    z0, z1 = TOP_HANDLE_Z
    h = handle_loop(x1 - x0, z0, z1)
    for c in handle_screw_holes(x1 - x0, HANDLE_INSERT_Z_TOP):
        h -= c
    # landscape level: 15 mm bull's-eye in the top of the bar, between the shoes (reads pitch and roll)
    h -= level_pocket((LEVEL_TOP_X - (x0 + x1) / 2, HANDLE_H, LEVEL_Z), "+y")
    # two ISO 518 accessory shoes, open to the rear (layers follow the slot: the lips print as walls)
    for xs in SHOES_X:
        u = xs - (x0 + x1) / 2
        h -= box_at(u - SHOE_OPEN / 2, u + SHOE_OPEN / 2, HANDLE_H - SHOE_LIP - 0.1, HANDLE_H + 1, z0 - 1, z0 + SHOE_L)
        h -= box_at(u - SHOE_W / 2, u + SHOE_W / 2, HANDLE_H - SHOE_LIP - SHOE_D, HANDLE_H - SHOE_LIP, z0 - 1, z0 + SHOE_L)
        lead = Pos(u, HANDLE_H - SHOE_LIP - SHOE_D / 2, z0) * Rot(0, 0, 0) * Box(SHOE_W + 2, SHOE_D + 1.2, 2.0)
        h -= lead
    h = Pos((x0 + x1) / 2, H, 0) * h
    text, _ = wordmark()
    return h - text - brand_dot()


SHOE_OPEN, SHOE_W, SHOE_D, SHOE_LIP, SHOE_L = 12.6, 18.9, 2.2, 1.6, 18.5
LEVEL_Z = 10.8


def bullseye(c, axis):
    """15 x 8 mm bull's-eye vial (for the render and the checks), top flush with its face."""
    v = Pos(0, 0, -LEVEL_H + 0.3) * Cylinder(7.5, LEVEL_H - 0.3, align=Z_UP)
    return Pos(*c) * orient(v, axis)


def top_vial():
    return bullseye((LEVEL_TOP_X, H + HANDLE_H, LEVEL_Z), "+y")


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
    """Same plate on the side leg of the L bracket (portrait)."""
    base = arca_plate()
    y_top = -H - PLINTH + ARCA_POCKET
    x_face = H + SIDE_T - ARCA_POCKET
    return Pos(x_face, SIDE_ARCA_YC, 0) * Rot(0, 0, 90) * Pos(0, -y_top, 0) * base


# --------------------------------------------------------------------------
# LIGHT SEAL MATERIALS (cut from velvet / felt sheet; see docs/templates)
# --------------------------------------------------------------------------
VELVET_T = GAP
V1_X = (-46.5, 45.5)                   # body velvet: from the plunger strip to the screw channel
V2_Y = (-45.5, 45.5)                   # Y plate velvet: from the detent to the shift channel


def velvet_body_outline():
    """Velvet on the body front face: a frame around the gate, clear of the channels and the pads."""
    op = opening_body(BODY_Z1)
    outer = Pos((V1_X[0] + V1_X[1]) / 2, 0) * Rectangle(V1_X[1] - V1_X[0], 144.0)
    hole = RectangleRounded(2 * (op[0] + 0.3), 2 * (op[1] + 0.3), 3.0)
    return outer - hole


def velvet_yplate_outline():
    """Velvet on the Y plate front face: a band around the opening, between the guide channel and the pads."""
    op = opening_yplate(YP_Z1)
    hy = max(op[1], 33.0)
    outer = Pos(0, (V2_Y[0] + V2_Y[1]) / 2) * Rectangle(144.0, V2_Y[1] - V2_Y[0])
    hole = RectangleRounded(2 * (op[0] + 0.3), 2 * (hy + 0.3), 3.0)
    face = outer - hole
    for x, y in Y_TURRET_SCREWS:                  # the turret screws go in through these; a disc then closes each
        face -= Pos(x, y) * Circle(3.5)
    return face


def velvet_discs():
    """Two 7 mm velvet discs laid on the rise-turret screw heads after tightening (they close the holes in V2)."""
    return Compound([Pos(x, y, YP_Z1) * Cylinder(3.45, VELVET_T, align=Z_UP) for x, y in Y_TURRET_SCREWS])


def velvet_body():
    return Pos(0, 0, BODY_Z1) * extrude(velvet_body_outline(), amount=VELVET_T)


def velvet_yplate():
    return Pos(0, 0, YP_Z1) * extrude(velvet_yplate_outline(), amount=VELVET_T)


def felt_board_outline():
    return Circle(44.8) - Circle(REAR_CLEAR_D / 2 + 3.6)


def felt_adapter_outline():
    return Circle(36.8) - Circle(31.2)


def felt_board():
    return Pos(0, 0, BOARD_Z0 - 0.8) * extrude(felt_board_outline(), amount=0.8)


# --------------------------------------------------------------------------
# LENS SHIMS: printed rings under the shutter flange, so every lens reaches infinity at the stop
# --------------------------------------------------------------------------
SHIM_STEPS = (0.4, 0.6, 0.8, 1.0, 1.2)     # print at 0.2 mm layers: every step is whole layers


def copal0_shim(t):
    """Ring between the shutter and the lens board front. The notches on the rim tell the thickness:
    count them and multiply by 0.2 mm."""
    ring = Circle(26.0) - Circle(35.4 / 2)
    n = round(t / 0.2)
    for i in range(n):
        ring -= Rot(0, 0, 90 + (i - (n - 1) / 2) * 9) * Pos(26.0, 0) * Rectangle(2.4, 1.6)
    return extrude(ring, amount=t)


def shrink_gauge():
    """100.0 x 100.0 mm frame for measuring the filament's XY shrinkage (tab marks the X side)."""
    g = extrude(Rectangle(100, 100) - Rectangle(88, 88), amount=3.0)
    g += Pos(0, -50 - 4, 0) * extrude(Rectangle(20, 8), amount=3.0)
    return g


# --------------------------------------------------------------------------
# BOUGHT PARTS (envelopes)
# --------------------------------------------------------------------------
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
