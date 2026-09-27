"""White-studio product render (transparent film, composited on pure white by compose.py).

blender -b -P white.py -- <manifest.json> <out.png> <view> [samples] [res_x]
Env: EXPO (exposure), DIST (camera distance factor), LENS (mm), FSTOP, ASPECT, FLAT (flat shading).
Views: w_34, w_front, w_side, w_rear, w_top, w_section, w_section34, explode34.
"""
import bpy, json, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
manifest, out, view = argv[0], argv[1], argv[2]
samples = int(argv[3]) if len(argv) > 3 else 96
res_x = int(argv[4]) if len(argv) > 4 else 1600

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mat(name, color, rough, metal=0.0, spec=0.5, transm=0.0, bump=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular"].default_value = spec
    b.inputs["Transmission"].default_value = transm
    b.inputs["Clearcoat"].default_value = coat
    if transm:
        b.inputs["IOR"].default_value = 1.52
    if bump:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 900.0
        tex.inputs["Detail"].default_value = 2.0
        bn = nt.nodes.new("ShaderNodeBump")
        bn.inputs["Strength"].default_value = bump
        bn.inputs["Distance"].default_value = 0.0002
        nt.links.new(tex.outputs["Fac"], bn.inputs["Height"])
        nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m


MATS = {
    "plastic_body": mat("plastic_body", (0.018, 0.018, 0.02), 0.62, bump=0.25),
    "plastic_panel": mat("plastic_panel", (0.05, 0.05, 0.052), 0.5, bump=0.2),
    "plastic_knob": mat("plastic_knob", (0.02, 0.02, 0.02), 0.45, bump=0.15),
    "steel": mat("steel", (0.62, 0.62, 0.6), 0.28, metal=1.0),
    "chrome": mat("chrome", (0.8, 0.8, 0.8), 0.08, metal=1.0),
    "alu_black": mat("alu_black", (0.03, 0.03, 0.032), 0.32, metal=0.7),
    "lens_black": mat("lens_black", (0.025, 0.025, 0.025), 0.38, metal=0.3),
    "glass": mat("glass", (0.85, 0.9, 0.95), 0.0, transm=1.0, coat=0.5),
    "leather": mat("leather", (0.025, 0.024, 0.024), 0.75, bump=0.8),
    "white": mat("white", (0.80, 0.78, 0.73), 0.55, bump=0.18),
    "anthracite": mat("anthracite", (0.042, 0.044, 0.047), 0.5, bump=0.15),
    "level": mat("level", (0.05, 0.09, 0.06), 0.05, coat=1.0),
    "body_black": mat("body_black", (0.022, 0.022, 0.024), 0.42, spec=0.55, bump=0.12),
    "red": mat("red", (0.55, 0.012, 0.01), 0.32, coat=0.3),
    "black_steel": mat("black_steel", (0.03, 0.03, 0.03), 0.35, metal=1.0),
    "brass": mat("brass", (0.85, 0.62, 0.3), 0.3, metal=1.0),
    "bronze": mat("bronze", (0.7, 0.45, 0.25), 0.45, metal=1.0),
    "red_seal": mat("red_seal", (0.5, 0.05, 0.03), 0.6),
    "glass_red": mat("glass_red", (0.6, 0.05, 0.02), 0.1, coat=1.0),
    "ink_dark": mat("ink_dark", (0.08, 0.08, 0.08), 0.6),
    "ink_light": mat("ink_light", (0.85, 0.85, 0.82), 0.5),
    "rubber": mat("rubber", (0.02, 0.02, 0.02), 0.8),
    # light seals: grey in the assembly maps (SEALGREY=1) so they show, black in product shots
    "felt": mat("felt", (0.3, 0.3, 0.32) if __import__("os").environ.get("SEALGREY") else (0.012, 0.012, 0.013), 1.0, spec=0.2, bump=0.6),
    "velvet": mat("velvet", (0.3, 0.3, 0.32) if __import__("os").environ.get("SEALGREY") else (0.012, 0.012, 0.013), 1.0, spec=0.2, bump=0.6),
    "vial": mat("vial", (0.55, 0.75, 0.45), 0.05, transm=0.7, coat=1.0),
    "white_ink": mat("white_ink", (0.85, 0.85, 0.83), 0.5),
    "clamp": mat("clamp", (0.3, 0.3, 0.3), 0.5),
    "cap": mat("cap", (0.62, 0.62, 0.6), 0.7),
    "ink": mat("ink", (0.85, 0.85, 0.82), 0.5),
    "accent": mat("accent", (0.95, 0.30, 0.02), 0.45),
}

root = bpy.data.objects.new("root", None)
sc.collection.objects.link(root)
root.rotation_euler = (math.radians(90), 0, 0)   # model Y -> Blender Z, model Z (toward the subject) -> Blender -Y
root.scale = (0.001, 0.001, 0.001)

for item in json.load(open(manifest)):
    bpy.ops.import_mesh.stl(filepath=item["file"])
    o = bpy.context.selected_objects[0]
    o.name = item["name"]
    o.data.materials.append(MATS.get(item["mat"], MATS["plastic_body"]))
    o.parent = root
    if __import__("os").environ.get("FLAT"):
        bpy.ops.object.shade_flat()
    else:
        bpy.ops.object.shade_smooth()
        o.data.use_auto_smooth = True
        o.data.auto_smooth_angle = math.radians(30)
        wn = o.modifiers.new("wn", "WEIGHTED_NORMAL")
        wn.mode = "FACE_AREA"
        wn.keep_sharp = True

bpy.context.view_layer.update()
# scene centre and size
pts = []
for o in root.children:
    pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
ctr = (mn + mx) / 2
size = (mx - mn).length

# --- white studio: no floor, no shadows; transparent film composited on white afterwards ---
sc.render.film_transparent = True

def area(name, loc, energy, sx, sy_=None, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA")
    l.energy = energy
    if sy_ is None:
        l.shape = "SQUARE"; l.size = sx
    else:
        l.shape = "RECTANGLE"; l.size = sx; l.size_y = sy_
    l.color = color
    o = bpy.data.objects.new(name, l)
    sc.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (ctr - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o

S = size
area("top", (ctr.x, ctr.y - 0.2 * S, ctr.z + 2.2 * S), 55, 2.2 * S)
area("left", (ctr.x - 1.8 * S, ctr.y - 0.8 * S, ctr.z + 0.6 * S), 30, 1.6 * S)
area("right", (ctr.x + 1.8 * S, ctr.y - 0.6 * S, ctr.z + 0.5 * S), 22, 1.6 * S)
area("rim", (ctr.x + 0.6 * S, ctr.y + 1.6 * S, ctr.z + 0.9 * S), 30, 0.2 * S, 1.8 * S)

w = sc.world = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = float(__import__("os").environ.get("WORLD", "0.25"))

# camera
VIEWS = {
    "front34": (-0.55, -1.0, 0.38),
    "hero": (-0.62, -1.0, 0.16),
    "hero_r": (0.7, -1.0, 0.2),
    "rear_hero": (0.75, 1.0, 0.28),
    "detail": (-0.9, -0.35, 0.75),
    "w_front": (0.0, -1.0, 0.0),
    "w_side": (-1.0, 0.0, 0.0),
    "w_34": (-0.62, -1.0, 0.22),
    "w_rear": (0.62, 1.0, 0.22),
    "w_top": (0.0, -0.08, 1.0),
    "w_section": (1.0, 0.0, 0.0),
    "w_section34": (1.0, -0.55, 0.3),
    "focus": (-0.35, -0.75, 0.95),
    "profile": (-1.0, -0.12, 0.1),
    "rear34": (0.6, 1.0, 0.35),
    "front": (0.0, -1.0, 0.05),
    "side": (-1.0, 0.0, 0.05),
    "top": (-0.25, -0.35, 1.0),
    "left34": (0.75, -0.8, 0.3),
    "explode34": (-1.0, -0.62, 0.42),
}
cam = bpy.data.cameras.new("cam")
cam.lens = float(__import__("os").environ.get("LENS", "135"))
co = bpy.data.objects.new("cam", cam)
sc.collection.objects.link(co)
dirv = Vector(VIEWS[view] if view in VIEWS else [float(v) for v in view.split(",")]).normalized()
dist = float(__import__("os").environ.get("DIST", "2.55"))
co.location = ctr + dirv * size * dist
zoom = __import__("os").environ.get("AIM")
if zoom:
    ctr = ctr + Vector([float(v) * 0.001 for v in zoom.split(",")])
co.rotation_euler = (ctr - co.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = co
cam.dof.use_dof = True
cam.dof.focus_distance = (ctr - co.location).length
cam.dof.aperture_fstop = float(__import__("os").environ.get("FSTOP", "22"))

sc.render.engine = "CYCLES"
sc.cycles.samples = samples
sc.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    sc.cycles.device = "GPU" if len(argv) < 6 else "CPU"
except Exception:
    pass
sc.render.resolution_x = res_x
sc.render.resolution_y = int(res_x * float(__import__("os").environ.get("ASPECT", "0.75")))
sc.view_settings.view_transform = "Filmic"
sc.view_settings.look = "Medium High Contrast"
sc.view_settings.exposure = float(__import__("os").environ.get("EXPO", "-3.0"))
sc.render.filepath = out
pts_file = __import__("os").environ.get("PTS")
if pts_file:                                   # project callout points to pixels (render/letter.py)
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    data = json.load(open(pts_file))
    rx, ry = sc.render.resolution_x, sc.render.resolution_y
    for lab in data["labels"]:
        px = []
        for p in lab["points"]:
            v = world_to_camera_view(sc, co, root.matrix_world @ Vector(p))
            px.append([v.x * rx, (1 - v.y) * ry])
        lab["px"] = px
    json.dump(data, open(out.rsplit(".", 1)[0] + ".json", "w"), indent=1)
bpy.ops.render.render(write_still=True)
