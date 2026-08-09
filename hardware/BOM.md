# Bill of Materials — TARS mini

Based on the proven TARS-AI Community **V3** BOM (the community-standard 25.0cm
walking TARS, verified by measuring their official CAD), plus our additions.
INR prices from Indian vendors are being researched — column will be filled in.

Buyer location: New Delhi, India. Prefer robu.in / amazon.in / kitsguru.

## Core electronics

| # | Item | Spec / role | Qty | ~INR | Notes |
|---|------|-------------|-----|------|-------|
| 1 | **Raspberry Pi 5 — 8GB** | The brain. Runs wake word + STT + TTS locally, Claude API for thinking | 1 | TBD | 4GB is the documented minimum; 8GB buys vision/face features + headroom |
| 2 | Official Pi 5 Active Cooler | Pi 5 throttles without it inside a closed torso | 1 | TBD | |
| 3 | Official 27W USB-C PSU | Bench/desk use only (robot runs from battery) | 1 | TBD | |
| 4 | microSD 64GB A2 (SanDisk/Samsung) | OS | 1 | TBD | |
| 5 | **MG996R metal-gear servos** | Legs: 2× lift + 2× swing (TARS-AI V3 layout) | 4 | TBD | Metal gears non-negotiable; DS3218 20kg is the premium upgrade (~2× torque, same size) |
| 6 | PCA9685 16-ch PWM board | Servo driver over I2C — all community gait code targets it | 1 | TBD | |
| 7 | **MPU6050 IMU** | Balance/tilt sensing (our sim shows closed-loop balance enables 2-servo gaits; also useful for fall detection) | 1 | TBD | ~₹150; not in TARS-AI BOM — our addition |
| 8 | 12V Li-ion pack ~3000mAh + charger | Single battery, split into two rails | 1 | TBD | TalentCell-style; ~1.5–2.5h runtime |
| 9 | XL4015 5A buck converter | 12V → 6.0–6.2V **servo rail** | 1 | TBD | Add 470–1000µF cap across servo rail |
| 10 | 12V→5V 5–6A USB step-down | 12V → 5V **Pi rail** (separate from servos!) | 1 | TBD | Shared ground only — kills servo-brownout reboots |
| 11 | 5" DSI display (800×480/1024×600) | TARS's chest screen | 1 | TBD | DSI keeps HDMI free, ribbon stays inside; portrait mount |
| 12 | Waveshare "USB TO AUDIO" dongle | Mic in + **amplified** speaker out (2.6W BTL, drives the speaker directly — no amp board needed, verified) | 1 | TBD | Ships with the 8Ω 5W speaker in the US listing; check Indian listing contents |
| 13 | 8Ω 5W speaker | TARS's voice | 1 | TBD | Skip if included with #12 |
| 14 | OV5647 5MP camera (optional) | Vision / face presence | 1 | TBD | Pi-5-only features in TARS-AI stack |
| 15 | INA260 battery monitor (optional) | Auto-shutdown on low battery | 1 | TBD | Small solder job |
| 16 | Micro rocker switch, Dupont jumpers | Power + wiring | — | TBD | |
| 17 | M3 screw assortment (~140 pcs) | Chassis assembly | 1 kit | TBD | V3 uses M3 only, ~116 screws legs-only |
| 18 | PETG filament | Chassis (~1kg legs-only; PETG > PLA for load parts) | 1 kg | TBD | + optional 200g TPU for foot pads |

Our custom-design extras (only if we build the 2-servo SCAD chassis instead of
TARS-AI STLs): 8mm aluminium rod (~250mm), 2× 608ZZ bearings, 2× 18650 cells +
holders (low-mounted, one per outer slab).

## Print settings (community-validated for this design)

PETG, 0.2mm layers, 3+ walls, 20% gyroid infill, 5 top/bottom layers, no brim,
tree supports. **Bed must be ≥180×180mm** (largest part prints diagonally at
176×176mm). Print their calibration tool first — fits assume ±0.2mm accuracy.

## Power architecture (do not deviate)

```
12V Li-ion pack ──┬── XL4015 buck @ 6.0–6.2V ──► PCA9685 V+ ──► servos
                  └── 5V/5A USB step-down ─────► Raspberry Pi 5
                        (grounds common, rails separate)
```
Never power servos from the Pi's 5V rail. MG996R stall is ~2.5A *each*.
