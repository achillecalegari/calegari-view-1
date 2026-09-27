"""Calegari View 1: every dimension of the camera, in millimetres.

Coordinate system
- Z: optical axis. 0 = film plane, +Z toward the subject.
- Y: up (landscape orientation, camera on the bottom Arca plate).
- X: photographer's LEFT (camera seen from behind). -X is the photographer's right,
  which is where the RB67 dark slide comes out.

Change a value here and rebuild: every part, check, plate and render follows.
"""
import math

# --------------------------------------------------------------------------
# Film and back (Mamiya RB67 Pro / Pro-S / Pro-SD, Graflok 23 family)
# --------------------------------------------------------------------------
FILM_W, FILM_H = 69.5, 56.0          # 6x7 image
GATE_W, GATE_H = 78.0, 60.0          # body gate at the seat (also clears 6x8)
SEAT_Z = 4.8                         # back's nose face seats here; film ~4.8 mm behind
GF_T = 4.7                           # Graflok module thickness (rear face 4.7 behind the seat)
GF_Z0 = SEAT_Z - GF_T                # rear face of body and module
POCKET_Y0, POCKET_Y1 = -39.3, 40.0   # nose pocket (reference: RB67 body tested with Pro-S/Pro-SD)
POCKET_WALL_X = 55.0                 # closed end of the pocket (photographer's left)
TRAP_X = (-47.5, -42.5)              # light-trap groove in the seat
TRAP_Y = (-36.0, 36.5)               # closed ends, shorter than the nose
TRAP_D = 1.5
SLIDE_RELIEF_X = -56.0               # dark-slide handle hooks: clear everything X < this ...
SLIDE_RELIEF_Y = 40.0                # ... for |Y| < this (hooks sit at |Y| 24..35) ...
SLIDE_RELIEF_Z = SEAT_Z + 3.5        # ... up to this z (hooks protrude 3.5 ahead of the nose face)
LIP_RELIEF_X = 44.0                  # relief for the back's top/bottom lips on the module rear face
LIP_RELIEF_Y = (51.0, 64.0)
LIP_RELIEF_D = 2.2

# --------------------------------------------------------------------------
# Lens and focusing
# --------------------------------------------------------------------------
F_LENS = 65.0
FFD = 70.5                           # shutter flange to film (SA 65/8 70.5, Nikkor-SW 70.8, Grandagon-N 70.0)
BOARD_W, BOARD_H, BOARD_T = 99.0, 96.0, 2.0   # Linhof Technika board
HOLDER_BACK_T = 4.5                  # board holder wall behind the board (1.2 mm skin over the inserts)
ADAPTER_T = 2.5                      # printed M65 adapter flange: the calibration part (reprint thinner if needed)
REAR_CLEAR_D = 59.0                  # bore of adapter and holder: Nikkor-SW 65/4 rear cell is 54 mm
HELI_MIN, HELI_MAX = 17.0, 31.0      # M65 helicoid 17-31
HELI_OD, HELI_BORE = 78.0, 61.0
HELI_ROT = 313.0                     # degrees for the full travel: MEASURE YOUR HELICOID
HELI_TRAVEL = HELI_MAX - HELI_MIN
FOCUS_DIR = 1
M65 = 65.0
FLANGE_D, FLANGE_T, FLANGE_PCD = 79.0, 5.0, 69.0   # RafCamera M65x1 female lens flange (metal)

BOARD_Z1 = FFD                       # board front = shutter flange at infinity
BOARD_Z0 = BOARD_Z1 - BOARD_T
HOLDER_Z0 = BOARD_Z0 - HOLDER_BACK_T
ADAPTER_Z0 = HOLDER_Z0 - ADAPTER_T   # helicoid front face at infinity
HELI_INF = 18.0                      # helicoid length at infinity (1 mm margin + adapter reprint for more)
HELI_Z0 = ADAPTER_Z0 - HELI_INF      # helicoid shoulder = lens panel front face

# --------------------------------------------------------------------------
# Shift stages
# --------------------------------------------------------------------------
RISE, FALL = 25.0, 8.0               # vertical travel: fall is limited by the tripod clamp
SHIFT_X = 25.0                       # lateral travel, both ways
OVERLAP_MOVE = 8.0                   # light seal overlap in the direction of motion
OVERLAP_FIXED = 4.0                  # ... and across it
GAP = 0.8                            # plate-to-plate gap: hard pads, velvet compressed in it

# MGN9H linear guides (HIWIN catalogue values)
RAIL_W, RAIL_H = 9.0, 6.5
BLOCK_W, BLOCK_L, BLOCK_H = 20.0, 39.9, 10.0      # H: rail bottom to block top
BLOCK_HOLES = (15.0, 16.0)                        # 4 x M3, B x C
BLOCK_UNDER = 2.0                                 # block underside above rail bottom
RAIL_LEN_Y, RAIL_Y_OFFSET = 118.0, 8.5              # vertical rail, asymmetric travel
RAIL_LEN_X = 134.0
RAIL_HOLE_PITCH = 20.0
BLOCK_PITCH = 42.0                                # two blocks per rail (L 39.9)

# M6 drive screws
ROD_D = 6.0
NUT_AF, NUT_T = 10.0, 5.0
NUT_FLOAT = 0.5                                   # radial float of the drive nut (no binding)
BUSH_OD, BUSH_L, BUSH_FLANGE_D, BUSH_FLANGE_T = 10.0, 6.0, 12.0, 1.0   # flanged sintered bronze 6x10x6
CHAN_W = 16.0

# --------------------------------------------------------------------------
# Body and plates
# --------------------------------------------------------------------------
BODY = 148.0
CORNER_R = 9.0
EDGE = 1.0                           # one fillet size for every visible edge
BODY_Z0 = GF_Z0
BODY_Z1 = 20.0
YP_T = 14.5
YP_Z0 = BODY_Z1 + GAP
YP_Z1 = YP_Z0 + YP_T
XP_Z0 = YP_Z1 + GAP
XP_Z1 = HELI_Z0                      # lens panel front = helicoid shoulder
XP_T = XP_Z1 - XP_Z0
PLATE = 148.0
XP_NOTCH = (47.0, 48.0)              # lens panel top corners removed for |x|>47, y>48 (knob clearance)

Y_RAIL_X = -58.0                     # vertical guide: photographer's right
Y_SCREW_X = 62.0                     # vertical screw: photographer's left, knob on top
X_RAIL_Y = -57.0                     # horizontal guide: bottom of the Y plate
X_SCREW_Y = 62.0                     # horizontal screw: top of the Y plate, knob on the right
X_ROD_END = 44.0                     # the horizontal rod stops here (keeps the top-left corner free)

Y_SCREW_Z = 12.6                     # nut and bushings live in the body channel (floor above the Graflok recess)
X_SCREW_Z = YP_Z1 - 5.0              # nut in the lens-panel turret, bushings in the Y plate
CHAN_FLOOR_Y = SEAT_Z + 1.5          # body screw channel floor
KNOB_D, KNOB_H = 22.0, 14.0
ORING_T = 1.5                        # drag O-ring under each knob (constant friction, no lock wheels)

# --------------------------------------------------------------------------
# Tripod plates and handles
# --------------------------------------------------------------------------
ARCA_W, ARCA_L, ARCA_T = 38.0, 60.0, 10.0
ARCA_POCKET = 1.8
PLINTH = 12.0                        # bottom plinth: the clamp jaws stay below the Y plate at full fall
ARCA_ZC = BODY_Z1 - ARCA_W / 2 - 1.0

HANDLE_BAR = 14.0
HANDLE_POST = 16.0
HANDLE_H = 44.0                      # protrusion (30 mm finger room)
TOP_HANDLE_X = (-72.0, 44.0)         # leaves the top-left corner to the rise knob
TOP_HANDLE_Z = (-6.0, BODY_Z1 - 8.0) # set back 8 mm from the sliding plates (no pinch)
SIDE_HANDLE_Y = (-62.0, 53.0)        # photographer's left; carries the portrait Arca plate
SIDE_HANDLE_Z = (ARCA_ZC - ARCA_W / 2 - 1.0, ARCA_ZC + ARCA_W / 2 + 1.0)

# --------------------------------------------------------------------------
# Focus ring
# --------------------------------------------------------------------------
FOCUS_OD, FOCUS_W = 124.0, 10.0
HELI_GRIP_Z = (1.5, 11.5)            # knurled ring position on the helicoid (from the shoulder)
COC = 0.06


def focus_angle(dist_m):
    """Ring angle (deg from infinity) to focus at dist_m (subject to film)."""
    D = dist_m * 1000.0
    f = F_LENS
    v = (D - math.sqrt(D * D - 4 * f * D)) / 2
    return FOCUS_DIR * (v - f) / HELI_TRAVEL * HELI_ROT


def dof_angle(n):
    """Half-angle of the depth-of-field marks for aperture n (image-side +/- N*c)."""
    return n * COC / HELI_TRAVEL * HELI_ROT


def focus_distance(heli_len):
    ext = heli_len - HELI_INF
    if ext <= 0:
        return math.inf
    v = F_LENS + ext
    return F_LENS * v / ext + v


# --------------------------------------------------------------------------
# Light cone (sizes the openings; conservative)
# --------------------------------------------------------------------------
PUPIL_Z, PUPIL_R = 55.0, 18.0
LIGHT_MARGIN = 1.5


def cone_half(z, sx, sy, rel_x=0.0, rel_y=0.0):
    t = z / PUPIL_Z
    hx = (1 - t) * FILM_W / 2 + t * PUPIL_R
    hy = (1 - t) * FILM_H / 2 + t * PUPIL_R
    return hx + abs(t * sx - rel_x) + LIGHT_MARGIN, hy + abs(t * sy - rel_y) + LIGHT_MARGIN


def opening_body(z):
    return cone_half(z, SHIFT_X, RISE)


def opening_yplate(z):
    hx, _ = cone_half(z, SHIFT_X, 0)
    hy = max(cone_half(z, 0, RISE, rel_y=RISE)[1], cone_half(z, 0, -FALL, rel_y=-FALL)[1], cone_half(z, 0, 0)[1])
    return hx, hy


if __name__ == "__main__":
    print(f"lens panel thickness {XP_T:.1f} mm, helicoid shoulder at z {HELI_Z0:.1f}")
    print(f"helicoid at infinity {HELI_INF:.1f} mm (margin {HELI_INF - HELI_MIN:.1f}; thinner adapter adds more)")
    print(f"closest focus {focus_distance(HELI_MAX) / 1000:.2f} m")
    for z in (SEAT_Z, BODY_Z1):
        print(f"body opening at z={z}: +/-{opening_body(z)[0]:.1f} x +/-{opening_body(z)[1]:.1f}")
    for z in (YP_Z0, YP_Z1):
        print(f"Y plate opening at z={z}: +/-{opening_yplate(z)[0]:.1f} x +/-{opening_yplate(z)[1]:.1f}")
