# Design Decisions

## 1. Brain: Raspberry Pi 5, 8GB  (decided 2026-08-10)

The user owns NO Raspberry Pi; buying new in India (New Delhi).

**Choice: Raspberry Pi 5 — 8GB.** Rationale:
- The voice pipeline (wake word + on-device speech-to-text via sherpa-onnx +
  Piper text-to-speech) runs comfortably in real time on a Pi 5; on a Pi 4 the
  speech-to-text step is noticeably laggy for conversation.
- 8GB gives headroom to run STT + TTS + servo control + the Claude client
  simultaneously without swap. The 4GB saves ₹7,370 (live-verified 10 Aug 2026
  — India Pi pricing is steep, so the delta is real money), but on-device
  STT/TTS is exactly what eats RAM, and the only in-stock 4GB source is the
  vendor the BOM cautions against for large orders. 8GB stands.
- The community TARS-AI stack targets Pi 5, so we stay on the well-trodden path.
- The LLM itself is *not* local — TARS thinks via the Claude API — so we don't
  need anything bigger (no Jetson etc.).

Buy alongside it: official 27W USB-C PSU (bench use), the official Active
Cooler (the Pi 5 throttles without it), 64GB microSD (no India hobby vendor
stocks A2 — the BOM's SanDisk Ultra A1 is fine for a robot). On the robot, the
Pi runs from the battery through a 2S-rated 5V/5A converter instead of the PSU.
Exact INR prices + vendors: see `hardware/BOM.md` (live-verified 10 Aug 2026).

## 2. CAD: OpenSCAD  (user-suggested; agreed)

- Fully parametric — every dimension in `hardware/cad/tars.scad` is a variable;
  change `leg_h` once and the whole robot rescales.
- Text-based → diffs cleanly in git, and we can co-edit it easily.
- Exports STL directly for slicing AND meshes/dimensions shared with the
  simulator (`simulation/gen_model.py` / `v3_model.py` mirror the same
  numbers into MuJoCo MJCF).
- Escape hatch: if we later adopt proven community STLs (Charlie Diaz /
  TARS-AI, license research pending), OpenSCAD still handles our custom parts
  (spine, mounts, brackets).

## 3. Simulation: MuJoCo  (instead of Cinema 4D)

"Cinema 4D" is an animation/rendering tool — it makes pretty pictures but does
not simulate physics, motors, friction, or falling over, which is what we need
before printing. The plan:

| Purpose | Tool | Why |
|---|---|---|
| Gait physics (does it walk? fall?) | **MuJoCo** | DeepMind's physics engine, the robotics-research standard; installs instantly from a wheel; scriptable in Python; `mjpython gait_sim.py --gui` gives a live 3D view on the Mac |
| Mechanical fit / printability | **OpenSCAD** previews + slicer | Wall thickness, clearances, print orientation |
| Pretty renders (later, optional) | Blender (free) | Same niche as Cinema 4D, no license cost |

Alternatives considered: PyBullet (first pick, but it compiles from source on
macOS and the build failed — MuJoCo ships wheels and is the better engine
anyway), Webots (good fallback for sensor simulation), Gazebo (ROS-oriented,
overkill).

Big win: the balance gains and gait constants we tune in MuJoCo port almost
directly to the real servo code on the Pi.

## 4. Gait mechanism — VALIDATED IN SIM (2026-08-10)

> **Superseded by §8 (audit, 2026-09-29):** the IMU-balance result below did
> not hold up; the walker slumps into a tilted A-frame. Kept for the record.

Simulation verdict on the v0.1 two-servo rocking gait: **open-loop always falls**
(300+ configs swept). What made it walk:
- Deeper slabs (55mm), rounded bottom edges (roll-over, not edge-pivot)
- Low, centered mass: 18650 cells in outer slab bottoms, Pi on a front chest plate
- **IMU balance loop** (MPU6050): stance legs correct torso pitch, segway-style
- "Lean and catch": 0.04 rad forward lean + 25° kick gait at 1.2 Hz
- Result: **30cm in 10s (3.0 cm/s), upright, drift <1cm** at true MG996R
  torque (1.0 N·m; an earlier 5.1 cm/s figure came from an inflated 2.5 N·m
  servo model — corrected in the 10 Aug audit, all 75 sweep configs still
  stay upright)

## 5. Chassis fork: TARS-AI V3 STLs vs our custom SCAD

Research verdict: TARS-AI Community V3 is the ONLY proven walkable open design
(25.0cm tall — measured from their CAD; CC-BY-NC 4.0, personal use fine). Its
gait needs no balancing: 2 lift + 2 swing servos, torso rests on the ground
between steps.

**Recommended plan:** print & build TARS-AI V3 first (proven path: STLs,
assembly wiki, calibration tool, community Discord) while continuing our custom
OpenSCAD + MuJoCo design as the v2 platform (fewer servos, dynamic balance, our
own look). The electronics BOM is ~identical for both, so nothing ordered is
wasted either way. Next sim milestone: model the V3 lift+swing morphology in
MuJoCo and reproduce their keyframe gait before hardware arrives.

## 6. Sim-validated architecture + wheel mode (2026-08-10, late session)

> **Superseded by §8 (audit, 2026-09-29):** the V3 gait below only walked at
> the default 2 ms time step, and wheel mode did not roll. Kept for the record.

- **V3 morphology simulated and walking**: body-on-ground + lift/swing legs,
  2.4 cm/s quasi-static, zero falls (at true 1.0 N·m servo torque). Winning
  gait: plant feet 14deg AHEAD (step=14, back=4 — the body vaults forward
  over them), lift 30% of 35mm travel, vault overlapped with lowering
  (controlled forward topple). These keyframes ARE the future Pi servo code.
- **Wheel mode (Miller's planet)**: works as kickstart-and-coast — needs a
  ≥1.6 m/s entry; at 1.8 m/s (the sweet spot — 2.0 falls) the 4-slab
  pinwheel cartwheels ~1.6m. Cannot start from rest
  (4 spokes = 90deg tip-overs) and powered pumping destabilizes via hub
  counter-spin. Sustained powered rolling needs per-slab continuous drive +
  telescoping spokes (TARS3D, arXiv 2510.05001) -> v2 hardware goal with
  serial-bus servos.
- **CAD v0.3 final for v1**: central chassis (twin-slab facade; Pi vertical,
  display window, speaker grille, servo bays at the axle) + two outer legs
  (35mm axle slot for lift travel, 608ZZ bearing seat). v0.4 details pending:
  lift crank linkage, lids, wire channels.

## 7. Printing: outsourced to a print service (2026-08-10)

No home printer — chassis parts are ordered from an online 3D-printing
service, the workflow proven the same week on the micro-quad project
(ZBOTiC order delivered 10 Aug 2026; received part matched CAD, press-fit
bores true). Consequences:
- No filament spools in the BOM — material is specified in the print order
  instead (black PLA cosmetic, black PETG 3+ walls for load parts).
- No printer/bed-size constraint on our side.
- Vendors, settings, pinned STL source and on-receipt checks:
  `hardware/print-plan.md`.

## 8. Simulation audit + crutch-vault gait (2026-09-29)

Re-ran every simulation with finer solver settings (0.5 and 0.25 ms time
steps, the implicit and RK4 integrators, elliptic friction cones) and with a
strict fall test (body AND every slab within 45 deg of vertical, axle above
150 mm). Findings:

- **Old V3 gait** (feet planted 14 deg ahead, vault overlapped with lowering):
  walked only at the default 2 ms step; tipped over within 3-9 s at 0.5 ms,
  with implicitfast, or with elliptic cones. The body landed before it could
  vault; the progress came from rocking on the rails.
- **IMU-balance walker:** slumps into a tilted A-frame within 0.5 s (slabs
  ~60 deg, axle 140 mm). The old test only checked the torso.
- **Wheel mode:** tumbles ~0.4 m, then folds flat or falls sideways. Stiffer
  spokes (5-20 N m) fall sideways sooner. Needs a different mechanism (v2).

**Decision:** the build gait is now a **crutch vault**: press down on
vertical legs (weight over the feet), rotate the hinges back 12 deg with the
body fully off the ground, set down, swing the unloaded legs forward.
`vault=12 lift=0.7 tempo=1.0`: 35.9 cm in 15 s, worst tilt 11.5 deg, and the
same result at all 15 settings in `python v3_sim.py --robust` (incl. floor
friction 0.5-1.3, 20% weaker servos, body mass -10%/+20%). Peak loads: swing
0.30 N m (MG996R ~1.0), lift ~11 N (of 55). These keyframes are the future
Pi servo code. The CAD needs no change (the gait uses 24.5 of the 35 mm lift
travel).
