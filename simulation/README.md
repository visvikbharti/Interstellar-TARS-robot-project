# TARS gait simulation (MuJoCo)

Physics simulation of the walking gait, so we prove designs walk **before**
printing. Result so far: the robot walks **51cm in 10s (5.1 cm/s)** using an
IMU balance loop + "lean and catch" kick gait.

```sh
source software/.venv/bin/activate   # from the project root
cd simulation
python gen_model.py            # regenerate tars.xml after changing dimensions
python gait_sim.py             # headless run of the best gait (walks ~51cm/10s)
mjpython gait_sim.py --gui     # WATCH IT WALK (macOS needs mjpython, included in venv)
python gait_sim.py --sweep     # grid-search gait parameters
```

## What the sim taught us (chronological)

1. Sharp-edged feet + open-loop wiggling = falls, always (300+ configs).
2. Rounded bottom edges let the robot roll over the stance foot; a flat middle
   section keeps standing statically stable.
3. Mass placement is everything: battery cells low in the outer slabs + Pi on
   a front chest plate → COM at 11cm, centered (was 16cm, rear-biased).
4. **Closed-loop balance (MPU6050) is the enabler**: stance legs correct torso
   pitch (kp=2.0, kd=0.3 on pitch/pitch-rate), a 0.04 rad forward lean makes it
   perpetually fall forward, and a 25°/1.2Hz asymmetric kick gait catches it.
5. This mirrors reality: the proven TARS-AI V3 design avoids balancing entirely
   with 2 extra lift servos + resting the torso on the ground between steps.

The balance gains and gait constants port directly to the Pi servo code later.

Dimensions live in `gen_model.py` and must match `hardware/cad/tars.scad`.
