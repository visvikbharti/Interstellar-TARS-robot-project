# Design Decisions

## 1. Brain: Raspberry Pi 5, 8GB  (decided 2026-08-10)

The user owns NO Raspberry Pi; buying new in India (New Delhi).

**Choice: Raspberry Pi 5 — 8GB.** Rationale:
- The voice pipeline (wake word + on-device speech-to-text via sherpa-onnx +
  Piper text-to-speech) runs comfortably in real time on a Pi 5; on a Pi 4 the
  speech-to-text step is noticeably laggy for conversation.
- 8GB gives headroom to run STT + TTS + servo control + the Claude client
  simultaneously without swap. The 4GB saves ~₹1.5–2k but is the first thing
  you'd regret.
- The community TARS-AI stack targets Pi 5, so we stay on the well-trodden path.
- The LLM itself is *not* local — TARS thinks via the Claude API — so we don't
  need anything bigger (no Jetson etc.).

Buy alongside it: official 27W USB-C PSU (bench use), the official Active
Cooler (the Pi 5 throttles without it), 64GB A2 microSD. On the robot, the Pi
runs from the battery through a 5V/5A buck converter instead of the PSU.
Exact INR prices + vendors: see `hardware/BOM.md` (in progress).

## 2. CAD: OpenSCAD  (user-suggested; agreed)

- Fully parametric — every dimension in `hardware/cad/tars.scad` is a variable;
  change `slab_h` once and the whole robot rescales.
- Text-based → diffs cleanly in git, and we can co-edit it easily.
- Exports STL directly for slicing AND meshes/dimensions shared with the
  simulator (`simulation/gen_urdf.py` mirrors the same numbers).
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

Simulation verdict on the v0.1 two-servo rocking gait: **open-loop always falls**
(300+ configs swept). What made it walk:
- Deeper slabs (55mm), rounded bottom edges (roll-over, not edge-pivot)
- Low, centered mass: 18650 cells in outer slab bottoms, Pi on a front chest plate
- **IMU balance loop** (MPU6050): stance legs correct torso pitch, segway-style
- "Lean and catch": 0.04 rad forward lean + 25° kick gait at 1.2 Hz
- Result: **51cm in 10s (5.1 cm/s), upright, drift <1cm**

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

- **V3 morphology simulated and walking**: body-on-ground + lift/swing legs,
  2.3 cm/s quasi-static, zero falls. Winning gait: plant feet 14deg behind,
  lift 30% of 35mm travel, vault overlapped with lowering (controlled forward
  topple). These keyframes ARE the future Pi servo code.
- **Wheel mode (Miller's planet)**: works as kickstart-and-coast — entered at
  1.8 m/s the 4-slab pinwheel cartwheels 1.4-1.6m. Cannot start from rest
  (4 spokes = 45deg tip-overs) and powered pumping destabilizes via hub
  counter-spin. Sustained powered rolling needs per-slab continuous drive +
  telescoping spokes (TARS3D, arXiv 2510.05001) -> v2 hardware goal with
  serial-bus servos.
- **CAD v0.3 final for v1**: central chassis (twin-slab facade; Pi vertical,
  display window, speaker grille, servo bays at the axle) + two outer legs
  (35mm axle slot for lift travel, 608ZZ bearing seat). v0.4 details pending:
  lift crank linkage, lids, wire channels.
