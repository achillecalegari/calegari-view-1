"""Write render meshes + manifest for Blender (render/white.py).

python render_meshes.py --tag home [--sx 0 --sy 0 --explode 0 --section --step N]
"""
import argparse, json, pathlib
from build123d import *
from params import *
from assembly import assemble
from steps import step_of

ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="home")
ap.add_argument("--sx", type=float, default=0.0)
ap.add_argument("--sy", type=float, default=0.0)
ap.add_argument("--explode", type=float, default=0.0)
ap.add_argument("--section", action="store_true")
ap.add_argument("--step", type=int, default=0)
a = ap.parse_args()

OUT = pathlib.Path(__file__).resolve().parent.parent / "out" / f"mesh_{a.tag}"
OUT.mkdir(parents=True, exist_ok=True)
for f in OUT.glob("*.stl"):
    f.unlink()

items = assemble(a.sx, a.sy, a.explode)
if a.step:
    exploded = {i.name: i.shape for i in assemble(a.sx, a.sy, 26.0)}
    items = [i for i in items if step_of(i.name) <= a.step]
    for i in items:
        if step_of(i.name) == a.step:
            i.shape = exploded[i.name]
if a.section:
    half = Pos(-500, 0, 0) * Box(1000, 1000, 1000)
    slab = Pos(0.05, 0, 0) * Box(0.2, 1000, 1000)   # cap stands 0.15 mm proud of the cut: no z-fighting
    cut = []
    for i in items:
        try:
            h = i.shape & half
            if h.volume > 0.01:
                cut.append((i.name, h, i.mat))
                if i.mat not in ("glass", "vial") and not i.name.startswith(("rail_", "block_", "screw_", "insert_")):
                    c = i.shape & slab
                    if c.volume > 0.01:
                        cut.append((i.name + "_cap", c, "cap"))
        except Exception:
            pass
else:
    cut = [(i.name, i.shape, i.mat) for i in items]

manifest = []
for name, shape, mat in cut:
    f = OUT / f"{name}.stl"
    export_stl(shape, str(f), tolerance=0.04, angular_tolerance=0.15)
    manifest.append({"name": name, "file": str(f), "mat": mat})
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
print(f"{a.tag}: {len(manifest)} meshes")
