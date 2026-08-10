"""Walk the TARS-AI V3 morphology (tars_v3.xml) with a keyframe gait.

The gait is quasi-static — the body rests on the ground while the legs
reposition, so nothing ever balances (this is why the real V3 needs no IMU):

  1. swing the unloaded legs forward (body sitting on the ground)
  2. press the legs down            (body rises off the ground)
  3. rotate the hinges              (body vaults forward over the planted feet)
  4. set the body down ahead, unload the legs, repeat

Usage:
  python v3_sim.py                  # headless, prints distance walked
  python v3_sim.py --sweep          # tune step/vault angles
  mjpython v3_sim.py --gui          # watch (runs until you close the window)
"""

from __future__ import annotations

import argparse
import math
import time
from pathlib import Path

import mujoco

HERE = Path(__file__).parent
LIFT_TRAVEL = 0.035


def load():
    path = HERE / "tars_v3.xml"
    if not path.exists():
        raise SystemExit("tars_v3.xml missing — run: python v3_model.py")
    return mujoco.MjModel.from_xml_path(str(path))


def tilt_deg(qpos) -> float:
    w, x, y, z = qpos[3:7]
    up_z = 1 - 2 * (x * x + y * y)
    return math.degrees(math.acos(max(-1.0, min(1.0, up_z))))


def keyframes(step_deg: float, back_deg: float, tempo: float, lift: float = 0.5):
    """(lift 0..1, swing rad, duration s) — applied to both legs together.
    Small movements + overlapping vault/lower = the body lands mid-swing,
    so the inverted-pendulum fall is only a few millimetres."""
    s, b = -math.radians(step_deg), math.radians(back_deg)  # feet plant slightly AHEAD;
    # the body vaults forward over them — a gentle controlled topple caught by the ground
    return [
        (0.0, s, 0.35 * tempo),    # 1 swing unloaded legs forward
        (lift, s, 0.30 * tempo),   # 2 press down -> body rises, pendulum starts
        (0.0, b, 0.45 * tempo),    # 3 vault forward AND lower together
        (0.0, 0.0, 0.25 * tempo),  # 4 recover to neutral
    ]


class KeyframeGait:
    def __init__(self, frames):
        self.frames = frames
        self.cycle_t = sum(f[2] for f in frames)

    def targets(self, t: float) -> tuple[float, float]:
        """-> (lift_ctrl, swing_ctrl) with smooth ease between keyframes."""
        u = t % self.cycle_t
        prev = self.frames[-1]
        for lift, swing, dur in self.frames:
            if u < dur:
                a = u / dur
                a = a * a * (3 - 2 * a)  # smoothstep ease
                l = prev[0] + (lift - prev[0]) * a
                s = prev[1] + (swing - prev[1]) * a
                return -l * LIFT_TRAVEL, s
            u -= dur
            prev = (lift, swing, dur)
        return -self.frames[-1][0] * LIFT_TRAVEL, self.frames[-1][1]


def actuators(model):
    return {n: model.actuator(n).id for n in
            ("left_lift", "right_lift", "left_swing", "right_swing")}


def apply(data, act, lift_ctrl, swing_ctrl):
    data.ctrl[act["left_lift"]] = data.ctrl[act["right_lift"]] = lift_ctrl
    data.ctrl[act["left_swing"]] = data.ctrl[act["right_swing"]] = swing_ctrl


def run(model, gait: KeyframeGait, seconds: float) -> dict:
    data = mujoco.MjData(model)
    act = actuators(model)
    while data.time < 0.5:                      # settle
        apply(data, act, 0.0, 0.0)
        mujoco.mj_step(model, data)
    x0, y0 = data.qpos[0], data.qpos[1]
    t0 = data.time
    fell = False
    while data.time - t0 < seconds:
        lift, swing = gait.targets(data.time - t0)
        apply(data, act, lift, swing)
        mujoco.mj_step(model, data)
        if tilt_deg(data.qpos) > 50:
            fell = True
            break
    walked = data.qpos[0] - x0
    cycles = seconds / gait.cycle_t
    return {
        "walked_cm": 100 * walked,
        "drift_cm": 100 * (data.qpos[1] - y0),
        "fell": fell,
        "cm_per_cycle": 100 * walked / cycles if not fell else 0.0,
        "speed_cm_s": 100 * walked / seconds if not fell else 0.0,
    }


def gui_run(model, gait: KeyframeGait) -> None:
    from mujoco import viewer as mj_viewer

    data = mujoco.MjData(model)
    act = actuators(model)
    steps_per_frame = max(1, round(1 / 60 / model.opt.timestep))
    with mj_viewer.launch_passive(model, data) as v:
        v.cam.distance, v.cam.elevation, v.cam.azimuth = 1.5, -12, 125
        wall0 = time.monotonic()
        while v.is_running():
            for _ in range(steps_per_frame):
                if data.time < 0.5:
                    apply(data, act, 0.0, 0.0)
                else:
                    lift, swing = gait.targets(data.time - 0.5)
                    apply(data, act, lift, swing)
                mujoco.mj_step(model, data)
                if tilt_deg(data.qpos) > 60:
                    print(f"tipped at x={data.qpos[0]*100:+.1f}cm — resetting")
                    mujoco.mj_resetData(model, data)
                    wall0 = time.monotonic()
                    break
            v.cam.lookat[0] = data.qpos[0]
            v.cam.lookat[2] = 0.15
            v.sync()
            lag = data.time - (time.monotonic() - wall0)
            if lag > 0:
                time.sleep(lag)
        print(f"viewer closed — walked to x={data.qpos[0]*100:+.1f}cm")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--seconds", type=float, default=15.0)
    ap.add_argument("--step-deg", type=float, default=14.0, help="how far ahead the feet plant")
    ap.add_argument("--back-deg", type=float, default=4.0, help="how far past vertical the vault carries")
    ap.add_argument("--tempo", type=float, default=0.6, help="cycle time scale (1.0 = 1.35s/step)")
    ap.add_argument("--lift", type=float, default=0.3, help="lift height fraction of 35mm travel")
    args = ap.parse_args()

    model = load()

    if args.sweep:
        results = []
        for step in (-24, -18, -14, -10, 10, 14, 18, 24):
            for back in (-12, -8, -4, 4, 8, 12):
                for tempo in (0.6, 1.0, 1.5):
                    for lift in (0.3, 0.6):
                        g = KeyframeGait(keyframes(step, back, tempo, lift))
                        r = run(model, g, args.seconds)
                        results.append(((step, back, tempo, lift), r))
        ok = [x for x in results if not x[1]["fell"]]
        ok.sort(key=lambda x: -abs(x[1]["walked_cm"]))
        print(f"{len(ok)}/{len(results)} stayed upright; top 10:")
        print(f"{'step':>5} {'back':>5} {'tempo':>6} {'lift':>5} {'walked':>9} {'cm/cyc':>7} {'drift':>7}")
        for (step, back, tempo, lift), r in ok[:10]:
            print(f"{step:>4.0f}d {back:>4.0f}d {tempo:>6.1f} {lift:>5.1f} {r['walked_cm']:>8.1f}c "
                  f"{r['cm_per_cycle']:>6.1f}c {r['drift_cm']:>6.1f}c")
        if ok:
            (s, b, tp, lf), r = ok[0]
            print(f"\nbest: --step-deg {s} --back-deg {b} --tempo {tp} --lift {lf}"
                  f"  ({r['walked_cm']:.1f}cm in {args.seconds:.0f}s, {r['speed_cm_s']:.1f}cm/s)")
        return

    gait = KeyframeGait(keyframes(args.step_deg, args.back_deg, args.tempo, args.lift))
    if args.gui:
        gui_run(model, gait)
        return
    r = run(model, gait, args.seconds)
    verdict = "TIPPED OVER" if r["fell"] else "stayed upright"
    print(f"step={args.step_deg:.0f}deg back={args.back_deg:.0f}deg tempo={args.tempo:.1f}  ->  "
          f"walked {r['walked_cm']:+.1f}cm ({r['cm_per_cycle']:.1f}cm/cycle, "
          f"{r['speed_cm_s']:.1f}cm/s), drift {r['drift_cm']:+.1f}cm, {verdict}")


if __name__ == "__main__":
    main()
