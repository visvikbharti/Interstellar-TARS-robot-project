"""MuJoCo gait simulation for the TARS mini.

Walking = "lean and catch": an IMU balance loop (MPU6050 on the real robot)
keeps the torso upright via the stance legs, a small forward lean makes the
robot perpetually fall forward, and the inner pair's kick gait keeps catching
it. Best found gait: ~30cm in 10s (amp=25 freq=1.2 kp=2.0 kd=0.3 lean=0.04).

Usage:
  python gait_sim.py                    # headless, prints distance walked
  python gait_sim.py --sweep            # grid-search the balanced gait
  mjpython gait_sim.py --gui            # watch it walk — runs until you close
                                        # the window (macOS needs mjpython)
Tip: /Applications/MuJoCo.app also opens simulation/tars.xml directly for
interactive poking (double-click a body, ctrl+drag to apply forces).
"""

from __future__ import annotations

import argparse
import math
import time
from pathlib import Path

import mujoco

HERE = Path(__file__).parent

BEST = dict(amp_deg=25.0, freq=1.2, outer_amp_deg=0.0, phase_deg=180.0,
            wave="kick", duty=0.3, bal_kp=2.0, bal_kd=0.3, lean=0.04)


def load():
    path = HERE / "tars.xml"
    if not path.exists():
        raise SystemExit("tars.xml missing — run: python gen_model.py")
    return mujoco.MjModel.from_xml_path(str(path))


def tilt_deg(qpos) -> float:
    """Angle between the torso's up-axis and world up, in degrees."""
    w, x, y, z = qpos[3:7]
    up_z = 1 - 2 * (x * x + y * y)
    return math.degrees(math.acos(max(-1.0, min(1.0, up_z))))


def kick_wave(u: float, duty: float) -> float:
    """Asymmetric triangle in [-1, 1]: fast forward kick (duty fraction of the
    cycle), slow return. u is the cycle position in [0, 1). Starts mid-kick (0)."""
    u = (u + duty / 2) % 1.0
    if u < duty:
        return -1 + 2 * (u / duty)
    return 1 - 2 * ((u - duty) / (1 - duty))


class GaitController:
    """Computes servo targets: gait waveform + IMU balance correction.
    This is exactly what the Raspberry Pi will run on the real robot."""

    def __init__(self, amp_deg, freq, outer_amp_deg, phase_deg, wave, duty,
                 bal_kp, bal_kd, lean):
        self.amp = math.radians(amp_deg)
        self.outer_amp = math.radians(outer_amp_deg if outer_amp_deg is not None else amp_deg)
        self.phase = math.radians(phase_deg)
        self.freq = freq
        self.wave = wave
        self.duty = duty
        self.kp, self.kd, self.lean = bal_kp, bal_kd, lean

    def targets(self, t: float, qpos, qvel) -> tuple[float, float]:
        if self.wave == "kick":
            u = (t * self.freq) % 1.0
            gait_i = self.amp * kick_wave(u, self.duty)
            gait_o = self.outer_amp * kick_wave((u + self.phase / (2 * math.pi)) % 1.0, self.duty)
        else:
            w = 2 * math.pi * self.freq
            gait_i = self.amp * math.sin(w * t)
            gait_o = self.outer_amp * math.sin(w * t + self.phase)
        # IMU balance (MPU6050): correct torso pitch through both leg pairs
        qw, qx, qy, qz = qpos[3:7]
        pitch = math.asin(max(-1.0, min(1.0, 2 * (qw * qy - qz * qx))))
        corr = self.kp * (pitch - self.lean) + self.kd * qvel[4]
        return gait_o + corr, gait_i + corr


def fallen(data) -> bool:
    return data.qpos[2] < 0.10 or tilt_deg(data.qpos) > 70


def run(model, seconds: float, ctl: GaitController, push: float = 0.0) -> dict:
    """Headless run; returns walk statistics."""
    data = mujoco.MjData(model)
    outer = model.actuator("outer_servo").id
    inner = model.actuator("inner_servo").id

    while data.time < 1.0:  # settle standing
        data.ctrl[outer] = data.ctrl[inner] = 0.0
        mujoco.mj_step(model, data)

    x0, y0 = data.qpos[0], data.qpos[1]
    t0 = data.time
    fell = False
    while data.time - t0 < seconds:
        t = data.time - t0
        data.ctrl[outer], data.ctrl[inner] = ctl.targets(t, data.qpos, data.qvel)
        if push:
            body = model.body("torso").id
            data.xfrc_applied[body][0] = push if 2.0 < t < 2.1 else 0.0
        mujoco.mj_step(model, data)
        if fallen(data):
            fell = True
            break

    walked = data.qpos[0] - x0
    return {
        "walked_cm": 100 * walked,
        "drift_cm": 100 * (data.qpos[1] - y0),
        "fell": fell,
        "speed_cm_s": 100 * walked / seconds if not fell else 0.0,
    }


def gui_run(model, ctl: GaitController) -> None:
    """Interactive viewer: walks until you close the window. Smooth ~60fps,
    camera follows the robot, auto-resets if it falls."""
    from mujoco import viewer as mj_viewer  # macOS: run under mjpython

    data = mujoco.MjData(model)
    outer = model.actuator("outer_servo").id
    inner = model.actuator("inner_servo").id
    steps_per_frame = max(1, round(1 / 60 / model.opt.timestep))  # ~60 fps

    with mj_viewer.launch_passive(model, data) as v:
        v.cam.distance, v.cam.elevation, v.cam.azimuth = 1.4, -12, 125
        wall0 = time.monotonic()
        walk_t0 = None
        falls = 0
        while v.is_running():
            for _ in range(steps_per_frame):
                if data.time < 1.0:      # settle phase (also after each reset)
                    data.ctrl[outer] = data.ctrl[inner] = 0.0
                else:
                    if walk_t0 is None:
                        walk_t0 = data.time
                    t = data.time - walk_t0
                    data.ctrl[outer], data.ctrl[inner] = ctl.targets(t, data.qpos, data.qvel)
                mujoco.mj_step(model, data)
                if fallen(data):
                    falls += 1
                    print(f"fell at x={data.qpos[0]*100:+.1f}cm — resetting (fall #{falls})")
                    mujoco.mj_resetData(model, data)
                    walk_t0 = None
                    wall0 = time.monotonic()
                    break
            # camera tracks the robot as it walks
            v.cam.lookat[0] = data.qpos[0]
            v.cam.lookat[2] = 0.15
            v.sync()
            lag = data.time - (time.monotonic() - wall0)
            if lag > 0:
                time.sleep(lag)
        print(f"viewer closed — walked to x={data.qpos[0]*100:+.1f}cm, falls: {falls}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gui", action="store_true", help="live 3D view, runs until closed (macOS: use mjpython)")
    ap.add_argument("--sweep", action="store_true", help="grid-search the balanced gait")
    ap.add_argument("--seconds", type=float, default=10.0, help="headless run length")
    ap.add_argument("--amp", type=float, default=BEST["amp_deg"], help="inner swing amplitude, deg")
    ap.add_argument("--outer-amp", type=float, default=BEST["outer_amp_deg"], help="outer swing amplitude, deg")
    ap.add_argument("--phase", type=float, default=BEST["phase_deg"], help="outer phase offset, deg")
    ap.add_argument("--freq", type=float, default=BEST["freq"], help="gait frequency, Hz")
    ap.add_argument("--wave", choices=("sin", "kick"), default=BEST["wave"])
    ap.add_argument("--duty", type=float, default=BEST["duty"], help="kick: forward-stroke fraction")
    ap.add_argument("--kp", type=float, default=BEST["bal_kp"], help="IMU balance P gain (0 = off)")
    ap.add_argument("--kd", type=float, default=BEST["bal_kd"], help="IMU balance D gain")
    ap.add_argument("--lean", type=float, default=BEST["lean"], help="forward lean setpoint, rad")
    ap.add_argument("--push", type=float, default=0.0, help="test shove in newtons at t=2s")
    args = ap.parse_args()

    model = load()

    if args.sweep:
        results = []
        for amp in (15, 20, 25, 30, 35):
            for freq in (0.8, 1.0, 1.2, 1.5, 1.8):
                for lean in (0.02, 0.04, 0.06):
                    ctl = GaitController(amp, freq, args.outer_amp, args.phase,
                                         args.wave, args.duty, args.kp, args.kd, lean)
                    r = run(model, args.seconds, ctl)
                    results.append((amp, freq, lean, r))
        stable = [x for x in results if not x[3]["fell"]]
        stable.sort(key=lambda x: -x[3]["walked_cm"])
        print(f"{len(stable)}/{len(results)} gaits stayed upright; top 10 by distance:")
        print(f"{'amp':>5} {'freq':>5} {'lean':>5} {'walked':>9} {'drift':>8}")
        for amp, freq, lean, r in stable[:10]:
            print(f"{amp:>4.0f}d {freq:>5.1f} {lean:>5.2f} {r['walked_cm']:>8.1f}c {r['drift_cm']:>7.1f}c")
        if stable:
            amp, freq, lean, r = stable[0]
            print(f"\nbest: --amp {amp} --freq {freq} --lean {lean}"
                  f"  ({r['walked_cm']:.1f} cm in {args.seconds:.0f}s)")
        return

    ctl = GaitController(args.amp, args.freq, args.outer_amp, args.phase,
                         args.wave, args.duty, args.kp, args.kd, args.lean)
    if args.gui:
        gui_run(model, ctl)
        return

    r = run(model, args.seconds, ctl, push=args.push)
    verdict = "FELL OVER" if r["fell"] else "stayed upright"
    print(
        f"amp={args.amp:.0f}deg freq={args.freq:.1f}Hz kp={args.kp:.1f} lean={args.lean:.2f}  ->  "
        f"walked {r['walked_cm']:+.1f} cm (drift {r['drift_cm']:+.1f} cm), "
        f"{r['speed_cm_s']:.1f} cm/s, {verdict}"
    )


if __name__ == "__main__":
    main()
