"""MuJoCo gait simulation for the TARS mini.

Walking = "lean and catch": an IMU balance loop (MPU6050 on the real robot)
keeps the torso upright via the stance legs, a small forward lean makes the
robot perpetually fall forward, and the inner pair's kick gait keeps catching
it. Best found gait: 51cm in 10s (amp=25 freq=1.2 kp=2.0 kd=0.3 lean=0.04).

Usage:
  python gait_sim.py                    # headless, prints distance walked
  python gait_sim.py --sweep            # grid-search amp/freq, prints a table
  mjpython gait_sim.py --gui            # watch it walk (macOS needs mjpython)
  python gait_sim.py --amp 35 --freq 1.2 --seconds 15
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import mujoco

HERE = Path(__file__).parent


def load():
    path = HERE / "tars.xml"
    if not path.exists():
        raise SystemExit("tars.xml missing — run: python gen_model.py")
    return mujoco.MjModel.from_xml_path(str(path))


def tilt_deg(qpos) -> float:
    """Angle between the torso's up-axis and world up, in degrees."""
    w, x, y, z = qpos[3:7]
    # z-column of the rotation matrix, world-frame z of body z-axis
    up_z = 1 - 2 * (x * x + y * y)
    return math.degrees(math.acos(max(-1.0, min(1.0, up_z))))


def kick_wave(u: float, duty: float) -> float:
    """Asymmetric triangle in [-1, 1]: fast forward kick (duty fraction of the
    cycle), slow return. u is the cycle position in [0, 1). Starts mid-kick (0)."""
    u = (u + duty / 2) % 1.0
    if u < duty:
        return -1 + 2 * (u / duty)
    return 1 - 2 * ((u - duty) / (1 - duty))


def run(
    model,
    seconds: float,
    amp_deg: float,
    freq: float,
    outer_amp_deg: float | None = None,
    phase_deg: float = 180.0,
    wave: str = "sin",
    duty: float = 0.25,
    bal_kp: float = 0.0,
    bal_kd: float = 0.0,
    lean: float = 0.0,
    push: float = 0.0,
    gui: bool = False,
) -> dict:
    data = mujoco.MjData(model)
    outer = model.actuator("outer_servo").id
    inner = model.actuator("inner_servo").id
    amp = math.radians(amp_deg)
    outer_amp = math.radians(outer_amp_deg if outer_amp_deg is not None else amp_deg)
    phase = math.radians(phase_deg)
    w = 2 * math.pi * freq

    viewer = None
    if gui:
        from mujoco import viewer as mj_viewer  # macOS: run under mjpython

        viewer = mj_viewer.launch_passive(model, data)

    # settle standing for 1s
    while data.time < 1.0:
        data.ctrl[outer] = data.ctrl[inner] = 0.0
        mujoco.mj_step(model, data)
        if viewer:
            viewer.sync()

    x0, y0 = data.qpos[0], data.qpos[1]
    t0 = data.time
    fell = False
    while data.time - t0 < seconds:
        t = data.time - t0
        if wave == "kick":
            u = (t * freq) % 1.0
            gait_i = amp * kick_wave(u, duty)
            gait_o = outer_amp * kick_wave((u + phase / (2 * math.pi)) % 1.0, duty)
        else:
            gait_i = amp * math.sin(w * t)
            gait_o = outer_amp * math.sin(w * t + phase)

        # IMU balance loop (MPU6050 on the real robot): stance legs correct
        # torso pitch, segway-style
        qw, qx, qy, qz = data.qpos[3:7]
        pitch = math.asin(max(-1.0, min(1.0, 2 * (qw * qy - qz * qx))))
        corr = bal_kp * (pitch - lean) + bal_kd * data.qvel[4]
        data.ctrl[outer] = gait_o + corr
        data.ctrl[inner] = gait_i + corr

        # optional disturbance to test balance robustness
        if push and 2.0 < t < 2.1:
            data.xfrc_applied[model.body("torso").id][0] = push
        elif push:
            data.xfrc_applied[model.body("torso").id][0] = 0.0
        mujoco.mj_step(model, data)
        if viewer:
            viewer.sync()
        if data.qpos[2] < 0.10 or tilt_deg(data.qpos) > 70:
            fell = True
            break

    if viewer:
        viewer.close()

    walked = data.qpos[0] - x0
    return {
        "walked_cm": 100 * walked,
        "drift_cm": 100 * (data.qpos[1] - y0),
        "fell": fell,
        "speed_cm_s": 100 * walked / seconds if not fell else 0.0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gui", action="store_true", help="show the 3D view (use mjpython on macOS)")
    ap.add_argument("--sweep", action="store_true", help="grid-search amp x freq")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--amp", type=float, default=25.0, help="inner swing amplitude, degrees")
    ap.add_argument("--outer-amp", type=float, default=0.0, help="outer swing amplitude, degrees")
    ap.add_argument("--phase", type=float, default=180.0, help="outer phase offset, degrees")
    ap.add_argument("--freq", type=float, default=1.2, help="gait frequency, Hz")
    ap.add_argument("--wave", choices=("sin", "kick"), default="kick")
    ap.add_argument("--duty", type=float, default=0.3, help="kick: forward-stroke fraction")
    ap.add_argument("--kp", type=float, default=2.0, help="IMU balance P gain (0 = off)")
    ap.add_argument("--kd", type=float, default=0.3, help="IMU balance D gain")
    ap.add_argument("--lean", type=float, default=0.04, help="forward lean setpoint, rad")
    args = ap.parse_args()

    model = load()

    if args.sweep:
        results = []
        for amp in (15, 25, 35, 50):
            for outer_amp in (5, 10, 20, 35):
                for phase in (90, 180, 270):
                    for freq in (0.5, 0.8, 1.2):
                        r = run(model, args.seconds, amp, freq, outer_amp, phase)
                        results.append((amp, outer_amp, phase, freq, r))
        stable = [x for x in results if not x[4]["fell"]]
        stable.sort(key=lambda x: -abs(x[4]["walked_cm"]))
        print(f"{len(stable)}/{len(results)} gaits stayed upright; top 10 by distance:")
        print(f"{'inner':>6} {'outer':>6} {'phase':>6} {'freq':>5} {'walked':>9} {'drift':>8}")
        for amp, oamp, ph, fr, r in stable[:10]:
            print(
                f"{amp:>5.0f}d {oamp:>5.0f}d {ph:>5.0f}d {fr:>5.1f} "
                f"{r['walked_cm']:>8.1f}c {r['drift_cm']:>7.1f}c"
            )
        if stable:
            a, o, ph, fr, r = stable[0]
            print(
                f"\nbest: --amp {a} --outer-amp {o} --phase {ph} --freq {fr}"
                f"  ({r['walked_cm']:.1f} cm in {args.seconds:.0f}s)"
            )
        return

    r = run(model, args.seconds, args.amp, args.freq, args.outer_amp, args.phase,
            wave=args.wave, duty=args.duty, bal_kp=args.kp, bal_kd=args.kd,
            lean=args.lean, gui=args.gui)
    verdict = "FELL OVER" if r["fell"] else "stayed upright"
    print(
        f"amp={args.amp:.0f}deg freq={args.freq:.1f}Hz  ->  walked {r['walked_cm']:+.1f} cm "
        f"(drift {r['drift_cm']:+.1f} cm), {r['speed_cm_s']:.1f} cm/s, {verdict}"
    )


if __name__ == "__main__":
    main()
