# Design notes

[Back to the project](../README.md)

## Architecture

The camera is a stack of flat slabs on the optical axis, from the film forward:

1. **Graflok module** (printed, separate): the back's nose pocket, the fixed bottom rail that hooks the back and releases the Pro-S dark-slide interlock, and the red clamp blade with two tongues.
2. **Body** (printed, one piece): the seat for the back, the stepped gate, the vertical guide, the rise screw, and an L bracket (bottom plinth and side leg) carrying the two Arca plates.
3. **Y plate** (printed): rises and falls on an MGN9 guide, carries the horizontal guide and the shift screw.
4. **Lens panel** (printed): shifts left and right, carries a metal M65 flange.
5. **Optics on the flange:** the helicoid, the printed adapter ring, the Technika board holder and the lens.

The light seal is the flatness of these faces. Each plate covers the opening of the one behind it, and the contact band between them, with black velvet in it, is at least 5.3 mm wide at every shift position (`cad/seal_check.py`). Hard pads on each plate set the gap and compress the velvet, so the velvet never carries load.

## Choices and why

| Choice | Why |
|---|---|
| 6x7 with RB67 backs | backs are common and cheap; the Graflok-type interface is simple enough to print; the gate also clears 6x8 |
| 65 mm lenses in Copal 0 | 33 mm equivalent on 6x7, cheap used, image circles of 153 to 170 mm for large shifts |
| Technika 99 x 96 boards | the most common board: lenses often come mounted on one, and it swaps with 4x5 field cameras |
| One board per lens, spring latch | a lens changes in ten seconds without tools; printed shims under the shutter (0.4 to 1.2 mm) let every lens reach infinity on the same stop |
| Metal M65 flange on the lens panel | a printed thread carrying the lens and the focusing torque was the weakest point of the first design |
| Printed adapter ring as the calibration part | if infinity is out of reach, reprint a thinner 20-minute part instead of a plate |
| MGN9H guides, one per axis | 20 mm carriages leave room for a seal band 6.5 mm wide; one rail and a screw per axis is enough for a stage this size |
| M6 threaded rod and brass nut, 1 mm per turn | fine control, self-locking under gravity, parts from any hardware shop; the nut floats 0.5 mm so the rod never binds |
| O-ring drag instead of lock wheels | lock wheels moved the composition as you tightened them; constant drag holds the plate and never shifts it |
| Ball-plunger zero detents | you feel zero without looking |
| Rise and fall +/-25, the same as lateral shift | the base of the L bracket is 22 mm tall so that at full fall the Y plate stays above the clamp's jaws; the two scales read the same way |
| L bracket printed with the body, side leg on the photographer's left | one continuous outline with the body's R9 corners, no joints to loosen; the RB67 dark slide comes out on the right, so nothing protrudes there; in portrait the shifted lens panel stays clear of the clamp |
| One top handle, bolted, flush with the body rear and 6 mm behind the sliding plates | printable flat, feet flared into the body, nothing overhangs the film back's advance lever, no fingers pinched by a moving plate |
| Recessed dot scales, red only for zeros, infinity and release controls | print cleanly in multi-material; red means "this is the reference" or "this lets go" |

## Design review

Before the first print the design was reviewed area by area: mechanics and printing, light-tightness, optics and registration, the RB67 interface, field use and looks. The first version had 15 problems that would have stopped the prototype, plus about 40 smaller ones. The main ones, all fixed in v1:

| Area | Blocker found | Fix |
|---|---|---|
| RB67 interface | the dark-slide side was walled off, so the slide could not come out | dark-slide relief open to the right side; nothing protrudes there |
| RB67 interface | latch bars in the wrong plane, without tongues, no relief for the back's lips | module rebuilt on the scheme of a body tested with Pro-S and Pro-SD: fixed bottom rail, top blade with two tongues, lip reliefs |
| RB67 interface | nothing released the Pro-S dark-slide interlock | the fixed bottom rail presses the catch |
| Optics | the back and the ground glass could seat on different surfaces | both seat on their nose face on the printed seat; everything else on the module (lips, rails) is relieved so it cannot touch first |
| Optics | Nikkor-SW 65/4 rear cell (54 mm) could not pass the 54 mm bores | bores to 59 mm |
| Optics / use | lens and focusing torque on 3 printed threads, helicoid free to unscrew | metal M65 flange, Loctite 222, infinity stop |
| Use | at full fall the Y plate hit the tripod clamp | taller base on the L bracket, clamp envelope in the checks at +/-25 mm |
| Use | a large side loop handle added width and snagged, and both handles overhung the body | side loop replaced by an L bracket printed with the body; the top handle sits flush with the body rear |
| Mechanics | the rise nut could not be inserted into its pocket | pocket rebuilt, nut slides in from the side |
| Mechanics | carriage screw pattern and lengths wrong | 4 x M3 per carriage, lengths computed from the stack |
| Mechanics | the lens panel could not be printed as documented | panel prints rear face down, turret is a separate part |
| Mechanics | Graflok latches could not open fully and were not retained | new blade with countersunk guide screws and a clamp wheel |
| Light | the vertical guide channel became a daylight tunnel beyond 11 mm of rise | narrower MGN9 carriages widen the seal band; press-fit plugs over the carriage screws |

Other changes from the reviews:
- Five walls around the light path.
- Felt ring on the adapter flange.
- Stepped baffles in the Y plate opening.
- Top handle set back from the sliding plates, feet flared into the body.
- Tubular levels readable from behind.
- Red used only for references.
- Single-solid and open/closed-state checks added to `check.py`.
- `seal_check.py` added.

## Automated checks

| Script | What it proves |
|---|---|
| `cad/check.py` | every printed part is one solid; no two parts intersect (threshold 0.3 mm3) at home and at the four shift extremes, with the blade and the board latch closed and open; the 65 mm clamp envelopes in landscape and portrait touch nothing that moves |
| `cad/seal_check.py` | minimum width of the contact band around the light path at both sliding interfaces, at the five shift positions |
| `cad/export.py` | `print/PRINTABILITY.txt`: overhangs and bridges of every part in its print orientation |

## Open points

- **RB67 interface.** It is derived from reference designs and has not yet been fitted on a real back. The RB67 model used by the checks has no lips or slots, so the back-to-module fit is not part of the automated check: it is test print #1 ([calibration](calibration.md#1-before-printing-the-body-test-prints)).
- **Wind-stop coupling.** Not implemented: after each frame, press the back's own release lever, as on the Mamiya Press. A plunger at the top-left corner of the module is the planned v2 feature (M7 in the calibration list).
- **Lens tilt.** The board can be squared in rotation through the adapter's arc slots, but it cannot be adjusted in tilt. Parallelism relies on flat prints: check it with the procedure in calibration.
- **Focus scale.** It is correct only once `HELI_ROT` and `FOCUS_DIR` are measured on your helicoid.
