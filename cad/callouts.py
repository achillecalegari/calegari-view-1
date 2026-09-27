"""Lettered part maps for the assembly manual: every hole of a printed part and what goes into it.

python callouts.py [sheet ...]   writes out/mesh_cal_<sheet>/manifest.json and points.json
render/callouts.sh renders them (render/white.py with PTS) and letters them (render/letter.py).

A sheet shows one printed part with the hardware that goes into it, already in place. Each letter
points at every instance of one kind of hardware (or at a feature), and docs/assembly.md has the
matching table: letter, what, how many, how.
"""
import json, math, pathlib, sys
from build123d import *
from params import *
import parts as P
from assembly import assemble

OUT = pathlib.Path(__file__).resolve().parent.parent / "out"

H = BODY / 2
Z_RING = HELI_Z0 + HELI_GRIP_Z[0]
R_RING = FOCUS_OD / 2


def ring_point(ang, r, z):
    a = math.radians(ang)
    return (-r * math.sin(a), r * math.cos(a), z)


# name, title, view (Blender direction: +x photographer's left, +y behind, +z up), items, letters
# letters: (letter, prefix or list of points, offset of the point along the view is not needed)
SHEETS = [
    ("body_rear", "Body, from behind", (0.25, 1.0, 0.3),
     ["body", "vial_side", "insert_gf"],
     [("A", "insert_gf"),
      ("B", [(sum(TRAP_X) / 2, 0.0, SEAT_Z)]),
      ("C", [(-60.0, 20.0, 2.0)])]),
    ("body_front", "Body, from the front", (-0.3, -1.0, 0.35),
     ["body", "insert_yrail", "plunger_y", "bush_y"],
     [("D", "insert_yrail"), ("E", "plunger_y"), ("F", "bush_y"),
      ("G", [(48.0, -50.0, BODY_Z1), (48.0, 20.0, BODY_Z1)])]),
    ("body_top", "Body, top and right side", (-1.0, -0.45, 0.85),
     ["body", "insert_top", "vial_side"],
     [("H", "insert_top"), ("J", "vial_side"), ("K", [(Y_SCREW_X, H, Y_SCREW_Z)])]),
    ("body_under", "Body, underside and L bracket", (0.9, -0.55, -0.75),
     ["body", "insert_arca_b", "insert_arca_s"],
     [("L", "insert_arca_b"), ("M", "insert_arca_s"), ("N", [(Y_SCREW_X, -H - PLINTH, Y_SCREW_Z)])]),
    ("body_velvet", "Body front: where the velvet goes", (0.0, -1.0, 0.12),
     ["body", "velvet_body", "plunger_y"],
     [("V1", [(-20.0, -58.0, BODY_Z1 + GAP)]), ("G", [(48.0, -50.0, BODY_Z1), (48.0, 20.0, BODY_Z1)]), ("E", "plunger_y")]),
    ("graflok_inserts", "Graflok module, from behind", (0.2, 1.0, 0.3),
     ["graflok_module", "insert_blade"],
     [("A", "insert_blade"), ("B", [(x, y, GF_Z0) for x, y in P.GF_SCREWS])]),
    ("graflok_blade", "Graflok module with blade and wheel", (0.2, 1.0, 0.3),
     ["graflok_module", "graflok_blade", "graflok_wheel", "screw_blade", "screw_wheel", "screw_gf"],
     [("C", "screw_blade"), ("D", "graflok_wheel"), ("E", "screw_gf"), ("F", [(0.0, -63.0, -2.0)])]),
    ("yplate_rear", "Y plate, from behind", (0.35, 1.0, 0.3),
     ["y_plate", "nut_y_drive", "screw_yblock"],
     [("A", "nut_y_drive"), ("B", "screw_yblock"), ("C", [(x, y, YP_Z0 - GAP / 2) for x, y in P.PADS_YREAR])]),
    ("yplate_front", "Y plate, from the front", (-0.3, -1.0, 0.35),
     ["y_plate", "insert_xrail", "plunger_x", "pad_y", "plug_yblock", "bush_x"],
     [("D", "insert_xrail"), ("E", "plunger_x"), ("F", "pad_y"), ("G", "plug_yblock"), ("H", "bush_x")]),
    ("yplate_velvet", "Y plate front: where the velvet goes", (0.0, -1.0, 0.12),
     ["y_plate", "velvet_yplate", "pad_y", "plunger_x", "rail_x", "screw_xrail", "bush_x"],
     [("V2", [(-30.0, -39.0, YP_Z1 + GAP)]), ("F", "pad_y"), ("E", "plunger_x")]),
    ("xplate_rear", "Lens panel, from behind", (0.35, 1.0, 0.35),
     ["x_plate", "insert_turret", "x_turret", "screw_turret", "nut_x_drive", "screw_flange"],
     [("A", "insert_turret"), ("B", "nut_x_drive"), ("C", "screw_turret"), ("D", "screw_flange")]),
    ("xplate_front", "Lens panel, from the front", (-0.35, -1.0, 0.35),
     ["x_plate", "flange", "insert_stop", "stop_pin", "screw_xblock"],
     [("E", "flange"), ("F", "stop_pin"), ("G", "screw_xblock")]),
    ("focus_ring", "Focus ring, from behind", (0.45, 1.0, 0.55),
     ["focus_ring", "helicoid"],
     [("A", [ring_point(a, R_RING, Z_RING + FOCUS_W / 2) for a in (45, 135, 225, 315)]),
      ("B", [ring_point(-P.STOP_TAB_ANG, R_RING - 3.0, Z_RING - 0.6)]),
      ("C", [ring_point(-P.LEVER_ANG, R_RING + 6, Z_RING + FOCUS_W / 2)]),
      ("D", [ring_point(0.0, R_RING, Z_RING + FOCUS_W - 2.5)])]),
    ("holder_rear", "Board holder, from behind", (0.3, 1.0, 0.35),
     ["board_holder", "insert_holder", "felt_adapter"],
     [("A", "insert_holder"), ("V3", [(0.0, -32.7, 64.0)])]),
    ("holder_front", "Board holder, from the front", (-0.3, -1.0, 0.4),
     ["board_holder", "felt_board", "spring_latch", "holder_latch", "screw_latch"],
     [("V4", [(0.0, -39.0, 68.5)]), ("B", "spring_latch"), ("C", "holder_latch"), ("D", "screw_latch")]),
    ("top_handle", "Top handle", (0.4, 1.0, 0.7),
     ["top_handle", "vial_top", "screw_top"],
     [("A", "vial_top"), ("B", "screw_top")]),
]


def knob_sheet():
    """The knob alone, from below: nut pocket, grub hole, O-ring groove."""
    k, _ = P.knob_part()
    d = KNOB_D
    return (("knob", "Knob, from below", (0.35, 1.0, -0.2),
             [("knob", k, "body_black")],
             [("A", [(0.0, NUT_AF / 2 - 0.6, 0.0)]),
              ("B", [(d / 2, 0.0, NUT_T + 3.0)])]))


# per-sheet camera distance and exposure (the knob is small: the lights are not scaled down)
LOOK = {"body_top": {"dist": 5.4}, "body_under": {"dist": 5.4}, "knob": {"dist": 6.0, "expo": -6.5},
        "top_handle": {"dist": 4.8}}


def build(sheet):
    name, title, view, prefixes, letters = sheet
    d = OUT / f"mesh_cal_{name}"
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.stl"):
        f.unlink()
    if prefixes and isinstance(prefixes[0], tuple):
        shown = prefixes
    else:
        shown = [(i.name, i.shape, i.mat) for i in ITEMS if any(i.name.startswith(p) for p in prefixes)]
    manifest = []
    for n, s, m in shown:
        f = d / f"{n}.stl"
        export_stl(s, str(f), tolerance=0.04, angular_tolerance=0.15)
        manifest.append({"name": n, "file": str(f), "mat": m})
    (d / "manifest.json").write_text(json.dumps(manifest, indent=1))
    pts = []
    for letter, spec in letters:
        if isinstance(spec, str):
            ps = []
            for n, s, _ in shown:
                if n.startswith(spec):
                    c = s.bounding_box().center()
                    ps.append((c.X, c.Y, c.Z))
            if not ps:
                raise KeyError(f"{name}: nothing matches {spec}")
        else:
            ps = [tuple(p) for p in spec]
        pts.append({"letter": letter, "points": ps})
    (d / "points.json").write_text(json.dumps({"title": title, "view": view, "labels": pts, **LOOK.get(name, {})}, indent=1))
    print(f"{name}: {len(manifest)} meshes, {len(pts)} letters")


if __name__ == "__main__":
    ITEMS = assemble()
    want = set(sys.argv[1:])
    for sh in SHEETS + [knob_sheet()]:
        if not want or sh[0] in want:
            build(sh)
