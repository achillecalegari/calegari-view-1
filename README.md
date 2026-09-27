# Calegari View 1

![Calegari View 1](docs/img/01_three_quarter.jpg)

A rigid 6x7 architecture camera you can print at home. Screw-driven rise and shift on two axes, helicoid focusing, Mamiya RB67 film backs, large-format wide-angle lenses on Linhof Technika boards.

**[Project page](https://achillecalegari.github.io/calegari-view-1/)** · [Shopping list](docs/bom.md) · [Printing](docs/printing.md) · [Assembly](docs/assembly.md) · [Calibration and tests](docs/calibration.md) · [Design notes](docs/design.md)

## Why I made it

I have wanted a view camera for years. The rigid kind, compact, built for architecture: you put it on the tripod, raise the lens a couple of centimetres and the verticals stay vertical, straight on the negative, with nothing to fix afterwards.

The problem is the price. A new Arca-Swiss or Silvestri costs thousands before you add a lens, and the used market is not much kinder. So I designed my own, around what I already had: a Bambu Lab P1S, the Mamiya RB67 backs you can find everywhere for little money, and a used large-format wide angle.

This repository is the whole camera: the files to print, the parametric model they come from, the shopping list with links, and step-by-step instructions. Without back and lens, the parts cost about 450 EUR, much of it in packs of screws and inserts that will outlast the camera.

## What it is

| | |
|---|---|
| Format | 6x7 (56 x 69.5 mm); the gate also clears 6x8 |
| Back | Mamiya RB67 Pro, Pro-S, Pro-SD on a Graflok-type interface; Mercury Works Graflok 23 ground glass |
| Lens | 65 mm large-format wide angle in Copal 0 (Super-Angulon 65/8, Nikkor-SW 65/4, Grandagon-N 65/4.5) on a Linhof Technika 99 x 96 board |
| Movements | rise and fall +/-25 mm, lateral shift +/-25 mm; M6 lead screws, 1 mm per turn, hard stops, zero detents |
| Focus | M65 helicoid 17-31 on a metal flange, 124 mm focus ring with a lever and an adjustable infinity stop, infinity to 0.47 m |
| Tripod | integrated L bracket with two Arca-Swiss plates: under the body (landscape) and on the side leg (portrait) |
| Handle | one top handle, bolted on; tubular spirit levels readable from behind for landscape and portrait |
| Size | 192 x 222 mm front, 161 mm deep with back and lens |
| Weight | about 1.15 kg without back and lens (605 g printed ASA, 530 g of metal); about 2 kg ready to shoot (estimate) |

The body, the two shift plates and the lens panel are flat slabs that slide face to face on MGN9 steel guides. Every plate covers the opening of the one behind it with at least 5.3 mm of contact at every shift position, with black velvet in between: that is how it stays light-tight without a bellows. The rise knob is on top; turned onto the side leg for portrait, the knob that ends up on top is again the one that raises the lens.

| | | |
|---|---|---|
| ![front](docs/img/02_front.jpg) | ![side](docs/img/03_side.jpg) | ![rear](docs/img/04_rear.jpg) |
| ![top](docs/img/05_top.jpg) | ![rise and shift](docs/img/08_shift.jpg) | ![section](docs/img/06_section.jpg) |

![exploded](docs/img/09_exploded.jpg)

## Status

The design is complete and checked in software, not yet proven in the hand.

- `cad/check.py`: no interference between any of the 145 components, at home and at the four shift extremes, with the Graflok blade and the board latch both closed and open, and against the envelope of a 65 mm Arca clamp in landscape and portrait. Every printed part is a single solid.
- `cad/seal_check.py`: every sliding light seal is at least 5.3 mm wide at every shift position.
- `print/PRINTABILITY.txt`: overhangs and bridges of every part in its print orientation; the longest bridge is 21 mm.
- Before the first print the design was reviewed area by area: mechanics and printing, light-tightness, optics and registration, the RB67 interface, field use. What changed as a result is in the [design notes](docs/design.md).

What only the first physical build can prove is listed in [calibration and tests](docs/calibration.md). The most important is the first: the fit of the Graflok module on a real RB67 back. It is a separate 1-hour print for exactly that reason, and it comes before the body.

## The model

Everything is generated from Python with [build123d](https://github.com/gumyr/build123d). All dimensions live in `cad/params.py`: change a value (a lens with a different flange distance, a helicoid that turns a different angle, a tighter or looser fit) and rebuild the whole camera.

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cd cad
../.venv/bin/python check.py          # interference, single-solid and clamp checks
../.venv/bin/python seal_check.py     # light-seal widths
../.venv/bin/python export.py         # STEP, oriented STL, AMS inlays, P1S plates, test prints
../render/gen_all.sh                  # every image in docs/img (needs Blender)
```

The STEP files in `print/step` open in Fusion, FreeCAD or any CAD.

## Credits

The RB67 interface was measured from two open designs that take the same backs: [Super-67](https://github.com/DamienHazard/Super-67) by Damien Hazard, and the [RB67 pinhole body](https://www.thingiverse.com/thing:7270507) by bogdanbogvzyan, tested with Pro-S and Pro-SD backs. Lens data come from the Schneider, Nikon, Rodenstock and Fujinon catalogues and the Mercury lens database; Graflok 23 figures from Mercury Camera's guide.

## License

[CC BY-NC-SA 4.0](LICENSE). Build it, change it, share it with credit; do not sell it.
