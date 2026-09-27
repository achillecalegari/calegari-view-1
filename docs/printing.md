# Printing

[Back to the project](../README.md)

Designed for a Bambu Lab P1S with AMS, but any enclosed printer with a 256 x 256 mm bed works. The largest part, the body with its L bracket, is 170 x 170 mm on the bed.

## Order: test first

Print and fit the risky interfaces before spending half a kilo of ASA.

| Step | Plate | What you check |
|---|---|---|
| 1 | `print/plates/plate_00_test_1.3mf` (PLA is fine) | Graflok module, blade and wheel on your RB67 back and ground glass; the M65 male coupon in your helicoid; the metal flange in its pocket. See [calibration, section 1](calibration.md#1-before-printing-the-body-test-prints). |
| 2 | adjust `cad/params.py` if needed, re-run `export.py` | |
| 3 | plates 01 to 06 in black ASA, then the red plate | |

## Material

**ASA.** It does not warp in a hot car, it resists UV and it has a matte finish that reads like anodized aluminium in black. PLA is fine for fit tests, not for the camera. No fibre-filled filaments: they need a hardened nozzle and give nothing here.

- Black ASA: about 700 g for the whole camera, purge and brims included (a 1 kg spool is enough).
- Red ASA: a few grams (Graflok blade, board latch, zero and infinity dots).
- White ASA: a few grams, optional (the other scale dots).

## Settings

| Setting | Value |
|---|---|
| Nozzle | 0.4 mm stainless (stock) |
| Plate | textured PEI with a thin layer of glue stick |
| Chamber | door closed, top on; preheat 10 minutes with the bed at temperature |
| Temperatures | Bambu ASA profile (260 C nozzle, 100 C bed) |
| Part cooling | 20-30 % |
| Layer height | 0.16 mm; 0.12 mm for `adapter_ring` (external M65 thread) |
| Walls | 5 on the parts that close the dark chamber (body, Graflok module, Y plate, lens panel, board holder, adapter ring); 4 elsewhere |
| Top and bottom layers | 6 |
| Infill | 30 % gyroid; 100 % for knobs, turret, blade, wheel, latch, pads and plugs |
| Ironing | top surfaces only, on the body (it becomes the back's seat) and the lens panel front |
| Supports | none |
| Brim | 5 mm on the body, the Y plate and the lens panel (ASA lifts at the corners) |

Five walls give about 2 mm of solid ASA around every opening of the light path, so the seal never depends on infill.

## The plates

All parts are already oriented. Open the 3MF in Bambu Studio, check the settings above, slice and print.

| Plate | Parts | Material |
|---|---|---|
| `plate_00_test_1` | Graflok module, blade, wheel, M65 male coupon, flange pocket coupon | PLA or ASA |
| `plate_01_black` | body with L bracket, top handle, 2 knobs, turret, wheel, 2 pads, 8 plugs | ASA black |
| `plate_02_black` | Y plate | ASA black |
| `plate_03_black` | lens panel (X plate) | ASA black |
| `plate_04_black` | focus ring, adapter ring | ASA black |
| `plate_05_black` | board holder | ASA black |
| `plate_06_black` | Graflok module | ASA black |
| `plate_red_1` | Graflok blade, board latch | ASA red |

Single parts, oriented and dropped on the bed, are in `print/stl`; the same parts in assembly coordinates are in `print/step` for editing.

| Part | Orientation | Notes |
|---|---|---|
| body (with the L bracket) | front face down | the Graflok seat prints as the top surface of the recess: iron it; the name and the red dot are on the bed side, sharp |
| Graflok module | seat face down | |
| Graflok blade | countersunk slots up | 100 % infill |
| Y plate | front face down | the nut turret points up |
| lens panel | rear face down | the metal flange pocket is on top |
| turret | top face down | |
| focus ring | front face down | the lever and the infinity stop tab point up |
| adapter ring | flange down | 0.12 mm layers for the thread |
| board holder | rear face down | |
| board latch | flat | red |
| knobs | base down | |
| top handle | flat on its side | layers follow the loop: stronger |

## Coloured dots with the AMS

The scales are recessed dots, 2 to 3.4 mm across and 0.6 mm deep: no text or fine ticks, which do not print well in multi-material. Red marks the zeros and infinity, white the other positions.

1. Import the part, for example `print/stl/x_plate.stl`.
2. Right-click, *Add part*, *Load*, and pick the matching file in `print/inlays/`, for example `x_plate__red.stl`. The coordinates match: it drops into the recesses.
3. Assign the part to the red (or white) filament.
4. Repeat for every file of that part in `print/inlays/`.

Without an AMS, print everything black and fill the dots with a drop of acrylic paint, wiping the excess with a damp cloth.

## Printability report

`print/PRINTABILITY.txt` lists, for every part in its print orientation, the downward-facing area steeper than 45 degrees and the largest downward span. The longest real bridge is the ceiling of the guide channels, 21 mm; the other large "spans" in the report are rings (the stepped light baffles, the felt groove, the thread flanks), whose overhang is 1.4 to 4.5 mm wide.

## After printing

- **Flatness.** Put a steel straightedge on the body front, both faces of the Y plate and the lens panel rear. The gap under the straightedge must stay below 0.1 mm: these faces are the light seal. Reprint a warped plate rather than shimming it.
- **Heat-set inserts.** Soldering iron with an insert tip at about 230 C for ASA. Press straight and stop 0.2 mm below the surface; check the face stays flat afterwards.
- **Threads to tap by hand.** M3 in the four grub holes of the focus ring (2.5 mm holes), M5 in the two ball plunger holes (4.2 mm holes).
- **Bushing seats.** 10.05 mm holes for 10 mm bushings: a light press fit. If they are tight, ream with a 10 mm drill turned by hand.
- **Deburr** the guide channels: the carriages must not touch the channel walls.
