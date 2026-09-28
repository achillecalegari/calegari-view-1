# Design notes

[Back to the project](../README.md)

## Architecture

The camera is a stack of flat slabs on the optical axis, from the film forward:

1. **Graflok module** (printed, separate): the back's nose pocket, the fixed bottom rail that hooks the back and releases the Pro-S dark-slide interlock, and the red clamp blade with two tongues.
2. **Body** (printed, one piece): the seat for the back, the stepped gate, the two vertical dovetail rails, the rise screw, and an L bracket (bottom plinth and side leg) carrying the two Arca plates.
3. **Y plate** (printed): rises and falls between the vertical rails, carries the two horizontal dovetail rails and the shift screw.
4. **Lens panel** (printed): shifts left and right, carries a metal M65 flange.
5. **Optics on the flange:** the helicoid, the printed adapter ring, the Technika board holder and the lens.

The light seal is the flatness of these faces. Each plate covers the opening of the one behind it, and the band of black velvet between them is at least 4.6 mm wide at every shift position (`cad/seal_check.py`, swept every 5 mm). The thin flanges of the dovetail rails set the 0.8 mm gap and the velvet is compressed in it, so the velvet never carries load.

## Choices and why

| Choice | Why |
|---|---|
| 6x7 with RB67 backs | backs are common and cheap; the Graflok-type interface is simple enough to print; the gate also clears 6x8 |
| 65 mm lenses in Copal 0 | 33 mm equivalent on 6x7, cheap used, image circles of 153 to 170 mm for large shifts |
| Technika 99 x 96 boards | the most common board: lenses often come mounted on one, and it swaps with 4x5 field cameras |
| One board per lens, spring latch | a lens changes in ten seconds without tools; the red latch slides in a printed dovetail, held by two screws from the back, so nothing shows on the front; printed shims under the shutter (0.4 to 1.2 mm) let every lens reach infinity on the same stop |
| Metal M65 flange on the lens panel | a printed thread carrying the lens and the focusing torque was the weakest point of the first design |
| Printed adapter ring as the calibration part | if infinity is out of reach, reprint a thinner 20-minute part instead of a plate |
| Printed dovetail ways with a gib | the way view cameras have always done it: nothing to buy, nothing to align, play taken up by three grub screws. The rails print as separate parts, so the sliding flanks come from the printer's perimeters, not from stair-stepped layers; test coupons prove the fit on your printer before the big parts |
| Front standard assembled on the bench, then slid in from the top | the Y plate's front overhangs the vertical rails (the shift screw passes over them), so it goes in like a drawer; the rise nut turret is screwed on afterwards through the plate |
| M6 threaded rod and brass nut, 1 mm per turn | fine control, self-locking under gravity, parts from any hardware shop; the nut floats 0.5 mm so the rod never binds. The rise rod ends in a plain M6 nut and washer, fixed on the bench and hidden under the camera. The shift rod shows nothing on the left: it ends in a blind seat, and a washer and a nut locked inside the channel hold it against the knob side. No hardware in sight on the front or the sides |
| All small hardware in M3 | one insert size (M3 x 3 x 5) for every insert, socket heads in four lengths, countersunk in two (only where a head must sit flush: the flange, the Graflok blade and the thin vertical rails), one grub size. Four assortments and an M6 set buy the whole camera; three hex keys build it |
| Shift nut turret keyed into the lens panel | the hard stops push on the pocket walls, not on the glue |
| O-ring drag instead of lock wheels | lock wheels moved the composition as you tightened them; constant drag holds the plate and never shifts it |
| Ball-plunger zero detents | you feel zero without looking; the plungers sit in through holes, so they are set from behind and then sealed |
| Rise and fall +/-25, the same as lateral shift | the base of the L bracket is 25 mm tall so that at full fall the Y plate stays 4 mm above a clamp's jaws; the two scales read the same way |
| L bracket printed with the body, side leg on the photographer's left | one continuous outline with the body's R9 corners, no joints to loosen; the RB67 dark slide comes out on the right, so nothing protrudes there; in portrait the shifted lens panel stays clear of the clamp |
| One top handle, bolted, as deep as the body | feet flared into the body, nothing overhangs the film back's advance lever; room on top for two ISO 518 accessory shoes and a bull's-eye level, and on its front for the engraved name |
| Bull's-eye levels | a tubular vial reads one direction only; the one that keeps verticals vertical is front to back |
| Hidden infinity stop | a pin on the lens panel runs in a groove under the focus ring and meets one solid block at infinity; you set it by turning the ring on the helicoid, no adjusting screw |
| Recessed dot scales, red only for zeros, infinity and release controls | print cleanly in multi-material; red means "this is the reference" or "this lets go" |

## Design reviews

The design went through three rounds of independent review before the first print: mechanics and tolerances, light and optics, printability, and assembly and use by someone who has never built a camera. Each finding was measured in the CAD, fixed, and checked again. The main ones:

| Area | Found | Fix |
|---|---|---|
| RB67 interface | the dark slide could not come out; the latch bars had no tongues; nothing released the Pro-S interlock | Graflok module rebuilt on the scheme of a body tested with Pro-S and Pro-SD, dark-slide passage open to the right |
| Mechanics | industrial linear guides were overkill and made the build long | printed dovetail ways with gibs, test coupons |
| Assembly | the Y plate could not go on once the rails were fixed; the rod nuts could not be tightened inside the camera | the plate slides in from the top; the rise end nut is fixed on the bench, the shift thrust nut before the lens panel goes on |
| Assembly | the board holder's screws were unreachable under the focus ring | they now go in from the front, under the board, into eight inserts in the adapter |
| Mechanics | the Graflok wheel did not turn its screw; screws too long in six places; the detent balls never touched the plate | screw head glued in the wheel; every screw length checked against its hole; balls 1.0 mm proud with a 0.3 mm seat |
| Mechanics | the shift hard stop loaded a glued joint | the turret sits in a 2.5 mm pocket |
| Optics | the lens panel bore cut the corner at large combined shifts | flare lobes on the diagonals; single movements now reach 25 mm clean down to about 0.9 m |
| Light | screw holes and a detent hole could carry light around the velvet | velvet discs over the turret screws, the detent moved outside both velvets, black paint in the flange's unused holes, light-trap grooves in the seat and the flange pocket |
| Printing | knife edges, a hood printed in the air, thin walls under inserts | chamfers and lands on every bed edge that mates, a hood bridging rail to rail, thicker walls |
| Use | tubular levels could not show the tilt that bends verticals | two bull's-eye levels |

## Automated checks

| Script | What it proves |
|---|---|
| `cad/check.py` | every printed part is one solid; no two parts intersect (threshold 0.3 mm3) at home and at the four shift extremes, with the blade and the board latch closed and open, including every screw against the bottom of its hole; the 65 mm clamp envelopes in landscape and portrait touch nothing that moves |
| `cad/seal_check.py` | minimum width of the velvet band around the light path at both sliding interfaces, at every shift position in 5 mm steps |
| `cad/optics_check.py` | rays from the lens pupil to the four corners of the frame, through every part, at the shift, aperture and pupil positions listed in the script |
| `cad/export.py` | `print/PRINTABILITY.txt`: overhangs and bridges of every part in its print orientation |

## Open points

- **RB67 interface.** It is derived from reference designs and has not yet been fitted on a real back. The RB67 model used by the checks has no lips or slots, so the back-to-module fit is not part of the automated check: it is test print #1 ([calibration](calibration.md#1-before-printing-the-body-test-prints)).
- **Wind-stop coupling.** Not implemented: after each frame, press the back's own release lever, as on the Mamiya Press. A plunger at the top-left corner of the module is the planned v2 feature (M7 in the calibration list).
- **Lens tilt.** The board can be squared in rotation through the holder's arc slots, but it cannot be adjusted in tilt. Parallelism relies on flat prints: check it with the procedure in calibration.
- **Focus scale.** It is correct only once `HELI_ROT` and `FOCUS_DIR` are measured on your helicoid.
