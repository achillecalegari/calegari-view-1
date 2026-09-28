"""Calegari View 1: automatic design checks. Exit code 1 if anything fails.

1. every printed part is ONE solid (no floating islands in the print files)
2. no interference between any two parts, at home and at the four shift extremes,
   with the Graflok blade and the board latch both locked and open
3. tripod clamp envelopes (landscape on the bottom plate, portrait on the side handle)
   stay clear of every moving part
"""
import itertools, sys, time
from build123d import *
from params import *
import parts as P
from assembly import assemble, Item

THRESHOLD = 0.3  # mm3

# pairs that touch or nest by design (prefix pairs)
EXPECTED = [
    # heat-set inserts sit in their hosts (interference fit) and carry their screws
    ("insert_", "body"), ("insert_", "y_plate"), ("insert_", "x_plate"), ("insert_", "graflok_module"),
    ("insert_", "board_holder"), ("insert_", "adapter_ring"), ("insert_", "way_"), ("insert_", "y_turret"),
    ("insert_", "screw_"), ("insert_", "stop_pin"),
    # threads cut or formed in the plastic: grubs in the gib rails, latch screws, ball plungers
    ("grub_gib", "way_"), ("grub_latch", "board_holder"), ("screw_xway", "way_x"), ("washer_", "screw_"), ("washer_x_thrust", "rod_"), ("washer_x_thrust", "nut_x_thrust"), ("washer_y_end", "rod_"), ("washer_y_end", "nut_y_end"), ("plunger_y", "body"), ("plunger_x", "y_plate"),
    # the detent balls stand 1.0 proud in the 0.8 gap: they press on the plate and click into a dimple at zero
    ("plunger_y", "y_plate"), ("plunger_x", "x_plate"),
    # rods: bushings, drive nuts, cap nuts, O-rings (stretched)
    ("rod_", "bush_"), ("rod_", "nut_"), ("rod_", "oring_"), ("rod_", "knob_"), ("knob_", "inlay_knob"),
    # O-rings squeezed between their seat and the knob
    ("oring_y", "body"), ("oring_y", "knob_y"), ("oring_x", "y_plate"), ("oring_x", "knob_x"),
    # press fits and contacts
    ("bush_y", "body"), ("bush_x", "y_plate"), ("arca_", "body"), ("vial_side", "body"), ("vial_top", "top_handle"),
    ("inlay_", "body"), ("inlay_", "y_plate"), ("inlay_", "x_plate"), ("inlay_", "focus_ring"), ("inlay_", "top_handle"),
    ("inlay_xway", "way_x"), ("velvet_", "body"), ("velvet_", "y_plate"), ("velvet_", "x_plate"),
    ("felt_", "board_holder"), ("felt_board", "lensboard"), ("felt_adapter", "adapter_ring"),
    ("focus_ring", "helicoid"), ("helicoid", "adapter_ring"), ("helicoid", "flange"), ("flange", "x_plate"),
    ("lens", "lensboard"), ("lens", "lens_glass"), ("spring_latch", "holder_latch"), ("spring_latch", "board_holder"),
    ("rb_", "rb_"),
    # countersunk heads seat in their cones
    ("screw_gf", "graflok_module"), ("screw_blade", "graflok_blade"), ("screw_flange", "x_plate"), ("screw_yway", "way_y"),
    ("screw_flange", "flange"),                 # M3 threads in the metal flange
    # The RB67 envelope has no lips or Graflok slots: the back-to-module fit is verified on the
    # real back with the printed module (docs/calibration.md), not here.
    ("rb_", "graflok_"), ("rb_", "screw_blade"), ("rb_", "screw_wheel"),
]


def expected(a, b):
    for p, q in EXPECTED:
        if (a.startswith(p) and b.startswith(q)) or (a.startswith(q) and b.startswith(p)):
            return True
    return False


def boxes_overlap(ba, bb):
    return not (ba.max.X < bb.min.X or bb.max.X < ba.min.X or ba.max.Y < bb.min.Y or bb.max.Y < ba.min.Y
                or ba.max.Z < bb.min.Z or bb.max.Z < ba.min.Z)


def clamp_envelopes():
    """65 x 65 mm Arca clamp with jaws reaching 4 mm above the plate's clamp face."""
    y_face = -BODY / 2 - PLINTH + ARCA_POCKET - ARCA_T
    landscape = P.box_at(-32.5, 32.5, y_face - 25, y_face + 4.0, ARCA_ZC - 32.5, ARCA_ZC + 32.5)
    x_face = BODY / 2 + SIDE_T - ARCA_POCKET + ARCA_T
    yc = SIDE_ARCA_YC
    portrait = P.box_at(x_face - 4.0, x_face + 25, yc - 32.5, yc + 32.5, ARCA_ZC - 32.5, ARCA_ZC + 32.5)
    return [Item("clamp_landscape", landscape, "clamp"), Item("clamp_portrait", portrait, "clamp")]


CLAMP_OK = ("arca_", "body")


def interferences(items):
    found = []
    boxes = {id(i): i.shape.bounding_box() for i in items}
    for a, b in itertools.combinations(items, 2):
        if a.name.startswith("clamp") or b.name.startswith("clamp"):
            other = b if a.name.startswith("clamp") else a
            if other.name.startswith(CLAMP_OK) or (a.name.startswith("clamp") and b.name.startswith("clamp")):
                continue
        elif expected(a.name, b.name):
            continue
        if not boxes_overlap(boxes[id(a)], boxes[id(b)]):
            continue
        try:
            v = (a.shape & b.shape).volume
        except Exception:
            v = -1.0
        if v > THRESHOLD or v < 0:
            found.append((a.name, b.name, round(v, 2)))
    return found


def single_solids():
    bad = []
    for it in assemble():
        if it.printed and len(it.shape.solids()) != 1:
            bad.append((it.name, len(it.shape.solids())))
    return bad


if __name__ == "__main__":
    fails = 0
    bad = single_solids()
    print(f"printed parts that are not one solid: {len(bad)}")
    for n, k in bad:
        print(f"   {n}: {k} solids")
    fails += len(bad)
    cases = [(0, 0, True, True), (SHIFT_X, RISE, True, True), (-SHIFT_X, -FALL, True, True),
             (SHIFT_X, -FALL, True, True), (-SHIFT_X, RISE, True, True), (0, 0, False, False)]
    if len(sys.argv) > 1:
        cases = cases[: int(sys.argv[1])]
    for sx, sy, bl, ll in cases:
        t = time.time()
        items = assemble(sx, sy, 0.0, blade_locked=bl, latch_locked=ll) + clamp_envelopes()
        r = interferences(items)
        state = "" if bl else " (blade and latch open)"
        print(f"shift x={sx:+.0f} y={sy:+.0f}{state}: {len(r)} interferences ({time.time() - t:.0f}s)")
        for a, b, v in r:
            print(f"   {a:30s} x {b:30s} {v} mm3")
        fails += len(r)
    sys.exit(1 if fails else 0)
