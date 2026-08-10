# TARS simulations (MuJoCo)

Three models, all sharing dimensions with `hardware/cad/tars.scad`:

| Files | What it proves | Result |
|---|---|---|
| `gen_model.py` + `gait_sim.py` | v1 custom idea: 2 servo pairs + MPU6050 IMU balance ("lean and catch") | walks **3.0 cm/s** (sweep best 3.4), survives 4N shoves; needs closed-loop balance |
| `v3_model.py` + `v3_sim.py` | **The build architecture** (TARS-AI V3): central body touches ground, legs lift+swing. No balancing, no IMU | walks **2.4 cm/s** quasi-static, zero falls with the chosen gait |
| `pinwheel_model.py` + `roll_sim.py` | **Miller's planet WHEEL MODE**: 4 slabs splayed into a rimless wheel | needs a >=1.6 m/s kickstart; at 1.8 m/s it cartwheels **~1.6m**; powered sustained rolling needs telescoping spokes (TARS3D trick) -> v2 hardware |

```sh
source software/.venv/bin/activate    # from the project root
cd simulation
python v3_model.py && python v3_sim.py          # the build gait (headless)
mjpython v3_sim.py --gui                        # watch the V3 walk
python pinwheel_model.py && mjpython roll_sim.py --gui   # WATCH IT CARTWHEEL
mjpython gait_sim.py --gui                      # the IMU-balance walker
```

Every sim has `--sweep` for parameter search and runs until you close the
window in `--gui` mode (auto-reset on falls, camera tracks the robot).
`/Applications/MuJoCo.app` opens any of the `tars*.xml` files interactively.

## Findings log

1. Open-loop wiggling on sharp-edged feet falls, always (300+ configs).
2. Rounded bottom edges (flat middle + 6mm round-over) let the robot roll
   over the stance foot; mass must sit LOW and CENTERED.
3. Two ways to walk: IMU balance loop (fewer servos, dynamic) or the V3
   lift+swing with ground-resting body (more servos, unconditionally stable).
   We build V3 first; the gait keyframes port straight to the Pi.
4. V3 gait: feet plant slightly AHEAD (the body vaults forward over them),
   small lift (30%), vault overlapped with lowering — a controlled forward
   topple. step=14deg back=4deg tempo=0.6 lift=0.3 -> 2.0cm/cycle.
5. Wheel mode physics: a 4-spoke rimless wheel cannot start from rest
   (90-degree tip-overs) — it must be THROWN in at >=1.6 m/s, and from a
   1.8 m/s entry coasts ~1.6m. Just like the movie. Powered rolling = v2
   research (telescoping spokes or 8+ spokes).
