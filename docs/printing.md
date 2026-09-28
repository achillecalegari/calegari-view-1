# Printing

[Back to the project](../README.md)

Designed for a Bambu Lab P1S with AMS, but any enclosed printer with a 256 x 256 mm bed works. The largest part, the body with its L bracket, is 173 x 173 mm on the bed. Every part is already oriented and needs no supports.

## Order: calibrate, test, then print

About 50 hours of printing go into the camera. The first four hours tell you whether they will be well spent.

| Step | Plate | What it tells you |
|---|---|---|
| 1 | `plate_00a_shrink_gauge` | how much your ASA shrinks: set it in the slicer (below) before anything else |
| 2 | `plate_00b_test_1`, with the shrinkage set | the Graflok module on your RB67 back and ground glass, the metal flange in its pocket, and ten 40 mm slices of the dovetail ways to slide by hand. See [calibration, section 1](calibration.md#1-before-printing-the-body-test-prints) |
| 3 | `plate_00c_test_thread_0.12mm_layers` | the printed M65 thread in your helicoid |
| 4 | change `cad/params.py` if a test asked for it, run `export.py` again | |
| 5 | plates 01 to 06 in black, the red plate, and the shims if you will use more than one lens | the camera |

The Graflok module, blade and wheel on the test plate are real parts, printed with the final shrinkage: if they fit your back, keep them and skip `plate_05` and the blade on the red plate (a black blade works as well as a red one).

## Shrinkage: calibrate it before anything else

ASA shrinks about 0.5 to 0.7 % as it cools. Uncompensated, that is 0.5 mm on the lens board pocket and on the flange pocket: the board or the flange would not go in, and the dovetails would bind. Bambu Studio compensates it per filament, but the value must be measured on your spool.

1. Print `plate_00a_shrink_gauge` in the ASA you will use, with the settings below.
2. Let it cool for ten minutes, then measure the outer size along X (the side with the tab) and along Y with a caliper.
3. Shrinkage (%) = measured / 100 x 100. For example 99.45 mm gives 99.45 %.
4. In Bambu Studio, open the filament (three dots next to it, *Edit*), set *Shrinkage* to that value and save the profile as "ASA - Calegari View".
5. Use that profile for every part. Reprint the gauge once: it should now measure 100.0 +/- 0.1 mm.

## Material

**ASA.** It does not warp in a hot car, it resists UV, and printed on the textured plate it has a matte finish that reads like black paint. PLA is fine for fit tests, not for the camera. No fibre-filled filaments.

- Black ASA: about 750 g for the camera plus about 120 g of tests. Buy two 1 kg spools, or one if you are confident in the first print.
- Red ASA: a few grams (the Graflok blade, the board latch, the zero and infinity dots).
- White ASA: a few grams, optional (the other scale dots).

ASA gives off fumes while printing: keep the printer in a ventilated room.

## Settings

| Setting | Value |
|---|---|
| Nozzle | 0.4 mm stainless (stock) |
| Plate | textured PEI with a thin layer of glue stick |
| Chamber | door closed, top on; preheat 10 minutes with the bed at temperature |
| Temperatures | Bambu ASA profile (260 C nozzle, 100 C bed) |
| Part cooling | 20-30 % |
| Layer height | 0.16 mm; 0.12 mm for plate 06 (focus ring and adapter ring) and the thread coupon; 0.2 mm for the shims |
| Walls | 5 on the parts that close the dark chamber (body, Graflok module, Y plate, lens panel, board holder, adapter ring); 4 elsewhere |
| Top and bottom layers | 6 |
| Infill | 30 % gyroid; 100 % for the knobs, turrets, rails, gib strips, blade, wheel, latch and shims |
| Elephant foot compensation | 0.15 mm (the Bambu default): the edges that mate are chamfered as well |
| Ironing | only the body's Graflok seat (the floor of the rear recess, which prints as a top surface) |
| Seams | paint them where they do not matter: the body inside the bottom Arca pocket, the Y plate's bottom edge, the lens panel's photographer's-right edge, the rails and gibs at their ends, the knobs and the focus ring inside a flute, the handle at the inner foot |
| Supports | none |
| Brim | brim ears (corners only) on the body, the Y plate and the lens panel: ASA lifts at the corners. The plates leave 12 mm between parts for them |

Let each plate cool in the closed printer for ten minutes before opening the door: ASA warps if it cools in a draught.

## The plates

| Plate | Parts | Notes |
|---|---|---|
| `plate_00a_shrink_gauge` | 100 mm gauge | first |
| `plate_00b_test_1` | Graflok module, blade, wheel, flange pocket coupon, ten dovetail coupons | the ASA you will use |
| `plate_00c_test_thread_0.12mm_layers` | M65 thread coupon | 0.12 mm layers, like the adapter |
| `plate_01_black` | body with the L bracket | alone on the plate: about 18 hours |
| `plate_02_black` | Y plate, the four dovetail rails, the X gib strip, two knobs | |
| `plate_03_black` | lens panel, Y gib strip, top handle, both nut turrets, Graflok wheel | |
| `plate_04_black` | board holder | |
| `plate_05_black` | Graflok module | skip it if the test module fits |
| `plate_06_black_0.12mm_layers` | focus ring, adapter ring | 0.12 mm layers for the M65 thread |
| `plate_red_1` | Graflok blade, board latch | red ASA |
| `plate_07_shims_0.2mm_layers` | five lens shims, 0.4 to 1.2 mm | 0.2 mm layers; only for more than one lens ([calibration, section 4](calibration.md#4-more-lenses-one-stop-for-all-of-them)) |

Single parts, oriented and dropped on the bed, are in `print/stl`; the same parts in assembly coordinates are in `print/step` for editing. The cutting templates for the velvet and felt (V1 to V4, and two 7 mm discs) are A4 SVG files in `print/templates`: print them at 100 %.

| Part | Orientation | Why |
|---|---|---|
| body | front face down | the front comes out flat and textured; the Graflok seat is the top of the rear recess, ironed |
| Y plate | front face down | the front is the flat sliding face; the dovetail lips print at 30 degrees |
| lens panel | rear face down | the rear is the sliding face; the flange pocket is on top |
| fixed rails | base down | the base and the bearing flange come off the bed flat |
| gib rails | on their outer face | the gib pocket prints as a wall, not as an overhang |
| gib strips | upside down | the flank ends in a small flat, not a knife edge |
| turrets | as modelled | the nut slots open on the bed |
| knobs | crown down | the knurl prints as walls, the red dot is on the bed |
| focus ring | front face down | the front and the dots print crisp |
| adapter ring | flange down | the thread and the bosses print upwards |
| board holder | rear face down | |
| top handle | front face down | the engraved name plate prints on the bed; the accessory shoes print as walls |

## Coloured dots

The scales are recessed dots, 2 to 3.4 mm across and 0.6 mm deep: no text or fine ticks, which do not print well in multi-material. Red marks the zeros and infinity, white the other positions.

**With the AMS, only where it is cheap.** The dots on a top or bed face need a few colour changes: the lens panel front (focus index, depth of field and shift scale), the bottom horizontal rail (shift index), the two knobs, the handle's name plate. Their inlays are in `print/inlays/`.

1. Import the part, for example `print/stl/x_plate.stl`.
2. Right-click, *Add part*, *Load*, and pick the matching file in `print/inlays/`, for example `x_plate__red.stl`. The coordinates match: it drops into the recesses.
3. Assign the part to the red (or white) filament.

**With paint, on the walls.** The dots on side walls (the rise scale on the Y plate edge and its index on the body, the distance dots on the focus ring rim) would cost dozens of colour changes and grams of purge. Print them black and fill them with a drop of acrylic paint, wiping the excess with a damp cloth. The same works for every dot if you have no AMS.

## Printability report

`print/PRINTABILITY.txt` lists, for every part in its print orientation, the downward-facing area steeper than 45 degrees and the largest downward span. The large "spans" in the report are rings and slots whose overhang is short (the stepped light baffles, the felt grooves, the thread flanks, the flare lobes behind the lens panel bore); the longest true bridge is the board holder's latch hood, 30 mm between two rails.

## After printing

- **Flatness.** Put a steel straightedge on the body front, both faces of the Y plate and the lens panel rear. The gap under it must stay below 0.1 mm: these faces carry the light seal. Reprint a warped plate rather than shimming it.
- **Heat-set inserts.** Soldering iron with the right tip at about 230 C. See [assembly](assembly.md#five-techniques-you-will-use).
- **Threads to tap by hand.** M3 in the four radial holes of the focus ring and in the two knobs (2.5 mm holes), M3 in the six grub holes of the two gib rails, M5 in the two ball plunger holes (4.2 mm).
- **Bushing seats.** 8.1 mm horizontal holes for 8 mm bushings: horizontal holes print slightly small, so ream them with an 8 mm drill turned by hand.
- **Deburr** the dovetail flanks with a fine file if a layer sticks out, then give them a light coat of dry PTFE.
