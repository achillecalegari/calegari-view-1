"""Figures for docs/assembly.md and docs/calibration.md.

python figures.py [name ...]   writes out/figs/<name>/manifest.json and points.json
render/figures.sh renders them (render/white.py with PTS) and annotates them (render/annotate.py).

An assembly figure shows what is already built in place and only the parts of that sub-step pulled
out along the way they go in, with a dashed guide from each part to its hole. Letters match the
tables in the guide. Calibration figures use words instead of letters.
"""
import json, math, pathlib, sys
from build123d import *
from params import *
import parts as P
import hardware as hw
from hardware import orient
from assembly import assemble

OUT = pathlib.Path(__file__).resolve().parent.parent / "out" / "figs"
H = BODY / 2

# every component belongs to one group; the groups follow the order of assembly
G = {
    "body": ["body", "inlay_body"], "ins_gf": ["insert_gf"], "ins_yway": ["insert_yway"],
    "plunger_y": ["plunger_y"], "bush_y": ["bush_y"], "ins_top": ["insert_top"], "ins_arca": ["insert_arca"],
    "gf_module": ["graflok_module"], "ins_blade": ["insert_blade"], "screw_gf": ["screw_gf"],
    "blade": ["graflok_blade", "screw_blade"], "wheel": ["graflok_wheel", "screw_wheel"],
    "arca": ["arca_"], "handle": ["top_handle", "screw_top", "inlay_handle"], "vial_top": ["vial_top"],
    "vial_side": ["vial_side"], "ways_y": ["way_y", "screw_yway"], "velvet_body": ["velvet_body"],
    "yplate": ["y_plate", "inlay_yplate"], "bush_x": ["bush_x"], "plunger_x": ["plunger_x"],
    "velvet_y": ["velvet_yplate"], "xplate": ["x_plate", "inlay_xplate"], "flange": ["flange", "screw_flange"],
    "ins_stop": ["insert_stop"], "x_turret": ["x_turret"], "ways_x": ["way_x", "insert_xway", "inlay_xway"],
    "screw_xway": ["screw_xway"], "gib_x": ["gib_x", "grub_gib_x"],
    "rod_x": ["rod_x", "washer_x_thrust", "nut_x_thrust", "nut_x_drive"], "knob_x": ["oring_x", "knob_x", "inlay_knob_x"],
    "y_turret": ["y_turret", "nut_y_drive", "insert_yturret"], "rod_y": ["rod_y", "nut_y_cap"],
    "screw_yturret": ["screw_yturret"], "discs": ["velvet_discs"], "gib_y": ["gib_y", "grub_gib_y"],
    "knob_y": ["oring_y", "knob_y", "inlay_knob_y"], "stop_pin": ["stop_pin"], "helicoid": ["helicoid"],
    "focus": ["focus_ring", "inlay_focus"], "adapter": ["adapter_ring", "insert_adapter"],
    "holder": ["board_holder"], "felts": ["felt_"], "latch": ["holder_latch", "spring_latch", "screw_latch"],
    "screw_adapter": ["screw_adapter"], "board": ["lensboard", "lens"], "back": ["rb_"],
}


def g(*keys):
    return [p for k in keys for p in G[k]]


BODY_DONE = g("body", "ins_gf", "ins_yway", "plunger_y", "bush_y", "ins_top", "ins_arca")
C2 = BODY_DONE + g("gf_module", "ins_blade", "screw_gf", "blade", "wheel")
C3 = C2 + g("arca", "handle", "vial_top", "vial_side")
C4 = C3 + g("ways_y", "velvet_body")
FRONT = g("yplate", "bush_x", "plunger_x", "velvet_y", "xplate", "flange", "ins_stop", "x_turret", "ways_x",
          "screw_xway", "gib_x", "rod_x", "knob_x")
C6 = C4 + g("y_turret", "rod_y") + FRONT + g("screw_yturret", "discs", "gib_y", "knob_y")
C7 = C6 + g("stop_pin", "helicoid", "focus")
C8 = C7 + g("adapter", "holder", "felts", "latch", "screw_adapter", "board")

Z_RING = HELI_Z0 + HELI_GRIP_Z[0]
R_RING = FOCUS_OD / 2


def ring_point(ang, r, z):
    a = math.radians(ang)
    return (-r * math.sin(a), r * math.cos(a), z)


def mv(pts, d):
    return [(x + d[0], y + d[1], z + d[2]) for x, y, z in pts]


# Blender view directions: +x photographer's left, +y behind the camera, +z up
V_REAR = (0.35, 1.0, 0.3)
V_FRONT = (-0.3, -1.0, 0.35)
V_34 = (-0.62, -1.0, 0.3)
V_34L = (0.62, -1.0, 0.3)
V_OB_R = (0.95, 1.0, 0.45)      # oblique: parts pulled out along the optical axis stay readable
V_OB_F = (-0.95, -1.0, 0.45)
V_OB_FL = (0.95, -1.0, 0.45)

FIGS = []


def fig(name, title, view, show, new=(), labels=(), lines=(), state=None, extra=(), doc="asm", **look):
    FIGS.append(dict(name=name, title=title, view=view, show=list(show), new=list(new), labels=list(labels),
                     lines=list(lines), state=state or {}, extra=list(extra), doc=doc, look=look))


# ------------------------------------------------------------------ assembly: 1 body
fig("1a_seat_inserts", "1a  Inserts in the Graflok seat", V_REAR, g("body"),
    new=[(g("ins_gf"), (0, 0, -30))],
    labels=[("A", "insert_gf"), ("B", [(sum(TRAP_X) / 2, 0.0, SEAT_Z), (P.LOOP_X, 20.0, SEAT_Z)]),
            ("C", [(-60.0, 20.0, 2.0)]), ("D", [(P.Y_DETENT[0], P.Y_DETENT[1], SEAT_Z)])])
fig("1b_front_inserts", "1b  Inserts along the front edges", V_FRONT, g("body", "ins_gf"),
    new=[(g("ins_yway"), (0, 0, 30))], labels=[("E", "insert_yway")])
fig("1c_plunger_bushings", "1c  Rise plunger and bushings", V_FRONT, g("body", "ins_gf", "ins_yway"),
    new=[(["plunger_y"], (0, 0, 35)), (["bush_y_top"], (0, -14, 30)), (["bush_y_bot"], (0, 14, 30))],
    labels=[("F", "plunger_y"), ("G", "bush_y")])
fig("1d_top_inserts", "1d  Handle inserts on top", (-1.0, -0.45, 0.85), BODY_DONE[:0] + g("body", "ins_gf", "ins_yway", "plunger_y", "bush_y"),
    new=[(g("ins_top"), (0, 30, 0))],
    labels=[("H", "insert_top"), ("J", [tuple(P.body_vial().bounding_box().center())]), ("K", [(Y_SCREW_X, H, Y_SCREW_Z)])],
    dist=5.0)
fig("1e_arca_inserts", "1e  Tripod inserts underneath", (0.9, -0.55, -0.75),
    g("body", "ins_gf", "ins_yway", "plunger_y", "bush_y", "ins_top"),
    new=[(["insert_arca_b"], (0, -30, 0)), (["insert_arca_s"], ("out", 0, 30))],
    labels=[("L", "insert_arca_b"), ("M", "insert_arca_s"), ("N", [(Y_SCREW_X, -H - PLINTH, Y_SCREW_Z)])], dist=5.0)

# ------------------------------------------------------------------ 2 Graflok
fig("2a_module_inserts", "2a  Inserts in the Graflok module", (0.2, 1.0, 0.3), g("gf_module"),
    new=[(g("ins_blade"), (0, 0, -25))], labels=[("A", "insert_blade")])
fig("2b_module_on", "2b  Module into the body", V_OB_R, BODY_DONE,
    new=[(g("gf_module", "ins_blade"), (0, 0, -45), ["graflok_module"]), (g("screw_gf"), (0, 0, -85))],
    labels=[("B", "screw_gf"), ("C", [(-60.0, 20.0, 2.0)])])
fig("2c_blade_wheel", "2c  Blade and wheel", V_OB_R, BODY_DONE + g("gf_module", "ins_blade", "screw_gf"),
    new=[(["graflok_blade"], (0, 0, -30)), (["screw_blade"], (0, 0, -60)), (g("wheel"), (0, 0, -45), ["graflok_wheel"])],
    labels=[("D", "graflok_blade"), ("E", "screw_blade"), ("F", "graflok_wheel"), ("G", [(0.0, -63.0, -2.0)])])

# ------------------------------------------------------------------ 3 tripod plates, handle, levels
fig("3a_arca", "3a  Arca plates", (0.9, -0.55, -0.75), C2,
    new=[(["arca_bottom"], (0, -35, 0)), (["arca_side"], ("out", 0, 35))],
    labels=[("A", ["arca_bottom"]), ("B", ["arca_side"])], dist=5.0)
fig("3b_handle", "3b  Top handle", (-0.45, -1.0, 0.8), C2 + g("arca"),
    new=[(["top_handle", "inlay_handle"], (0, 40, 0), ["top_handle"]), (["screw_top"], (0, 95, 0))],
    labels=[("C", "top_handle"), ("D", "screw_top"),
            ("E", mv([(x, H + HANDLE_H, TOP_HANDLE_Z[0] + 8.0) for x in SHOES_X], (0, 40, 0)))], dist=4.6)
fig("3c_levels", "3c  The two levels", (-1.0, -0.45, 0.85), C2 + g("arca", "handle"),
    new=[(["vial_top"], (0, 30, 0)), (["vial_side"], ("out", 0, 30))],
    labels=[("F", "vial_top"), ("J", "vial_side")], dist=5.0)

# ------------------------------------------------------------------ 4 vertical ways, body velvet
fig("4a_ways_y", "4a  Vertical rails", V_OB_F, C3,
    new=[(["way_y_fixed"], (0, 0, 35)), (["way_y_gib"], (0, 0, 35)), (["screw_yway"], (0, 0, 75))],
    labels=[("P", "way_y_fixed"), ("Q", "way_y_gib"), ("T", "screw_yway")], dist=4.6)
fig("4b_velvet_v1", "4b  Velvet V1 on the body front", V_OB_F, C3 + g("ways_y"),
    new=[(g("velvet_body"), (0, 0, 30))], labels=[("V1", "velvet_body"), ("F", "plunger_y")])

# ------------------------------------------------------------------ 5 front standard on the bench
fig("5a_yplate", "5a  Y plate: bushings and shift plunger", V_FRONT, g("yplate"),
    new=[(["bush_x_left"], (-14, 0, 30)), (["bush_x_right"], (14, 0, 30)), (["plunger_x"], (0, 0, 35))],
    labels=[("A", "bush_x"), ("B", "plunger_x"), ("H", [(-H, X_SCREW_Y, X_SCREW_Z)])])
fig("5b_yplate_rear", "5b  Y plate from behind", V_REAR, g("yplate", "bush_x", "plunger_x"),
    labels=[("C", [(P.X_DETENT[0], P.X_DETENT[1], YP_Z0)]), ("D", [(P.Y_DETENT[0], P.Y_DETENT[1], YP_Z0)])])
fig("5c_velvet_v2", "5c  Velvet V2 on the Y plate", V_OB_F, g("yplate", "bush_x", "plunger_x"),
    new=[(g("velvet_y"), (0, 0, 25))],
    labels=[("V2", "velvet_yplate"), ("E", [(x, y, YP_Z1) for x, y in P.Y_TURRET_SCREWS])])
fig("5d_flange", "5d  Lens panel: flange and stop insert", V_OB_F, g("xplate"),
    new=[(["flange"], (0, 0, 35)), (["insert_stop"], (0, 0, 22))],
    labels=[("F", "flange"), ("K", "insert_stop")])
fig("5e_panel_rear", "5e  Lens panel from behind: screws and turret", V_OB_R, g("xplate", "ins_stop") + ["flange"],
    new=[(["screw_flange"], (0, 0, -30)), (g("x_turret"), (0, 0, -35))],
    labels=[("G", "screw_flange"), ("J", "x_turret"), ("L", [(P.X_DETENT[0], P.X_DETENT[1], XP_Z0)])])
fig("5f_rail_inserts", "5f  Inserts in the horizontal rails", V_OB_R, ["way_x", "inlay_xway"],
    new=[(["insert_xway"], (0, 0, -22))], labels=[("M", "insert_xway"), ("P", "way_x_fixed"), ("Q", "way_x_gib")])
fig("5g_rod", "5g  Shift rod, thrust nut and drive nut", (-0.25, -1.0, 0.75),
    g("yplate", "bush_x", "plunger_x", "velvet_y"),
    new=[(["rod_x"], (-60, 0, 0)), (["washer_x_thrust"], (18, 0, 26)), (["nut_x_thrust"], (18, 0, 40)),
         (["nut_x_drive"], (0, 0, 32))],
    labels=[("T", "rod_x"), ("U", "washer_x_thrust"), ("W", "nut_x_thrust"), ("X", "nut_x_drive")],
    lines=[dict(points=[(-H - 55, X_SCREW_Y + 12, X_SCREW_Z), (-H - 15, X_SCREW_Y + 12, X_SCREW_Z)], style="arrow")])
fig("5h_stack", "5h  Lens panel onto the Y plate", V_OB_F, g("yplate", "bush_x", "plunger_x", "velvet_y", "rod_x"),
    new=[(g("xplate", "flange", "ins_stop", "x_turret"), (0, 0, 45), ["x_plate"])],
    labels=[("J", "x_turret"), ("X", "nut_x_drive")])
fig("5i_rails", "5i  Horizontal rails, screwed from behind", V_OB_R,
    g("yplate", "bush_x", "plunger_x", "velvet_y", "rod_x", "xplate", "flange", "ins_stop", "x_turret"),
    new=[(["way_x_fixed", "insert_xway_-1", "inlay_xway"], (0, -40, 0), ["way_x_fixed"]),
         (["way_x_gib", "insert_xway_1"], (0, 40, 0), ["way_x_gib"]), (["screw_xway"], (0, 0, -40))],
    labels=[("P", "way_x_fixed"), ("Q", "way_x_gib"), ("N", "screw_xway")], dist=5.2)
fig("5j_gib_x", "5j  Gib strip and grub screws", (-0.3, -1.0, 0.7),
    g("yplate", "bush_x", "plunger_x", "velvet_y", "rod_x", "xplate", "flange", "ins_stop", "x_turret", "ways_x", "screw_xway"),
    new=[(["gib_x"], (60, 0, 0)), (["grub_gib_x"], (0, 25, 0))],
    labels=[("R", "gib_x"), ("S", "grub_gib_x"), ("0", [(0.0, -H + 1.5, YP_Z1 + 2.0)])])
fig("5k_knob_x", "5k  Shift knob", V_34, FRONT[:0] + g("yplate", "bush_x", "plunger_x", "velvet_y", "rod_x", "xplate",
                                                         "flange", "ins_stop", "x_turret", "ways_x", "screw_xway", "gib_x"),
    new=[(["oring_x"], (-20, 0, 0)), (["knob_x", "inlay_knob_x"], (-42, 0, 0), ["knob_x"])],
    labels=[("Y", "oring_x"), ("Z", "knob_x")])

# ------------------------------------------------------------------ 6 front standard into the body
fig("6a_y_turret", "6a  Rise nut turret", (0.6, -0.8, 0.6), ["y_turret"],
    new=[(["nut_y_drive"], (25, 0, 0)), (["insert_yturret"], (0, 0, 18))],
    labels=[("A", "nut_y_drive"), ("B", "insert_yturret")], dist=5.0)
fig("6b_rise_rod", "6b  Turret and rise rod into the body", V_OB_FL, C4,
    new=[(g("y_turret"), (0, 0, 40), ["y_turret"]), (g("rod_y"), (0, -100, 0), ["rod_y"])],
    labels=[("C", "y_turret"), ("D", "rod_y"), ("N", "nut_y_cap")], dist=5.4)
fig("6c_slide_in", "6c  The front standard slides in from the top", (-0.62, -1.0, 0.35), C4 + g("y_turret", "rod_y"),
    new=[(FRONT, (0, 115, 0), [])],
    labels=[("V1", [(-20.0, -58.0, BODY_Z1 + GAP)])],
    lines=[dict(points=[(-H - 30, 150, 60), (-H - 30, 60, 60)], style="arrow")], dist=5.2)
fig("6d_turret_screws", "6d  Turret screws and velvet discs", V_OB_F, C4 + g("y_turret", "rod_y") + FRONT,
    state=dict(sx=-25.0),
    new=[(g("screw_yturret"), (0, 0, 30)), (g("discs"), (0, 0, 55))],
    labels=[("E", "screw_yturret"), ("V2d", "velvet_discs")])
fig("6e_gib_y", "6e  Gib strip and grub screws", (-0.75, -1.0, 0.4), C4 + g("y_turret", "rod_y") + FRONT + g("screw_yturret", "discs"),
    new=[(["gib_y"], (0, 75, 0)), (["grub_gib_y"], (-25, 0, 0))],
    labels=[("R", "gib_y"), ("S", "grub_gib_y")], dist=4.6)
fig("6f_knob_y", "6f  Rise knob", V_34L, C6[:0] + C4 + g("y_turret", "rod_y") + FRONT + g("screw_yturret", "discs", "gib_y"),
    new=[(["oring_y"], (0, 18, 0)), (["knob_y", "inlay_knob_y"], (0, 42, 0), ["knob_y"])],
    labels=[("Y", "oring_y"), ("Z", "knob_y")], dist=4.6)

# ------------------------------------------------------------------ 7 helicoid, focus ring
fig("7a_helicoid", "7a  Stop pin and helicoid", V_OB_F, C6,
    new=[(["stop_pin"], (0, 0, 25)), (["helicoid"], (0, 0, 60))],
    labels=[("F", "stop_pin"), ("H", "helicoid")], dist=4.4)
fig("7b_focus_ring", "7b  Focus ring", V_OB_F, C6 + g("stop_pin", "helicoid"),
    new=[(g("focus"), (0, 0, 45), ["focus_ring"])],
    labels=[("A", mv([ring_point(a, R_RING, Z_RING + FOCUS_W / 2) for a in (45, 135, 225, 315)], (0, 0, 45))),
            ("C", mv([ring_point(-P.LEVER_ANG, R_RING + 6, Z_RING + FOCUS_W / 2)], (0, 0, 45)))], dist=4.4)
fig("7c_ring_back", "7c  Focus ring from behind: the hidden stop", (0.45, 1.0, 0.55), ["focus_ring", "stop_pin"],
    labels=[("B", [ring_point(-P.STOP_TAB_ANG, P.STOP_R, Z_RING)]), ("F", "stop_pin"),
            ("D", [ring_point(0.0, R_RING, Z_RING + FOCUS_W - 2.5)])])

# ------------------------------------------------------------------ 8 adapter, holder, board
fig("8a_adapter", "8a  Inserts in the adapter ring", V_OB_F, ["adapter_ring"],
    new=[(["insert_adapter"], (0, 0, 18))], labels=[("A", "insert_adapter")], dist=4.6)
fig("8b_holder_rear", "8b  Felt V3 behind the board holder", V_OB_R, ["board_holder"],
    new=[(["felt_adapter"], (0, 0, -22))], labels=[("V3", "felt_adapter")])
fig("8c_holder_front", "8c  Felt V4 and the spring", V_OB_F, ["board_holder", "felt_adapter"],
    new=[(["felt_board"], (0, 0, 22)), (["spring_latch"], (0, -22, 14))],
    labels=[("V4", "felt_board"), ("B", "spring_latch")])
fig("8d_latch", "8d  Latch, held by two screws from behind", (0.35, -1.0, 0.6), ["board_holder", "felt_", "spring_latch"],
    new=[(["holder_latch"], (0, -30, 0)), (["screw_latch"], (0, 0, -30))],
    labels=[("C", "holder_latch"), ("D", "screw_latch")],
    lines=[dict(points=[(26, 5, BOARD_Z1 + 3), (26, 40, BOARD_Z1 + 3)], style="arrow")])
fig("8e_holder_on", "8e  Adapter and board holder onto the helicoid", V_OB_F, C7,
    new=[(g("adapter"), (0, 0, 35), ["adapter_ring"]), (g("holder", "felts", "latch"), (0, 0, 75), ["board_holder"]),
         (g("screw_adapter"), (0, 0, 105))],
    labels=[("G", "adapter_ring"), ("H", "board_holder"), ("E", "screw_adapter")], dist=4.6)
fig("8f_board", "8f  Lens board", V_OB_F, C7 + g("adapter", "holder", "felts", "latch", "screw_adapter"),
    state=dict(latch_locked=False),
    new=[(g("board"), (0, -12, 55), ["lensboard"])],
    labels=[("J", [(sx_ * 30, -BOARD_H / 2 + 1.0, BOARD_Z1 + 1.8) for sx_ in (-1, 1)]), ("C", "holder_latch")], dist=4.6)

# ------------------------------------------------------------------ 9 back
fig("9a_back", "9a  Film back", V_OB_R, C8, state=dict(blade_locked=False),
    new=[(g("back"), (0, 0, -70), ["rb_back"])],
    labels=[("G", [(0.0, -63.0, -2.0)]), ("D", "graflok_blade"), ("F", "graflok_wheel")], dist=4.4)


# ================================================================== calibration
def ext_glass():
    return Pos(0, 0, SEAT_Z + 1.5) * Box(190, 170, 3)


CAL = dict(doc="cal", aspect=0.66)

fig("c_overview_front", "The camera from the front", (-0.62, -1.0, 0.25), C8 + g("back"),
    labels=[("Lens and shutter", "lens_glass"), ("Lens board", [(BOARD_W / 2 - 6, -BOARD_H / 2 + 6, BOARD_Z1)]),
            ("Board latch", "holder_latch"), ("Focus ring", [ring_point(-P.LEVER_ANG, R_RING + 6, Z_RING + FOCUS_W / 2)]),
            ("Lens panel (shift)", [(-H + 6, -40.0, XP_Z1)]), ("Y plate (rise)", [(-H + 2, -H + 6, YP_Z1)]),
            ("Rise knob", "knob_y"), ("Shift knob", "knob_x"), ("Top handle", [(-50.0, H + HANDLE_H - 3, BODY_Z1)]),
            ("Arca plate", "arca_bottom")], dist=4.2, **CAL)
fig("c_overview_rear", "The camera from behind", (-0.62, 1.0, 0.25), C8 + g("back"),
    labels=[("Film back (RB67)", "rb_back"), ("Graflok blade", "graflok_blade"), ("Clamp wheel", "graflok_wheel"),
            ("Dark slide exit", [(-64.0, 0.0, GF_Z0 - 6)]), ("Level (landscape)", "vial_top"),
            ("Level (portrait)", "vial_side")], dist=4.2, **CAL)
fig("c_back_fit", "Test: the back on the test module", (0.7, 1.0, 0.75), g("gf_module", "ins_blade", "blade", "wheel", "back"),
    extra=[("glass", ext_glass(), "grey")],
    labels=[(">Glass sheet", [(80.0, -70.0, SEAT_Z + 3)]), (">Bottom rail", [(0.0, -63.0, -2.0)]),
            (">Blade tongues", "graflok_blade"), (">Wheel", "graflok_wheel"),
            ("<Dark slide exit", [(-64.0, 0.0, GF_Z0 - 6)])], dist=4.4, **CAL)


def coupons():
    yp = P.y_plate_part()
    cut = lambda sh: sh & P.box_at(-80, 80, -20, 20, -50, 120)
    lip_y, hy, _ = P.way_stage("y")
    uw = P.gib_wall("y")
    grub = Pos(-(uw - GIB_BACK + 6.0), 0.0, BODY_Z1 + WAY_FL + lip_y / 2) * orient(hw.grub(3, 6), "-x")
    m = Pos(95, 0, 0)                  # the gib pair next to the fixed pair
    return [("rail_fixed", cut(P.way_rail("y", 1, False)), "body_black"),
            ("lip_left", Pos(0, -16, 0) * (yp & P.box_at(50, 75, -20, 20, YP_Z0 - 0.1, YP_Z1 + 1)), "grey"),
            ("rail_gib", m * cut(P.way_rail("y", -1, True)), "body_black"),
            ("gib", m * cut(P.gib_strip("y", -1)), "red"),
            ("lip_right", m * Pos(0, -16, 0) * (yp & P.box_at(-75, -50, -20, 20, YP_Z0 - 0.1, YP_Z1 + 1)), "grey"),
            ("grub", m * grub, "black_steel")]


def _top(sh):
    b = sh.bounding_box()
    return ((b.min.X + b.max.X) / 2, b.max.Y, (b.min.Z + b.max.Z) / 2)


TOP = {n: _top(sh) for n, sh, m in coupons()}
fig("c_dovetails", "Test: the dovetail coupons, seen from the top end", (0.15, -0.4, 1.0), [], extra=coupons(),
    labels=[(">Fixed rail", [TOP["rail_fixed"]]), (">Plate lip", "lip_left"), ("<Gib rail", [TOP["rail_gib"]]),
            ("<Gib strip", [TOP["gib"]]), ("<Plate lip", "lip_right")], dist=4.2, **CAL)


def metal():
    gauge = Pos(0, 130, 0) * P.shrink_gauge()
    heli = Pos(0, 0, -HELI_Z0) * P.helicoid_part(HELI_INF)
    ad = P.adapter_part(with_thread=True)
    coupon = Pos(0, 0, 45 - (ADAPTER_Z0 - 10)) * (ad & P.cyl_z(45, ADAPTER_Z0 - 10, ADAPTER_Z0 + 3))
    xp = P.x_plate_part() & P.cyl_z(46, XP_Z0 - 1, XP_Z1 + 1)
    fl_coupon = Pos(0, -115, -XP_Z0) * xp
    fl = Pos(0, -115, -XP_Z0 + 22) * P.flange_part()
    return [("gauge", gauge, "body_black"), ("helicoid", heli, "alu_black"), ("m65_coupon", coupon, "red"),
            ("flange_coupon", fl_coupon, "body_black"), ("flange", fl, "alu_black")]


fig("c_metal_fit", "Test: shrinkage, thread and flange", (0.0, -0.45, 1.0), [], extra=metal(),
    labels=[("<Gauge", [(-47.0, 130.0, 3.0)]), (">M65 coupon", [(36.0, 0.0, 52.0)]), ("<Helicoid", [(-38.0, 0.0, 10.0)]),
            (">Flange", [(38.0, -115.0, 26.0)]), ("<Flange coupon", [(-44.0, -115.0, 4.0)])],
    lines=[dict(points=[(-50.0, 190.0, 3.0), (50.0, 190.0, 3.0)], style="dim", text="100.0", offset=(0, -34))],
    dist=3.6, **CAL)


def heli_arc(r, z, a0, a1, n=40):
    return [ring_point(a0 + (a1 - a0) * i / n, r, z) for i in range(n + 1)]


fig("c_helicoid_turn", "Measure how far the helicoid turns", (0.0, -1.0, 0.45), [],
    extra=[("helicoid", Pos(0, 0, -HELI_Z0) * P.helicoid_part(HELI_MAX), "alu_black")],
    labels=[(">Tape on the fixed part", [ring_point(0, HELI_OD / 2 - 4, HELI_MAX - 3)]),
            (">Mark on the grip", [ring_point(0, HELI_OD / 2, 6.5)])],
    lines=[dict(points=heli_arc(HELI_OD / 2 + 12, 6.5, 0, -250), style="arrow", text="count the degrees", offset=(0, 60))],
    dist=4.2, **CAL)

fig("c_light_test", "Light test: torch in front, eye behind", (1.0, -0.1, 0.12),
    [p for p in C8 if not p.startswith("lens")], section=True,
    labels=[(">Velvet", "velvet_body"), (">Velvet ", "velvet_yplate")],
    lines=[dict(points=[(0.0, 22.0, 150.0), (0.0, 22.0, 85.0)], style="arrow", text="torch", offset=(0, -40)),
           dict(points=[(0.0, 22.0, -70.0), (0.0, 22.0, -20.0)], style="arrow", text="eye", offset=(0, -40))],
    dist=4.6, **CAL)

fig("c_infinity_front", "Focus ring and lens panel marks", (-0.15, -1.0, 0.75),
    g("xplate", "flange", "ins_stop", "stop_pin", "helicoid", "focus"),
    labels=[("<Red index", [(0.0, P.INDEX_R, XP_Z1)]),
            ("<Depth of field", [ring_point(dof_angle(22), P.INDEX_R, XP_Z1)]),
            ("<Focus tab", [ring_point(-P.LEVER_ANG, R_RING + 6, Z_RING + FOCUS_W / 2)]),
            (">Infinity dot", [ring_point(0.0, R_RING, Z_RING + FOCUS_W - 2.5)]),
            (">Distance dots", [ring_point(-40.0, R_RING, Z_RING + FOCUS_W - 2.5)]),
            (">Grub screws", [ring_point(a, R_RING, Z_RING + FOCUS_W / 2) for a in (315,)])], dist=3.8, **CAL)
fig("c_infinity_stop", "The hidden stop, seen from behind", (0.45, 1.0, 0.55), ["focus_ring", "stop_pin"],
    labels=[(">Stop pin", "stop_pin"), (">Block", [ring_point(-P.STOP_TAB_ANG, P.STOP_R, Z_RING)]),
            ("<Groove", [ring_point(-P.STOP_TAB_ANG + 60, P.STOP_R, Z_RING)])], dist=3.8, **CAL)


def shim_parts():
    lm, lg = P.lens_part()
    sh = Pos(0, 0, BOARD_Z1) * P.copal0_shim(0.8)
    return [("lensboard", P.lensboard_part(), "alu_black"), ("shim", Pos(0, 0, 18) * sh, "red"),
            ("lens", Pos(0, 0, 40) * lm, "lens_black"), ("lens_glass", Pos(0, 0, 40) * lg, "glass")]


fig("c_shim", "A shim under the shutter", V_OB_F, [], extra=shim_parts(),
    labels=[(">Shutter", [(0.0, 31.5, BOARD_Z1 + 40 + 9)]), ("<Shim", [(-26.0, 0.0, BOARD_Z1 + 18.4)]),
            ("<Lens board", [(-BOARD_W / 2 + 6, BOARD_H / 2 - 6, BOARD_Z1)]),
            (">Retaining ring", [(0.0, -21.5, BOARD_Z0 - 1.5 + 40)])], dist=3.8, **CAL)


def holder_corner():
    b = P.holder_part().bounding_box()
    return (b.max.X - 4, b.max.Y - 4, BOARD_Z1)


HC = holder_corner()
fig("c_shim_measure", "Measure h at the top left corner", (0.95, -0.55, 0.35), C8,
    lines=[dict(points=[(HC[0], HC[1] + 10, XP_Z1), (HC[0], HC[1] + 10, BOARD_Z1)], style="dim", text="h", offset=(0, -34))],
    labels=[(">Lens panel front", [(HC[0], HC[1], XP_Z1)]), ("<Holder front", [HC])], dist=4.2, **CAL)
fig("c_parallel", "Lens board parallel to the film", (-1.0, 0.0, 0.08), C8,
    lines=[dict(points=[(-H - 10, BOARD_H / 2 - 4, GF_Z0), (-H - 10, BOARD_H / 2 - 4, BOARD_Z1)], style="dim", text="1", offset=(0, -34)),
           dict(points=[(-H - 10, -BOARD_H / 2 + 4, GF_Z0), (-H - 10, -BOARD_H / 2 + 4, BOARD_Z1)], style="dim", text="2", offset=(0, 34))],
    labels=[("<Module back face", [(-H, -30.0, GF_Z0)]), (">Board front face", [(-BOARD_W / 2, -30.0, BOARD_Z1)])],
    dist=4.2, **CAL)


# ------------------------------------------------------------------ build
_cache = {}


def items_for(state):
    key = tuple(sorted(state.items()))
    if key not in _cache:
        _cache[key] = assemble(**state)
    return _cache[key]


def matches(name, prefixes):
    return any(name.startswith(p) for p in prefixes)


def section_cut(shown):
    half = Pos(-500, 0, 0) * Box(1000, 1000, 1000)
    slab = Pos(0.05, 0, 0) * Box(0.2, 1000, 1000)
    out = []
    for n, s, m in shown:
        try:
            h = s & half
            if h.volume > 0.01:
                out.append((n, h, m))
                if m not in ("glass", "vial") and not n.startswith(("screw_", "insert_")):
                    c = s & slab
                    if c.volume > 0.01:
                        out.append((n + "__cap", c, "cap"))
        except Exception:
            pass
    return out


def build(f):
    items = items_for(f["state"])
    shown_names = f["show"] + [p for nw in f["new"] for p in nw[0]]
    shown = [(i.name, i.shape, i.mat) for i in items if shown_names and matches(i.name, shown_names)]
    shown += f["extra"]
    base = [s for n, s, m in shown if not any(matches(n, nw[0]) for nw in f["new"])]
    ref = Compound(base).bounding_box().center() if base else Vector(0, 0, 0)
    guides, placed = [], {}
    for nw in f["new"]:
        prefixes, off = nw[0], nw[1]
        guided = nw[2] if len(nw) > 2 else None
        for k, (n, s, m) in enumerate(shown):
            if not matches(n, prefixes) or n in placed:
                continue
            c = s.bounding_box().center()
            if off[0] == "out":
                ax, dist = off[1], off[2]
                sign = 1 if (c.X, c.Y, c.Z)[ax] > (ref.X, ref.Y, ref.Z)[ax] else -1
                v = [0, 0, 0]
                v[ax] = sign * dist
            else:
                v = list(off)
            shown[k] = (n, Pos(*v) * s, m)
            placed[n] = v
            if guided is None or any(n.startswith(p) for p in guided):
                guides.append({"points": [(c.X, c.Y, c.Z), (c.X + v[0], c.Y + v[1], c.Z + v[2])]})
    if f["look"].get("section"):
        shown = section_cut(shown)
    d = OUT / f["name"]
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.stl"):
        old.unlink()
    manifest = []
    for n, s, m in shown:
        p = d / f"{n}.stl"
        export_stl(s, str(p), tolerance=0.04, angular_tolerance=0.15)
        manifest.append({"name": n, "file": str(p), "mat": m})
    (d / "manifest.json").write_text(json.dumps(manifest, indent=1))
    labels = []
    for text, spec in f["labels"]:
        if isinstance(spec, str) or (isinstance(spec, list) and spec and isinstance(spec[0], str)):
            prefs = [spec] if isinstance(spec, str) else spec
            pts = [tuple(s.bounding_box().center()) for n, s, m in shown if matches(n, prefs) and not n.endswith("__cap")]
            if not pts:
                raise KeyError(f"{f['name']}: nothing matches {spec}")
        else:
            pts = [tuple(p) for p in spec]
        labels.append({"text": text, "points": pts})
    look = {k: v for k, v in f["look"].items() if k != "section"}
    (d / "points.json").write_text(json.dumps({"title": f["title"], "view": f["view"], "doc": f["doc"], "labels": labels,
                                               "guides": guides, "lines": f["lines"], **look}, indent=1))
    print(f"{f['name']}: {len(manifest)} meshes, {len(labels)} labels, {len(guides)} guides")


if __name__ == "__main__":
    want = set(sys.argv[1:])
    for f in FIGS:
        if not want or f["name"] in want:
            build(f)
