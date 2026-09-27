"""PNG con alpha -> JPG su bianco pieno (per la documentazione)."""
import sys, pathlib
from PIL import Image
out_dir = pathlib.Path(sys.argv[1])
out_dir.mkdir(parents=True, exist_ok=True)
for path in sys.argv[2:]:
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    dst = out_dir / (pathlib.Path(path).stem + ".jpg")
    bg.convert("RGB").save(dst, quality=88, optimize=True, progressive=True)
    print(dst.name, dst.stat().st_size // 1024, "KB")
