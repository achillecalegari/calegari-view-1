"""Calegari View 1: full assembly with every fastener, for checks, renders and exports.

assemble(sx, sy, E) -> list of Item(name, shape, material, printed)
  sx, sy: lateral shift and rise (mm), E: explode distance (mm, 0 = assembled).
"""
from dataclasses import dataclass
import math
from build123d import *
from params import *
import parts as P
import hardware as hw
from hardware import orient

H = BODY / 2


@dataclass
class Item:
    name: str
    shape: object
    mat: str
    printed: bool = False


# explode directions per group (unit vectors times E)
EXPLODE = {
    "body": (0, 0, 0), "graflok": (0, 0, -1.2), "blade": (0, 0, -1.7), "back": (0, 0, -3.0),
    "arca_b": (0, -0.9, 0), "arca_s": (0.9, 0, 0), "top_handle": (0, 1.1, 0), "side_handle": (1.1, 0, 0),
    "y_rail": (0, 0, 0.45), "y_block": (0, 0, 0.7), "y_drive": (0, 0, 0.3), "y_knob": (0, 0.9, 0),
    "y_plate": (0, 0, 1.0), "x_rail": (0, 0, 1.45), "x_block": (0, 0, 1.7), "x_drive": (0, 0, 1.3),
    "x_knob": (-0.9, 0, 1.0), "x_plate": (0, 0, 2.1), "turret": (0, 0, 1.8), "flange": (0, 0, 2.5),
    "helicoid": (0, 0, 2.9), "focus": (0, 0, 3.3), "adapter": (0, 0, 3.7), "holder": (0, 0, 4.2),
    "latch": (0, 0.3, 4.6), "board": (0, 0, 5.0), "lens": (0, 0, 5.8),
}


def assemble(sx=0.0, sy=0.0, E=0.0, thread=False, blade_locked=True, latch_locked=True, back=True):
    items = []

    def add(name, shape, mat, group, printed=False, extra=(0, 0, 0)):
        d = EXPLODE[group]
        if E:
            shape = Pos(d[0] * E + extra[0] * E, d[1] * E + extra[1] * E, d[2] * E + extra[2] * E) * shape
        items.append(Item(name, shape, mat, printed))

    # ---------------- body ----------------
    add("body", P.body_part(), "body_black", "body", True)
    add("vial_side", P.body_vial(), "vial", "body")
    add("inlay_body_index", P.body_index_inlay(), "red", "body")
    for x, y in P.GF_SCREWS:
        add(f"insert_gf_{x}_{y}", Pos(x, y, SEAT_Z) * hw.heat_insert(3, 3.0), "brass", "body")
    for yy in P.Y_RAIL_SCREWS:
        add(f"insert_yrail_{yy}", Pos(Y_RAIL_X, yy, YP_Z0 - BLOCK_H - 3.0) * hw.heat_insert(3, 3.0), "brass", "body")
    for x in P.TOP_POSTS_X:
        add(f"insert_top_{x}", Pos(x, H, P.HANDLE_INSERT_Z_TOP) * orient(hw.heat_insert(4), "-y"), "brass", "body")

    # ---------------- Graflok module and back ----------------
    add("graflok_module", P.graflok_module(), "body_black", "graflok", True)
    for x, y in P.GF_SCREWS:
        add(f"screw_gf_{x}_{y}", Pos(x, y, GF_Z0) * orient(hw.countersunk(3, 8), "-z"), "black_steel", "graflok", extra=(0, 0, -0.6))
    add("graflok_blade", P.graflok_blade(blade_locked), "red", "blade", True)
    add("graflok_wheel", P.graflok_wheel(), "body_black", "blade", True, extra=(0, 0, -0.6))
    for x in P.BLADE_GUIDES_X:
        yb = P.BLADE_Y0 + 4.0 + (0 if blade_locked else 0)
        add(f"screw_blade_{x}", Pos(x, yb, GF_Z0 - 2.2) * orient(hw.countersunk(3, 6), "-z"), "black_steel", "blade", extra=(0, 0, -0.4))
    add("screw_wheel", Pos(*P.WHEEL_XY, GF_Z0 - 5.2 + 1.7) * orient(hw.socket_cap(3, 8), "-z"), "black_steel", "blade", extra=(0, 0, -1.0))
    for x in P.BLADE_GUIDES_X + (P.WHEEL_XY[0],):
        y = P.WHEEL_XY[1] if x == P.WHEEL_XY[0] else P.BLADE_Y0 + 4.0
        add(f"insert_blade_{x}", Pos(x, y, GF_Z0) * hw.heat_insert(3, 3.0), "brass", "graflok")
    if back:
        bk, window, lever = P.rb67_back()
        add("rb_back", bk, "leather", "back")
        add("rb_window", window, "glass_red", "back")
        add("rb_lever", lever, "chrome", "back")

    # ---------------- tripod plates and handles ----------------
    add("arca_bottom", P.arca_plate(), "alu_black", "arca_b")
    y_in = -H - PLINTH + ARCA_POCKET
    for x in (-15.0, 15.0):
        add(f"insert_arca_b_{x}", Pos(x, y_in, ARCA_ZC) * orient(hw.heat_insert(4, 6.4), "+y"), "brass", "body")
    x_in = H + SIDE_T - ARCA_POCKET
    for y in (-15.0, 15.0):
        add(f"insert_arca_s_{y}", Pos(x_in, SIDE_ARCA_YC + y, ARCA_ZC) * orient(hw.heat_insert(4, 6.4), "-x"), "brass", "body")
    add("arca_side", P.side_arca_plate(), "alu_black", "arca_s")
    add("top_handle", P.top_handle(), "body_black", "top_handle", True)
    add("vial_top", P.top_vial(), "vial", "top_handle")
    for x in P.TOP_POSTS_X:
        add(f"screw_top_{x}", Pos(x, H + HANDLE_H - 4.5, P.HANDLE_INSERT_Z_TOP) * orient(hw.socket_cap(4, 50), "+y"),
            "black_steel", "top_handle", extra=(0, 0.5, 0))

    # ---------------- vertical stage ----------------
    rail_z = YP_Z0 - BLOCK_H
    add("rail_y", Pos(Y_RAIL_X, RAIL_Y_OFFSET, rail_z) * Rot(0, 0, 90) * P.mgn9_rail(RAIL_LEN_Y), "steel", "y_rail")
    for yy in P.Y_RAIL_SCREWS:
        add(f"screw_yrail_{yy}", Pos(Y_RAIL_X, yy, rail_z + RAIL_H - 3.0) * hw.socket_cap(3, 6), "black_steel", "y_rail", extra=(0, 0, 0.3))
    blk, seal = P.mgn9_block()
    for i, yy in enumerate(P.Y_BLOCK_Y):
        loc = Pos(Y_RAIL_X, yy + sy, rail_z + BLOCK_UNDER) * Rot(0, 0, 90)
        add(f"block_y{i}", loc * blk, "steel", "y_block")
        add(f"block_y{i}_seal", loc * seal, "red_seal", "y_block")
        for dx in (-BLOCK_HOLES[0] / 2, BLOCK_HOLES[0] / 2):
            for dy in (-BLOCK_HOLES[1] / 2, BLOCK_HOLES[1] / 2):
                add(f"screw_yblock_{i}_{dx}_{dy}", Pos(Y_RAIL_X + dx, yy + sy + dy, YP_Z1 - P.Y_BLOCK_CB) * hw.socket_cap(3, 12),
                    "black_steel", "y_plate", extra=(0, 0, 0.6))
    # drive: rod, bushings, nut, knob, O-ring, nut pair at the bottom
    y_bot, y_top = -H + 0.5, H + KNOB_H - 1.5
    add("rod_y", Pos(Y_SCREW_X, y_bot, Y_SCREW_Z) * orient(hw.threaded_rod(6, y_top - y_bot), "+y"), "steel", "y_drive")
    add("bush_y_top", Pos(Y_SCREW_X, P.Y_CHAN[1], Y_SCREW_Z) * orient(hw.bushing(6, 10, BUSH_L), "+y"), "bronze", "y_drive")
    add("bush_y_bot", Pos(Y_SCREW_X, P.Y_CHAN[0] - BUSH_L, Y_SCREW_Z) * orient(hw.bushing(6, 10, BUSH_L), "+y"), "bronze", "y_drive")
    add("nut_y_drive", Pos(Y_SCREW_X, sy - NUT_T / 2, Y_SCREW_Z) * orient(Rot(0, 0, 30) * hw.hex_nut(6, h=NUT_T), "+y"), "brass", "y_plate")
    for k in range(2):
        add(f"nut_y_bottom{k}", Pos(Y_SCREW_X, -H + 1.0 + k * 5.2, Y_SCREW_Z) * orient(hw.hex_nut(6, h=NUT_T), "+y"), "steel", "y_drive", extra=(0, -0.4, 0))
    add("oring_y", Pos(Y_SCREW_X, H - ORING_T, Y_SCREW_Z) * orient(Torus(4.5, 0.75), "+y") if False else
        Pos(Y_SCREW_X, H - ORING_T / 2, Y_SCREW_Z) * Rot(90, 0, 0) * Torus(4.4, 0.75), "rubber", "y_knob")
    kn, kidx = P.knob_part()
    add("knob_y", Pos(Y_SCREW_X, H, Y_SCREW_Z) * orient(kn, "+y"), "body_black", "y_knob", True)
    add("inlay_knob_y", Pos(Y_SCREW_X, H, Y_SCREW_Z) * orient(kidx, "+y"), "red", "y_knob")
    add("plunger_y", Pos(*P.Y_DETENT, 9.8) * (Cylinder(2.5, 10.5, align=hw.Z_UP) + Pos(0, 0, 10.5) * Sphere(1.5)), "steel", "body")
    add("insert_plunger_y", Pos(*P.Y_DETENT, BODY_Z1 - 8.0) * hw.heat_insert(4), "brass", "body") if False else None

    # ---------------- Y plate ----------------
    add("velvet_body", P.velvet_body(), "velvet", "y_rail")
    add("y_plate", Pos(0, sy, 0) * P.y_plate_part(), "body_black", "y_plate", True)
    add("velvet_yplate", Pos(0, sy, 0) * P.velvet_yplate(), "velvet", "x_rail")
    for i, pad in enumerate(P.y_plate_pads()):
        add(f"pad_y_{i}", Pos(0, sy, 0) * pad, "white_ink", "y_plate", True, extra=(0, 0, 0.5))
    for i, plug in enumerate(P.y_plate_plugs()):
        add(f"plug_yblock_{i}", Pos(0, sy, 0) * plug, "body_black", "y_plate", True, extra=(0, 0, 0.4))
    red, white = P.y_plate_inlays()
    add("inlay_yplate_red", Pos(0, sy, 0) * red, "red", "y_plate")
    add("inlay_yplate_white", Pos(0, sy, 0) * white, "white_ink", "y_plate")
    xr_z = XP_Z0 - BLOCK_H
    add("rail_x", Pos(0, X_RAIL_Y + sy, xr_z) * P.mgn9_rail(RAIL_LEN_X), "steel", "x_rail")
    for i, xx in enumerate(P.rail_holes(RAIL_LEN_X)):
        add(f"insert_xrail_{i}", Pos(xx, X_RAIL_Y + sy, xr_z - 3.0) * hw.heat_insert(3, 3.0), "brass", "y_plate")
        add(f"screw_xrail_{i}", Pos(xx, X_RAIL_Y + sy, xr_z + RAIL_H - 3.0) * hw.socket_cap(3, 6), "black_steel", "x_rail", extra=(0, 0, 0.3))
    for i, xx in enumerate(P.X_BLOCK_X):
        loc = Pos(xx + sx, X_RAIL_Y + sy, xr_z + BLOCK_UNDER)
        add(f"block_x{i}", loc * blk, "steel", "x_block")
        add(f"block_x{i}_seal", loc * seal, "red_seal", "x_block")
        for dx in (-BLOCK_HOLES[1] / 2, BLOCK_HOLES[1] / 2):
            for dy in (-BLOCK_HOLES[0] / 2, BLOCK_HOLES[0] / 2):
                add(f"screw_xblock_{i}_{dx}_{dy}", Pos(xx + sx + dx, X_RAIL_Y + sy + dy, XP_Z1) * hw.countersunk(3, 10),
                    "black_steel", "x_plate", extra=(0, 0, 0.5))
    yx = X_SCREW_Y + sy
    x_left, x_right = P.X_CHAN[1] + BUSH_L + 11.0, -H - KNOB_H + 1.5
    add("rod_x", Pos(x_left, yx, X_SCREW_Z) * orient(hw.threaded_rod(6, x_left - x_right), "-x"), "steel", "x_drive")
    add("bush_x_right", Pos(P.X_CHAN[0], yx, X_SCREW_Z) * orient(hw.bushing(6, 10, BUSH_L), "-x"), "bronze", "x_drive")
    add("bush_x_left", Pos(P.X_CHAN[1] + BUSH_L, yx, X_SCREW_Z) * orient(hw.bushing(6, 10, BUSH_L), "-x"), "bronze", "x_drive")
    for k in range(2):
        add(f"nut_x_end{k}", Pos(P.X_CHAN[1] + BUSH_L + 0.3 + k * 5.2, yx, X_SCREW_Z) * orient(hw.hex_nut(6, h=NUT_T), "+x"), "steel", "x_drive")
    add("nut_x_drive", Pos(sx - NUT_T / 2, yx, X_SCREW_Z) * orient(Rot(0, 0, 30) * hw.hex_nut(6, h=NUT_T), "+x"), "brass", "turret")
    add("oring_x", Pos(-H + ORING_T / 2, yx, X_SCREW_Z) * Rot(0, 90, 0) * Torus(4.4, 0.75), "rubber", "x_knob")
    add("knob_x", Pos(-H, yx, X_SCREW_Z) * orient(kn, "-x"), "body_black", "x_knob", True)
    add("inlay_knob_x", Pos(-H, yx, X_SCREW_Z) * orient(kidx, "-x"), "red", "x_knob")
    add("plunger_x", Pos(P.X_DETENT[0], P.X_DETENT[1] + sy, YP_Z1 - 10.5) * (Cylinder(2.5, 10.5, align=hw.Z_UP) + Pos(0, 0, 10.5) * Sphere(1.5)), "steel", "y_plate")

    # ---------------- lens panel ----------------
    mv = Pos(sx, sy, 0)
    add("x_plate", mv * P.x_plate_part(), "body_black", "x_plate", True)
    red, white = P.x_plate_inlays()
    add("inlay_xplate_red", mv * red, "red", "x_plate")
    add("inlay_xplate_white", mv * white, "white_ink", "x_plate")
    add("x_turret", mv * P.x_turret(), "body_black", "turret", True)
    for x, y in P.TURRET_SCREWS:
        add(f"screw_turret_{x}", mv * Pos(x, y, X_SCREW_Z - 4.5 + 3.5) * orient(hw.socket_cap(3, 10), "-z"), "black_steel", "turret", extra=(0, 0, -0.3))
        add(f"insert_turret_{x}", mv * Pos(x, y, XP_Z0) * hw.heat_insert(3, 3.0), "brass", "x_plate")
    add("flange", mv * P.flange_part(), "alu_black", "flange")
    for a in (0, 90, 180, 270):
        x, y = FLANGE_PCD / 2 * math.cos(math.radians(a)), FLANGE_PCD / 2 * math.sin(math.radians(a))
        add(f"screw_flange_{a}", mv * Pos(x, y, XP_Z0) * orient(hw.countersunk(3, 6), "-z"), "black_steel", "x_plate", extra=(0, 0, -0.5))
    add("stop_pin", mv * Pos(*P.STOP_PIN, XP_Z1) * hw.socket_cap(3, 5), "black_steel", "x_plate", extra=(0, 0, 0.3))
    add("insert_stop", mv * Pos(*P.STOP_PIN, XP_Z1 - 3.0) * hw.heat_insert(3, 3.0), "brass", "x_plate")

    # ---------------- focusing, holder, lens ----------------
    add("helicoid", mv * P.helicoid_part(HELI_INF), "alu_black", "helicoid")
    add("focus_ring", mv * P.focus_ring_part(), "body_black", "focus", True)
    fm = P.focus_ring_marks(0.6, lift=0)
    add("inlay_focus_inf", mv * fm[0], "red", "focus")
    add("inlay_focus_white", mv * Compound(fm[1:]), "white_ink", "focus")
    add("adapter_ring", mv * P.adapter_part(with_thread=thread), "body_black", "adapter", True)
    for a in (45, 135, 225, 315):
        x, y = P.ADAPTER_SCREW_R * math.cos(math.radians(a)), P.ADAPTER_SCREW_R * math.sin(math.radians(a))
        add(f"screw_adapter_{a}", mv * Pos(x, y, ADAPTER_Z0) * orient(hw.button_head(3, 6), "-z"), "black_steel", "adapter", extra=(0, 0, -0.4))
        add(f"insert_holder_{a}", mv * Pos(x, y, HOLDER_Z0) * hw.heat_insert(3, 3.0), "brass", "holder")
    add("board_holder", mv * P.holder_part(), "body_black", "holder", True)
    add("felt_board", mv * P.felt_board(), "felt", "holder")
    add("felt_adapter", mv * (P.cyl_z(34.8, HOLDER_Z0, HOLDER_Z0 + 0.8) - P.cyl_z(30.7, HOLDER_Z0 - 1, HOLDER_Z0 + 2)), "felt", "holder")
    add("holder_latch", mv * P.holder_latch(latch_locked), "red", "latch", True)
    for x in (-9.0, 9.0):
        add(f"screw_latch_{x}", mv * Pos(x, P.LATCH_SCREW_Y, BOARD_Z1 + 2.45) * hw.button_head(2.5, 6),
            "black_steel", "latch", extra=(0, 0, 0.3))
    y_sp0 = BOARD_H / 2 - P.LATCH_ENGAGE + P.LATCH_LEN + (0 if latch_locked else P.LATCH_ENGAGE + 1)
    y_sp1 = BOARD_H / 2 + 22.0
    add("spring_latch", mv * Pos(0, (y_sp0 + y_sp1) / 2, BOARD_Z1 + 1.3) * Rot(90, 0, 0) * Cylinder(1.8, y_sp1 - y_sp0 - 0.2), "steel", "latch")
    add("lensboard", mv * P.lensboard_part(), "alu_black", "board")
    lm, lg = P.lens_part()
    add("lens", mv * lm, "lens_black", "lens")
    add("lens_glass", mv * lg, "glass", "lens")
    return [it for it in items if it is not None]


if __name__ == "__main__":
    import sys, time
    t = time.time()
    it = assemble()
    bb = Compound([i.shape for i in it]).bounding_box()
    print(f"{len(it)} items, {sum(i.printed for i in it)} printed, envelope {bb.size.X:.0f} x {bb.size.Y:.0f} x {bb.size.Z:.0f} mm "
          f"({time.time() - t:.0f}s)")
