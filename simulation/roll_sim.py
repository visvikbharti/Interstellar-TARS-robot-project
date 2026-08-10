"""WHEEL MODE — TARS cartwheels like on Miller's planet.

The four slabs splay into a pinwheel (spokes every 90 degrees) and the robot
rolls over the slab tips like a rimless wheel. Sim findings: this works as a
KICKSTART-AND-COAST maneuver — it needs >=1.6 m/s to clear the 90 degree
tip-overs, and entered at 1.8 m/s it rolls ~1.6m (movie-accurate: TARS
enters the spin from a run). Sustained powered rolling needs telescoping
spokes (TARS3D trick) — future v2 hardware research.

Usage:
  python roll_sim.py                # headless: kickstart, measure roll
  python roll_sim.py --sweep       # try spin rates x spoke layouts
  mjpython roll_sim.py --gui       # WATCH IT CARTWHEEL
"""

from __future__ import annotations

import argparse
import math
import time
from pathlib import Path

import mujoco

HERE = Path(__file__).parent
SPOKE = 0.215

# spoke layouts: slab index -> spoke angle (deg from straight down)
LAYOUTS = {
    "staircase": [45, 135, 225, 315],   # spokes in y-order across the robot
    "interleave": [45, 225, 135, 315],  # adjacent slabs on opposite phases
}


def load():
    path = HERE / "tars_wheel.xml"
    if not path.exists():
        raise SystemExit("tars_wheel.xml missing — run: python pinwheel_model.py")
    return mujoco.MjModel.from_xml_path(str(path))


def roll_angle_deg(qpos) -> float:
    """Lateral (roll-over sideways) tilt of the hub axis — fall detector."""
    w, x, y, z = qpos[3:7]
    # world-z component of the body-y axis (the hub axis): 2*(y*z + w*x)
    axis_tilt = 2 * (y * z + w * x)
    return math.degrees(math.asin(max(-1.0, min(1.0, axis_tilt))))


def setup(model, layout, v0=0.0):
    data = mujoco.MjData(model)
    angles = [math.radians(a) for a in LAYOUTS[layout]]
    lowest = min(-SPOKE * math.cos(a) for a in angles)      # most-downward spoke tip
    data.qpos[2] = -lowest + 0.002                          # stand on the low spokes
    for i, a in enumerate(angles):
        data.qpos[7 + i] = a
        data.act[i] = a          # intvelocity integrator starts AT the pose
    # kickstart: wheel mode is entered from a running start (movie-accurate)
    data.qvel[0] = v0            # forward speed
    data.qvel[4] = v0 / 0.19     # matching roll rate about the hub axis
    mujoco.mj_forward(model, data)
    return data


def run(model, layout: str, omega: float, seconds: float = 14.0, v0: float = 1.2,
        gui: bool = False) -> dict:
    data = setup(model, layout, v0)
    if gui:
        from mujoco import viewer as mj_viewer
        v = mj_viewer.launch_passive(model, data)
        v.cam.distance, v.cam.elevation, v.cam.azimuth = 2.2, -12, 115
        wall0 = time.monotonic()
        frame = 0
    fell = False
    x_mark = None
    while data.time < seconds:
        t = data.time
        data.ctrl[:] = omega
        mujoco.mj_step(model, data)
        if abs(roll_angle_deg(data.qpos)) > 45:
            fell = True
            break
        if x_mark is None and t >= seconds - 5.0:
            x_mark = data.qpos[0]
        if gui:
            frame += 1
            if frame % 8 == 0:
                if not v.is_running():
                    break
                v.cam.lookat[0] = data.qpos[0]
                v.cam.lookat[2] = 0.18
                v.sync()
                lag = data.time - (time.monotonic() - wall0)
                if lag > 0:
                    time.sleep(lag)
    if gui:
        v.close()
    speed = (data.qpos[0] - x_mark) / 5.0 if (x_mark is not None and not fell) else 0.0
    return {
        "x_cm": 100 * data.qpos[0],
        "speed_cm_s": 100 * speed,
        "drift_cm": 100 * data.qpos[1],
        "fell": fell,
        "t": data.time,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--omega", type=float, default=0.0, help="slab spin rate (0 = rigid coast, the stable mode)")
    ap.add_argument("--v0", type=float, default=1.8, help="kickstart speed, m/s (needs >=1.6 to clear tip-overs)")
    ap.add_argument("--layout", choices=tuple(LAYOUTS), default="interleave")
    ap.add_argument("--seconds", type=float, default=14.0)
    args = ap.parse_args()

    model = load()

    if args.sweep:
        print(f"{'layout':>11} {'omega':>6} {'x':>9} {'speed':>10} {'drift':>8}  result")
        best = None
        for layout in LAYOUTS:
            for v0 in (0.8, 1.2, 1.8):
                for omega in (0.0, 2.0, 4.0, 6.0):
                    r = run(model, layout, omega, args.seconds, v0)
                    tag = "FELL" if r["fell"] else "ok"
                    print(f"{layout:>11} v0={v0:.1f} w={omega:>4.1f} {r['x_cm']:>8.1f}c "
                          f"{r['speed_cm_s']:>8.1f}c/s {r['drift_cm']:>7.1f}c  {tag}")
                    if not r["fell"] and (best is None or r["x_cm"] > best[3]):
                        best = (layout, v0, omega, r["x_cm"], r["speed_cm_s"])
        if best:
            print(f"\nbest: --layout {best[0]} --v0 {best[1]} --omega {best[2]}"
                  f"  (reached {best[3]:.0f}cm, end speed {best[4]:.0f}cm/s)")
        return

    r = run(model, args.layout, args.omega, args.seconds, args.v0, gui=args.gui)
    tag = "FELL OVER" if r["fell"] else "sustained roll"
    print(f"layout={args.layout} omega={args.omega:.1f}rad/s  ->  "
          f"reached x={r['x_cm']:+.0f}cm, cruise {r['speed_cm_s']:.0f} cm/s, "
          f"drift {r['drift_cm']:+.1f}cm, {tag}")


if __name__ == "__main__":
    main()
