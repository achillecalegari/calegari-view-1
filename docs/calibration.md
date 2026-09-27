# Calibration and tests

[Back to the project](../README.md)

The model is checked in software (interference, light seals, clamp clearance, printability). What follows can only be checked with the real parts in your hands. Do it in this order: the first section decides whether you print the body as it is or change a few numbers first.

## 1. Before printing the body: test prints

Print `print/plates/plate_00_test_1.3mf` (PLA is fine, about 2 hours).

### Graflok module on your RB67 back

The interface was measured from two open designs that take RB67 backs, one of them tested with Pro-S and Pro-SD. Your back and your ground glass have the last word.

1. Lay the module seat face down on a sheet of glass: the glass plays the body's seat.
2. Fit the blade and the wheel (screws into the plastic are fine for the test).
3. **Mount the back.** Hook the back's bottom lip under the bottom rail, swing the back down, and check four things:
   - the nose touches the glass all round, and nothing else holds the back off it (feeler gauge);
   - the top and bottom lips of the back fall into the reliefs of the module;
   - sliding the blade up puts both tongues into the back's top slots, and the wheel locks it;
   - the back does not move when you push on it.
4. **Dark slide.** With the back locked, pull the dark slide toward the photographer's right. It must come out: this also proves that the bottom rail releases the Pro-S interlock.
5. **Ground glass.** Repeat with the Mercury ground glass.

If something does not fit, measure the back and change the numbers in `cad/params.py`, the Graflok section: `POCKET_*`, `LIP_RELIEF_*`, `SLIDE_RELIEF_*`, and `BLADE_*` / `TONGUE_X` in `parts.py`. Then re-run `check.py` and `export.py`. The measurements that matter, with the nose face as Z = 0 and the film-frame centre as X/Y = 0:

| # | What | Why |
|---|---|---|
| M1 | nose: X to the closed end and to the dark-slide end, Y top and bottom, protrusion over the rim | pocket |
| M2 | light-trap ridge: X position, width, height | groove in the seat |
| M3 | top and bottom lips: inner and outer Y, X extent, gap from the nose face | lip reliefs |
| M4 | Graflok slots in the top lip: X centres, width, depth, walls from the nose face | blade tongues |
| M5 | dark-slide handle: hook Y band, protrusion ahead of the nose face, handle X and thickness, full slide length | dark-slide relief |
| M6 | dark-slide safety catch (Pro-S, Pro-SD): X, Y, diameter, protrusion, release depth | bottom rail |
| M7 | wind-stop release receptor: X, Y, diameter, stroke | future coupling |
| M8 | film advance lever: hub position, lever length, height above the top, swing | top handle clearance |
| M9 | overall outline including the lever | |
| M10 | same as M5 to M7 for a Pro-SD | |
| M11 | Mercury ground glass: outline, nose, ridge, slots | |
| M12 | nose face to the film rails (Graflok standard: 4.75 mm) | registration |

### M65 coupons

- **Male coupon.** It must screw into the front of your helicoid by hand, with no play and no binding. If it is tight, lower `M65` by 0.1 in `params.py`; if it wobbles, raise it.
- **Flange pocket coupon.** The RafCamera flange must drop in flush with the face, with its four M3 holes on the four countersinks.

### Helicoid

Measure three things on your helicoid:

1. **Rotation for the full 17 to 31 mm travel.** Chinese M65 helicoids turn anywhere from about 167 to 313 degrees. Put the value in `HELI_ROT` and the turning direction in `FOCUS_DIR`, then re-export the focus ring: the distance dots and the depth-of-field dots move with it.
2. **Length of the rear male thread.** It must be 5 mm or less, or it will not seat in the metal flange.
3. **Front rotation.** The front must not rotate when you turn the focusing ring.

## 2. After assembly

### Light test

1. In a dark room, with the lens board removed, shine a strong torch into the body through the lens panel bore, and look from behind through the gate, eyes adapted for two minutes.
2. Then do the opposite: the torch outside, pointed at every edge and slot, a paper sheet behind the gate.
3. Repeat at the five shift positions: centre, and the four combinations of +25/-25 lateral with +25/-8 rise.
4. **Film test.** Load a roll, cap the lens and leave the camera in the sun for ten minutes at maximum shift, then develop. It must come out clear.

### Infinity

1. Mount the ground glass.
2. Open the lens and focus on something at least 200 m away, with a 4x to 6x loupe on the glass centre.
3. Turn the focus ring on the helicoid (grub screws loose) until its large red dot is on the red index of the lens panel, then tighten the four grub screws.
4. Turn the stop screw in the ring's rear tab until it touches the stop pin. That is infinity for this lens.
5. With another lens, readjust only the stop screw.

**If infinity cannot be reached** (the helicoid bottoms out first), reprint the adapter ring with a thinner flange: `ADAPTER_T` in `params.py`, 0.5 mm less gives 0.5 mm more travel. This is what the adapter ring is for.

### Ground glass against film

The ground glass and the film must lie in the same plane within 0.05 mm.

1. With a depth gauge, measure from the rear face of the Graflok module to the ground surface of the glass at five points (centre and corners).
2. Measure from the same face to the film rails of the back, at the same five points.
3. If the two differ, the focus scale is off by the difference. Shim the glass (Mercury sells RS-0, RS-20 and RS-30 depths) rather than the back.

### Lens panel parallelism

1. With a depth gauge, measure from the rear face of the Graflok module to the front of the lens board, at the four corners of the board.
2. Repeat at the nine shift positions, and with the camera on each Arca plate.
3. The four readings must agree within 0.1 mm.

If one corner is consistently off, check the plates for flatness (straightedge) and the carriages for play before anything else.

### First roll

1. Photograph a flat brick wall at f/8, square to the camera, at centre and at maximum rise. Check the four corners with a loupe.
2. Photograph a ruler at 45 degrees: the sharpest mark must be the one you focused on.

## 3. Limits worth knowing

- **Super-Angulon 65/8 (153.5 mm image circle).** Full rise alone and full lateral shift alone are fine. Combined, keep each axis under about 22 mm or the corner falls outside the image circle. The Nikkor-SW 65/4 and Grandagon-N 65/4.5 (170 mm) cover 25 + 25.
- **Portrait on the side handle.** The clamp must be 65 mm or smaller: the model checks a 65 x 65 mm clamp.
- **Fall.** Limited to 8 mm, so the Y plate never reaches the jaws of the bottom clamp.
