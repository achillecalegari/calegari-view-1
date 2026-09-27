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
RISE, FALL = 25.0, 25.0              # vertical travel, symmetric
SHIFT_X = 25.0                       # lateral travel, both ways
OVERLAP_MOVE = 8.0                   # light seal overlap in the direction of motion
OVERLAP_FIXED = 4.0                  # ... and across it
GAP = 0.8                            # plate-to-plate gap: hard pads, velvet compressed in it

# Dovetail ways: printed rails screwed along the edges, 60 degree flanks. One rail of each pair is
# fixed, the other carries a gib strip set by three nylon-tip grub screws from the outside.
# Profile coordinates: u = outward from the axis of travel, w = height above the face the rail sits on.
WAY_FL = GAP                         # rail flange: the moving plate bears on it (sets the 0.8 mm gap)
WAY_UI = 64.0                        # rail inner face above the lip
WAY_UO = 74.0                        # rail outer face, flush with the body edges (BODY / 2)
WAY_FL_IN = WAY_UI - 1.0             # flange inner edge (bearing under the lip)
WAY_ANG = 60.0
Y_LIP, X_LIP = 2.6, 4.0              # lip heights of the Y plate and of the lens panel
Y_WAY_H = WAY_FL + Y_LIP + 1.8       # Y rails stay under the Y plate front (the X knob passes over them)
GIB_T = {"y": 2.3, "x": 1.5}      # gib strip thickness per stage (same outer wall for the grubs)
GIB_BACK = 0.4                       # room behind the gib: an oversize print still goes together
FLANK_C = 0.05                       # clearance on the flanks, as modelled (the gib takes it up)
EDGE_C = 0.3
WAY_SCREW_U = 70.5
Y_WAY_SCREWS = {1: (-58.0, -20.0, 20.0, 58.0), -1: (-58.0, -43.0, 43.0)}   # from the body rear (clear of the dark slide and the vial)
X_WAY_SCREWS = (-54.0, -18.0, 18.0, 36.0)
GIB_GRUBS = {"y": (-50.0, 0.0, 50.0), "x": (-40.0, 0.0, 50.0)}   # cone-point grubs into dimples in the gib
X_WAY_SCREW_U = 71.0                 # M2.5 screws from the Y plate rear into inserts in the X rails

# M6 drive screws
ROD_D = 6.0
NUT_AF, NUT_T = 10.0, 5.0
NUT_FLOAT = 0.5                                   # radial float of the drive nut (no binding)
BUSH_OD, BUSH_L = 8.0, 6.0          # sintered bronze bushing 6 x 8 x 6 (fits inside the Y plate without breaking its front)
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
XP_NOTCH = (47.0, 41.0)              # lens panel top corners removed for |x|>47, y>41 (shift knob clearance)

Y_SCREW_X = 54.0                     # vertical screw: photographer's left, knob on top
X_SCREW_Y = 54.0                     # horizontal screw: top of the Y plate, knob on the right
X_ROD_END = 44.0                     # the horizontal rod stops here (keeps the top-left corner free)

Y_SCREW_Z = 12.6                     # nut and bushings live in the body channel (floor above the Graflok recess)
X_SCREW_Z = YP_Z1 - 5.0              # nut in the lens-panel turret, bushings in the Y plate
CHAN_FLOOR_Y = SEAT_Z + 1.5          # body screw channel floor
KNOB_D, KNOB_H = 24.0, 15.0
KNOB_GAP = 0.4                       # the knob rides on its O-ring, 0.4 mm off the face
ORING_T = 1.5                        # drag O-ring under each knob (constant friction, no lock wheels)
ORING_SEAT = 1.1                     # seat depth: the 1.5 mm O-ring stands 0.4 proud and is squeezed by the knob
CAP_NUT_H = 12.0                     # DIN 1587 M6 domed cap nut at the far end of each rod (Loctite on the bench)
Y_CAP_ROD_END = -62.5 - 9.0          # the rise rod ends 9 mm inside its cap nut
X_CAP_ROD_END = 9.0                  # the shift rod ends 9 mm inside its cap nut (outside the Y plate's left edge)

# --------------------------------------------------------------------------
# Tripod plates and handles
# --------------------------------------------------------------------------
ARCA_W, ARCA_L, ARCA_T = 38.0, 60.0, 10.0
ARCA_POCKET = 1.8
PLINTH = 25.0                        # bottom of the L bracket: 4 mm from a 65 mm clamp's jaws to the Y plate at full fall
ARCA_ZC = BODY_Z1 - ARCA_W / 2 - 1.5

L_Z0 = ARCA_ZC - ARCA_W / 2 - 3.0   # the L bracket (bottom plinth + side leg) reaches behind the body
SIDE_T = 25.0                        # side leg of the L bracket (photographer's left), portrait Arca plate
SIDE_ARCA_YC = 0.0

HANDLE_BAR = 14.0
HANDLE_POST = 14.0
HANDLE_H = 44.0                      # protrusion (30 mm finger room)
HANDLE_FLARE = 5.0                   # concave fillet where the posts meet the body
TOP_HANDLE_X = (-60.0, 28.0)         # over the flat of the body top; 9 mm of finger room to the rise knob
TOP_HANDLE_Z = (BODY_Z0, BODY_Z1)    # flush with the body rear and front: deep enough for two accessory shoes
SHOES_X = (-35.5, 2.5)               # ISO 518 accessory shoes on top of the bar, open to the rear
LEVEL_TOP_X = -16.5                  # 15 mm bull's-eye level between the shoes (pitch and roll in landscape)
LEVEL_D, LEVEL_H = 15.4, 8.2         # pocket for a 15 x 8 mm bull's-eye vial

# --------------------------------------------------------------------------
# Focus ring
# --------------------------------------------------------------------------
FOCUS_OD, FOCUS_W = 116.0, 10.0
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
