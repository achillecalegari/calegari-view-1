"""Export everything needed to print the camera.

print/step/     STEP of every printed part, in assembly coordinates (open in Fusion, FreeCAD...)
print/stl/      STL of every printed part, already oriented on the bed
print/inlays/   coloured dot inlays (same coordinates as their part's STL) for AMS printing
print/plates/   Bambu P1S build plates (256 x 256), one material per plate, as 3MF
print/test/     the two test prints to run before anything else
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
        ("y_plate_pad", Pos(-P.PADS_Y[0][0], -P.PADS_Y[0][1], 0) * P.y_plate_pads()[0], EYE, 2, "black", []),
        ("y_plate_plug", P.y_plate_plugs()[0], EYE, 8, "black", []),
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


if __name__ == "__main__":
    for d in ("step", "stl", "inlays", "plates", "test"):
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
    test = [("graflok_module", [drop([oriented(mesh(P.graflok_module()), FLIP)])[0]]),
            ("graflok_blade", [drop([oriented(mesh(P.graflok_blade()), FLIP)])[0]]),
            ("graflok_wheel", [drop([oriented(mesh(P.graflok_wheel()), EYE)])[0]])]
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
    (ROOT / "plates" / "PLATES.txt").write_text("\n".join(summary) + "\n")
    print("\n".join(summary))
    print((ROOT / "PRINTABILITY.txt").read_text())
