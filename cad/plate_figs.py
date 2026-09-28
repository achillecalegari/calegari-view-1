"""Figures of the print plates for docs/printing.md, read back from the 3MF files export.py wrote.

python plate_figs.py     writes out/figs/p_<plate>/manifest.json and points.json (doc "print")
render/figures.sh p_<plate> ... renders and annotates them like every other figure.

The bed is drawn as a 256 x 256 mm plate; each part is labelled with its name.
"""
import json, pathlib
import numpy as np
import trimesh

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLATES = ROOT / "print" / "plates"
OUT = ROOT / "out" / "figs"
BED = 256.0
VIEW = (0.0, -0.55, 1.0)          # Blender: from the front edge of the bed, looking down

NAMES = {
    "shrink_gauge_100mm": "100 mm gauge", "rotator": "Rotator", "graflok_blade": "Graflok blade",
    "graflok_wheel": "Wheel", "flange_pocket_coupon": "Flange pocket coupon", "m65_male_coupon": "M65 thread coupon",
    "body": "Body", "bezel": "Rear frame", "y_plate": "Y plate", "x_plate": "Lens panel", "top_handle": "Top handle",
    "y_turret": "Rise nut turret", "x_turret": "Shift nut turret", "way_y_fixed": "Vertical rail",
    "way_y_gib": "Vertical gib rail", "way_x_fixed": "Horizontal rail", "way_x_gib": "Horizontal gib rail",
    "gib_x": "X gib strip", "gib_y": "Y gib strip", "knob": "Knob", "board_holder": "Board holder",
    "focus_ring": "Focus ring", "adapter_ring": "Adapter ring", "holder_latch": "Board latch",
}
TITLES = {
    "plate_00a_shrink_gauge": "Plate 00a: shrinkage gauge",
    "plate_00b_test_1": "Plate 00b, 1: rotator, blade and dovetail coupons",
    "plate_00b_test_2": "Plate 00b, 2: flange pocket, lip coupons, wheel",
    "plate_00c_test_thread_0.12mm_layers": "Plate 00c: M65 thread coupon, 0.12 mm layers",
    "plate_01_black": "Plate 01: body",
    "plate_02_black": "Plate 02: rear frame, rails, X gib strip, shift turret, wheel",
    "plate_03_black": "Plate 03: Y plate, Y gib strip, handle, knobs, rise turret",
    "plate_04_black": "Plate 04: lens panel",
    "plate_05_black": "Plate 05: rotator",
    "plate_06_black": "Plate 06: board holder",
    "plate_07_black_0.12mm_layers": "Plate 07: focus ring and adapter, 0.12 mm layers",
    "plate_red_1": "Red plate: blade and latch",
    "plate_07_shims_0.2mm_layers": "Shims: five thicknesses, 0.2 mm layers",
}


INLAYS = {}
for f_ in (ROOT / "print" / "inlays").glob("*__*.stl"):
    part_, colour_ = f_.stem.split("__")
    INLAYS.setdefault(part_, []).append((colour_, abs(trimesh.load(str(f_)).volume)))


def to_model(pts):
    """Bed coordinates (x right, y back, z up) -> model (X, Y up, Z toward the viewer)."""
    p = np.asarray(pts, dtype=float)
    return np.column_stack([p[:, 0] - BED / 2, p[:, 2], -(p[:, 1] - BED / 2)])


def label_for(node):
    base = node.split("_inlay")[0]
    for key in sorted(NAMES, key=len, reverse=True):
        if base.startswith(key):
            return NAMES[key]
    if base.startswith("coupon_"):
        return "Dovetail coupons"
    if base.startswith("copal0_shim_"):
        return base.replace("copal0_shim_", "Shim ")
    return base


def build(plate):
    scene = trimesh.load(str(PLATES / f"{plate}.3mf"), force="scene")
    name = "p_" + plate.replace(".", "_")
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    manifest, labels, seen = [], [], {}
    red = plate.startswith("plate_red")
    for node in scene.graph.nodes_geometry:
        T, gname = scene.graph[node]
        m = scene.geometry[gname].copy()
        m.apply_transform(T)
        m.vertices = to_model(m.vertices)
        m.invert()                                    # the axis swap mirrors the mesh: keep normals outward
        f = d / f"{node}.stl"
        m.export(str(f))
        inlay = "_inlay" in node
        mat = "red" if red else "body_black"
        if inlay:                                     # match the inlay to print/inlays/<part>__<colour>.stl by volume
            part = node.split("_inlay")[0]
            best = min(INLAYS.get(part, [("white", 0.0)]), key=lambda cv: abs(cv[1] - abs(m.volume)))
            mat = "red" if best[0] == "red" else "white_ink"
        manifest.append({"name": node, "file": str(f), "mat": mat})
        if not inlay:
            text = label_for(node)
            b = m.bounds
            top = [(b[0][0] + b[1][0]) / 2, b[1][1], (b[0][2] + b[1][2]) / 2]
            if text in seen:
                seen[text]["points"].append(top)
                continue
            seen[text] = {"text": text, "points": [top]}
            labels.append(seen[text])
    for lab in labels:
        if len(lab["points"]) > 1 and not lab["text"].endswith("s"):
            lab["text"] += "s"
    bed = trimesh.creation.box([BED, 1.0, BED])
    bed.apply_translation([0, -0.5, 0])
    f = d / "bed.stl"
    bed.export(str(f))
    manifest.insert(0, {"name": "bed", "file": str(f), "mat": "cap"})
    json.dump(manifest, open(d / "manifest.json", "w"), indent=1)
    json.dump({"title": TITLES.get(plate, plate), "view": list(VIEW), "doc": "print", "labels": labels,
               "guides": [], "lines": [], "dist": 3.6, "aspect": 0.75, "expo": -2.8}, open(d / "points.json", "w"), indent=1)
    return name


if __name__ == "__main__":
    names = [build(p.stem) for p in sorted(PLATES.glob("*.3mf"))]
    print(" ".join(names))
