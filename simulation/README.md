# TARS simulations (MuJoCo)

Three models, all sharing dimensions with `hardware/cad/tars.scad`:

| Files | What it tests | Result (audited 2026-09-29) |
|---|---|---|
| `v3_model.py` + `v3_sim.py` | **The build architecture** (TARS-AI V3): central body touches ground, legs lift+swing. No balancing, no IMU | **walks 36 cm in 15 s (2.4 cm/s), upright**, with the crutch-vault gait, and the same at every setting in `--robust` |
| `gen_model.py` + `gait_sim.py` | v1 custom idea: 2 servo pairs + MPU6050 IMU balance ("lean and catch") | **does not walk upright**: slumps into a tilted A-frame within 0.5 s (0/75 sweep settings upright) |
| `pinwheel_model.py` + `roll_sim.py` | **Miller's planet WHEEL MODE**: 4 slabs splayed into a rimless wheel | **does not roll**: tumbles ~0.4 m, then folds flat or falls sideways; needs a different mechanism (telescoping spokes, TARS3D) -> v2 research |

```sh
source software/.venv/bin/activate    # from the project root
cd simulation
python v3_model.py && python v3_sim.py          # the build gait (headless)
python v3_sim.py --robust                       # the same gait across 15 solver/physics settings
mjpython v3_sim.py --gui                        # watch the V3 walk
python pinwheel_model.py && mjpython roll_sim.py --gui   # wheel mode (falls: v2 research)
mjpython gait_sim.py --gui                      # the IMU-balance walker (slumps)
```

Every sim has `--sweep` for parameter search and runs until you close the
window in `--gui` mode (auto-reset on falls, camera tracks the robot).
`v3_sim.py --sweep` only keeps gaits that stay upright at 2 ms AND at 0.5 ms
with elliptic friction cones. Every fall test checks the body and all slabs
(within 45 deg of vertical) and the axle height, not just the torso.
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
6. **Audit, 29 Sep 2026.** Re-running every sim with finer solver settings and
   stricter fall tests: (a) the old V3 gait (feet planted 14 deg ahead, vault
   overlapped with lowering) only walked at the default 2 ms time step; at
   0.5 ms, with the implicit integrator or with elliptic friction cones it
   tipped over within 3-9 s. Its progress came from the body rocking on its
   rails, not from a vault: the body landed before it vaulted. (b) The
   IMU-balance walker's "upright" came from a fall test that only checked the
   torso; its slabs slump to ~60 deg within 0.5 s. (c) Wheel mode's "~1.6 m"
   was the folded, flat robot creeping undriven after a ~0.4 m tumble.
7. **The fix: a crutch vault.** Press the legs down while they are VERTICAL
   (the weight stays over the feet), rotate the hinges back 12 deg with the
   body fully off the ground (it swings forward over the planted feet), set
   it down, then swing the unloaded legs forward. vault=12 lift=0.7
   tempo=1.0 -> 35.9 cm in 15 s (4.3 cm/cycle), worst tilt 11.5 deg, the same
   to within 2 mm at every time step from 2 ms to 0.25 ms. Peak swing torque
   0.30 N m (30% of an MG996R), peak lift force ~11 N (of 55 N).
