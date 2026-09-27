"""Export everything needed to print the camera.

print/step/     STEP of every printed part, in assembly coordinates (open in Fusion, FreeCAD...)
print/stl/      STL of every printed part, already oriented on the bed
print/inlays/   coloured dot inlays (same coordinates as their part's STL) for AMS printing
print/plates/   Bambu P1S build plates (256 x 256), one material per plate, as 3MF
print/test/     the test prints to run before anything else
print/templates/ 1:1 SVG cutting templates for the velvet and felt (V1 to V4)
print/PRINTABILITY.txt  overhang and bridge report for every part in its print orientation

python export.py [--fast]    (--fast skips the printed threads)
"""
import math, pathlib, sys
import numpy as np
import trimesh
from build123d import *
from params import *
import parts as P

ROOT = pathlib.Path(__file__).resolve().parent.parent / "print"
FAST = "--fast" in sys.argv
BED = 256.0

FLIP = trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])
EYE = np.eye(4)
# rails and gib strips print lying on their outer face: the flanks are perimeters, not layers
ON_PLUS_X = trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0])
ON_MINUS_X = trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0])
ON_PLUS_Y = trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0])
ON_MINUS_Y = trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0])


def mesh(shape, tol=0.02):
    vs, fs = shape.tessellate(tol, 0.15)
    return trimesh.Trimesh(np.array([(v.X, v.Y, v.Z) for v in vs]), np.array(fs), process=True)


def catalogue():
    """(name, shape, orientation matrix, copies, material, inlays[(suffix, shape)])"""
    thread = not FAST
    kn, kidx = P.knob_part()
    yred, ywhite = P.y_plate_inlays()
    xred, xwhite = P.x_plate_inlays()
    fm = P.focus_ring_marks(0.6, lift=0)
    return [
        ("body", P.body_part(), FLIP, 1, "black", [("red", P.body_index_inlay())]),
        ("graflok_module", P.graflok_module(), FLIP, 1, "black", []),
        ("graflok_blade", P.graflok_blade(), FLIP, 1, "red", []),
        ("graflok_wheel", P.graflok_wheel(), EYE, 1, "black", []),
        ("y_plate", P.y_plate_part(), FLIP, 1, "black", [("red", yred), ("white", ywhite)]),
        ("way_y_fixed", P.way_rail("y", 1, False), ON_PLUS_X, 1, "black", []),
        ("way_y_gib", P.way_rail("y", -1, True), ON_MINUS_X, 1, "black", []),
        ("gib_y", P.gib_strip("y", -1), ON_MINUS_X, 1, "black", []),
        ("way_x_fixed", P.way_rail("x", -1, False), ON_MINUS_Y, 1, "black", [("red", P.way_x_index_inlay())]),
        ("way_x_gib", P.way_rail("x", 1, True), ON_PLUS_Y, 1, "black", []),
        ("gib_x", P.gib_strip("x", 1), ON_PLUS_Y, 1, "black", []),
        ("x_plate", P.x_plate_part(), EYE, 1, "black", [("red", xred), ("white", xwhite)]),
        ("x_turret", P.x_turret(), FLIP, 1, "black", []),
        ("focus_ring", P.focus_ring_part(), FLIP, 1, "black", [("red", fm[0]), ("white", Compound(fm[1:]))]),
        ("adapter_ring", P.adapter_part(with_thread=thread), FLIP, 1, "black", []),
        ("board_holder", P.holder_part(), EYE, 1, "black", []),
        ("holder_latch", P.holder_latch(), EYE, 1, "red", []),
        ("knob", kn, EYE, 2, "black", [("red", kidx)]),
        ("top_handle", P.top_handle(), EYE, 1, "black", []),
    ]


def oriented(m, T):
    m = m.copy()
    m.apply_transform(T)
    return m


def drop(meshes):
    """Translate a group (part + inlays) so the part sits on the bed at the origin."""
    b = meshes[0].bounds
    t = [-b[0][0], -b[0][1], -b[0][2]]
    out = []
    for m in meshes:
        m = m.copy()
        m.apply_translation(t)
        out.append(m)
    return out


def printability(m):
    """Downward-facing area not on the bed (overhangs steeper than 45 deg) and the largest span."""
    n = m.face_normals
    z = m.triangles_center[:, 2]
    down = (n[:, 2] < -0.72) & (z > 0.3)
    area = float(m.area_faces[down].sum())
    span = 0.0
    if down.any():
        sub = m.submesh([np.where(down)[0]], append=True)
        for part in sub.split(only_watertight=False):
            e = part.extents
            span = max(span, min(e[0], e[1]))
    return area, span


def pack(items):
    """Shelf packing on the P1S bed. items: [(label, [meshes])]. Returns plates of placed groups."""
    items = sorted(items, key=lambda it: -max(it[1][0].extents[:2]))
    plates = []
    margin, gap = 8.0, 6.0
    for label, group in items:
        w, d = group[0].extents[0], group[0].extents[1]
        if w > BED - 2 * margin or d > BED - 2 * margin:
            raise ValueError(f"{label} does not fit the bed: {w:.0f} x {d:.0f}")
        placed = False
        for pl in plates:
            x, y, row = pl["cursor"]
            if x + w > BED - margin:
                x, y, row = margin, y + row + gap, 0.0
            if y + d <= BED - margin:
                pl["groups"].append((label, [g.copy() for g in group], (x, y)))
                pl["cursor"] = (x + w + gap, y, max(row, d))
                placed = True
                break
        if not placed:
            plates.append({"groups": [(label, [g.copy() for g in group], (margin, margin))],
                           "cursor": (margin + w + gap, margin, d)})
    return plates


def write_plate(path, groups):
    scene = trimesh.Scene()
    lo = np.array([1e9, 1e9]); hi = -lo
    for label, meshes, (x, y) in groups:
        b = meshes[0].bounds
        lo = np.minimum(lo, [x, y]); hi = np.maximum(hi, [x + b[1][0], y + b[1][1]])
    shift = (BED - (hi - lo)) / 2 - lo
    for label, meshes, (x, y) in groups:
        for k, m in enumerate(meshes):
            m = m.copy()
            m.apply_translation([x + shift[0], y + shift[1], 0])
            scene.add_geometry(m, node_name=label if k == 0 else f"{label}_inlay{k}", geom_name=label if k == 0 else f"{label}_inlay{k}")
    scene.export(str(path))


def svg_page(path, title, shapes, note):
    """A4 page, 1:1 in mm. shapes: SVG elements already in mm around (0, 0), drawn at the page centre."""
    body = "\n".join(shapes)
    path.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">
<rect width="210" height="297" fill="white"/>
<text x="15" y="18" font-family="Helvetica, Arial" font-size="6" font-weight="bold">{title}</text>
<text x="15" y="26" font-family="Helvetica, Arial" font-size="3.6">{note}</text>
<text x="15" y="31" font-family="Helvetica, Arial" font-size="3.6">Print at 100 % (no "fit to page"), then check the 100 mm bar with a ruler.</text>
<g stroke="black" stroke-width="0.25"><line x1="55" y1="282" x2="155" y2="282"/><line x1="55" y1="279" x2="55" y2="285"/><line x1="155" y1="279" x2="155" y2="285"/></g>
<text x="105" y="278" font-family="Helvetica, Arial" font-size="3.6" text-anchor="middle">100 mm</text>
<g transform="translate(105 152)" fill="#e6e6e6" fill-rule="evenodd" stroke="black" stroke-width="0.3">
{body}
</g>
</svg>
''')


def rect_path(x0, y0, x1, y1, r=0.0):
    """Rectangle (y up in the model, so flipped for SVG) with optional corner radius, as path data."""
    y0, y1 = -y1, -y0
    if not r:
        return f"M{x0} {y0}H{x1}V{y1}H{x0}Z"
    return (f"M{x0 + r} {y0}H{x1 - r}A{r} {r} 0 0 1 {x1} {y0 + r}V{y1 - r}A{r} {r} 0 0 1 {x1 - r} {y1}"
            f"H{x0 + r}A{r} {r} 0 0 1 {x0} {y1 - r}V{y0 + r}A{r} {r} 0 0 1 {x0 + r} {y0}Z")


def ring_path(r0, r1):
    return (f"M{r1} 0A{r1} {r1} 0 1 0 {-r1} 0A{r1} {r1} 0 1 0 {r1} 0Z"
            f"M{r0} 0A{r0} {r0} 0 1 1 {-r0} 0A{r0} {r0} 0 1 1 {r0} 0Z")


def templates():
    d = ROOT / "templates"
    ob, oy = opening_body(BODY_Z1), opening_yplate(YP_Z1)
    hy = max(oy[1], 33.0)
    svg_page(d / "V1_velvet_body.svg", "V1 - velvet, body front",
             [f'<path d="{rect_path(-46.5, -72, 44, 72)} {rect_path(-ob[0] - 1, -ob[1] - 1, ob[0] + 1, ob[1] + 1, 3)}"/>',
              '<g font-family="Helvetica, Arial" font-size="4" stroke="none" fill="black"><text x="0" y="-62" text-anchor="middle">TOP</text><text transform="translate(-42 0) rotate(-90)" text-anchor="middle">rail side</text></g>'],
             "Cut on the lines. The camera sees this from the front: the vertical rail is on the left.")
    svg_page(d / "V2_velvet_y_plate.svg", "V2 - velvet, Y plate front",
             [f'<path d="{rect_path(-72, -45.5, 72, 40)} {rect_path(-oy[0] - 1, -hy - 1, oy[0] + 1, hy + 1, 3)}"/>',
              '<text x="0" y="-34" font-family="Helvetica, Arial" font-size="4" text-anchor="middle" stroke="none" fill="black">TOP</text>'],
             "Cut on the lines. The top edge stops 4 mm below the two white pads.")
    svg_page(d / "V3_V4_felt_rings.svg", "V3 and V4 - felt rings, board holder",
             [f'<g transform="translate(0 -65)"><path d="{ring_path(30.7, 34.8)}"/><text y="1.5" font-family="Helvetica, Arial" font-size="5" text-anchor="middle" stroke="none" fill="black">V3</text></g>',
              f'<g transform="translate(0 45)"><path d="{ring_path(REAR_CLEAR_D / 2 + 3.6, 44.8)}"/><text y="1.5" font-family="Helvetica, Arial" font-size="5" text-anchor="middle" stroke="none" fill="black">V4</text></g>'],
             "1 mm adhesive felt. V3: groove on the back of the holder. V4: shallow seat under the lens board.")


if __name__ == "__main__":
    for d in ("step", "stl", "inlays", "plates", "test", "templates"):
        (ROOT / d).mkdir(parents=True, exist_ok=True)
        for f in (ROOT / d).iterdir():          # start clean: no stale parts from older versions
            if f.is_file():
                f.unlink()
    report = ["part                 copies  material  overhang_area_mm2  largest_downward_span_mm"]
    plate_items = {"black": [], "red": []}
    for name, shape, T, copies, mat, inlays in catalogue():
        export_step(shape, str(ROOT / "step" / f"{name}.step"))
        group = drop([oriented(mesh(shape, 0.01 if name in ("x_plate", "adapter_ring") else 0.02), T)]
                     + [oriented(mesh(s, 0.02), T) for _, s in inlays])
        group[0].export(str(ROOT / "stl" / f"{name}.stl"))
        for (suffix, _), m in zip(inlays, group[1:]):
            m.export(str(ROOT / "inlays" / f"{name}__{suffix}.stl"))
        area, span = printability(group[0])
        report.append(f"{name:20s} {copies:6d}  {mat:8s}  {area:17.0f}  {span:10.1f}")
        for c in range(copies):
            plate_items[mat].append((f"{name}_{c + 1}" if copies > 1 else name, [group[0]]))
        print(f"{name}: {group[0].extents.round(1)}")
    (ROOT / "PRINTABILITY.txt").write_text("\n".join(report) + "\n")
    summary = []
    for mat, items in plate_items.items():
        for i, pl in enumerate(pack(items), 1):
            path = ROOT / "plates" / f"plate_{i:02d}_{mat}.3mf" if mat == "black" else ROOT / "plates" / f"plate_{mat}_{i}.3mf"
            write_plate(path, pl["groups"])
            summary.append(f"{path.name}: " + ", ".join(g[0] for g in pl["groups"]))
    # test prints: Graflok module with blade and wheel; M65 thread coupons
    test = [("shrink_gauge_100mm", [drop([oriented(mesh(P.shrink_gauge()), EYE)])[0]]),
            ("graflok_module", [drop([oriented(mesh(P.graflok_module()), FLIP)])[0]]),
            ("graflok_blade", [drop([oriented(mesh(P.graflok_blade()), FLIP)])[0]]),
            ("graflok_wheel", [drop([oriented(mesh(P.graflok_wheel()), EYE)])[0]])]
    # dovetail coupons: 40 mm slices of the real rails, gib strips and plate edges (slide them by hand)
    yp, xp_ = P.y_plate_part(), P.x_plate_part()
    cut_y = lambda sh: sh & P.box_at(-80, 80, -20, 20, -50, 120)
    cut_x = lambda sh: sh & P.box_at(-20, 20, -80, 80, -50, 120)
    coupons = [
        ("coupon_way_y_fixed", cut_y(P.way_rail("y", 1, False)), ON_PLUS_X),
        ("coupon_way_y_gib", cut_y(P.way_rail("y", -1, True)), ON_MINUS_X),
        ("coupon_gib_y", cut_y(P.gib_strip("y", -1)), ON_MINUS_X),
        ("coupon_lip_y_left", yp & P.box_at(50, 75, -20, 20, YP_Z0 - 0.1, YP_Z1 + 1), FLIP),
        ("coupon_lip_y_right", yp & P.box_at(-75, -50, -20, 20, YP_Z0 - 0.1, YP_Z1 + 1), FLIP),
        ("coupon_way_x_fixed", cut_x(P.way_rail("x", -1, False)), ON_MINUS_Y),
        ("coupon_way_x_gib", cut_x(P.way_rail("x", 1, True)), ON_PLUS_Y),
        ("coupon_gib_x", cut_x(P.gib_strip("x", 1)), ON_PLUS_Y),
        ("coupon_lip_x_bottom", xp_ & P.box_at(-20, 20, -75, -50, XP_Z0 - 0.1, XP_Z1 + 1), EYE),
        ("coupon_lip_x_top", xp_ & P.box_at(-20, 20, 50, 75, XP_Z0 - 0.1, XP_Z1 + 1), EYE),
    ]
    for label, sh, T in coupons:
        test.append((label, [drop([oriented(mesh(sh, 0.02), T)])[0]]))
    if not FAST:
        xp = P.x_plate_part()  # no threads in the plate any more: coupon = flange pocket fit
        ad = P.adapter_part(with_thread=True)
        coupon = ad & P.cyl_z(45, ADAPTER_Z0 - 10, ADAPTER_Z0 + 3)
        test.append(("m65_male_coupon", [drop([oriented(mesh(coupon, 0.01), FLIP)])[0]]))
        fl = xp & P.cyl_z(46, XP_Z0 - 1, XP_Z1 + 1)
        test.append(("flange_pocket_coupon", [drop([oriented(mesh(fl, 0.02), EYE)])[0]]))
    for label, g in test:
        g[0].export(str(ROOT / "test" / f"{label}.stl"))
    for i, pl in enumerate(pack(test), 1):
        write_plate(ROOT / "plates" / f"plate_00_test_{i}.3mf", pl["groups"])
        summary.append(f"plate_00_test_{i}.3mf: " + ", ".join(g[0] for g in pl["groups"]))
    # lens shims: their own plate, printed at 0.2 mm layers
    shims = [(f"copal0_shim_{t:.1f}mm", [drop([oriented(mesh(P.copal0_shim(t)), EYE)])[0]]) for t in P.SHIM_STEPS]
    for label, g in shims:
        g[0].export(str(ROOT / "stl" / f"{label}.stl"))
    for i, pl in enumerate(pack(shims), 1):
        write_plate(ROOT / "plates" / f"plate_07_shims_0.2mm_layers.3mf", pl["groups"])
        summary.append("plate_07_shims_0.2mm_layers.3mf: " + ", ".join(g[0] for g in pl["groups"]))
    templates()
    (ROOT / "plates" / "PLATES.txt").write_text("\n".join(summary) + "\n")
    print("\n".join(summary))
    print((ROOT / "PRINTABILITY.txt").read_text())
