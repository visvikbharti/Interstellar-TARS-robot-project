"""Walk the TARS-AI V3 morphology (tars_v3.xml) with a keyframe gait.

The gait is quasi-static and works like crutches: the body rests on the
ground while the legs reposition, so nothing ever balances (this is why the
real V3 needs no IMU):

  1. press the legs down on VERTICAL legs  (body rises, weight right over the feet)
  2. rotate the hinges back by the vault angle
                                             (body swings forward over the planted feet)
  3. set the body down ahead
  4. swing the unloaded legs forward to vertical (body resting), repeat

Audit (2026-09-29): the previous gait (feet planted 14 deg AHEAD, vault
overlapped with lowering) only walked at the default 2 ms time step. With
0.5 ms steps, the implicit integrator or elliptic friction cones it tipped over
within 3-9 s, because the body landed before it vaulted and the progress came
from rocking. The gait above keeps the weight over the feet while the body is
lifted, vaults with the body fully off the ground, and gives the same result at
every solver setting in --robust (time steps 2 ms to 0.25 ms, three
integrators, both friction cones, floor friction 0.5-1.3, 20% weaker servos,
body mass -10% / +20%).

The fall test is strict: the body AND both legs must stay within 45 deg of
vertical and the axle above 150 mm (standing: 219 mm).

Usage:
  python v3_sim.py                  # headless, prints distance walked
  python v3_sim.py --robust         # same gait across solver/physics settings
  python v3_sim.py --sweep          # tune vault angle / lift / tempo (checked at 2 ms AND 0.5 ms elliptic)
  mjpython v3_sim.py --gui          # watch (runs until you close the window)
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import mujoco

HERE = Path(__file__).parent
LIFT_TRAVEL = 0.035
MAX_TILT_DEG = 45.0      # body and legs: anything beyond this is a fall
MIN_AXLE_Z = 0.150       # m; the axle stands at 0.219 m

DEFAULTS = dict(vault_deg=12.0, lift=0.7, tempo=1.0)

# Solver and physics settings the gait must survive (--robust)
ROBUST_MATRIX = [
    dict(),
    dict(dt=0.001),
    dict(dt=0.0005),
    dict(dt=0.00025),
    dict(integrator="implicitfast"),
    dict(integrator="implicitfast", dt=0.0005),
    dict(integrator="RK4"),
    dict(cone="elliptic"),
    dict(cone="elliptic", dt=0.0005),
    dict(floor_mu=0.5),
    dict(floor_mu=0.7, dt=0.0005),
    dict(floor_mu=1.3),
    dict(torque=0.8, dt=0.0005),
    dict(mass=1.2, dt=0.0005),
    dict(mass=0.9, dt=0.0005),
]


def load():
    path = HERE / "tars_v3.xml"
    if not path.exists():
        raise SystemExit("tars_v3.xml missing — run: python v3_model.py")
    return mujoco.MjModel.from_xml_path(str(path))


def build_model(dt=0.002, integrator="Euler", cone="pyramidal", floor_mu=1.0,
                torque=1.0, mass=1.0):
    """tars_v3.xml with a different solver setup or physics, for --robust.
    torque scales the swing servos' torque limit; mass scales the body."""
    path = HERE / "tars_v3.xml"
    if not path.exists():
        raise SystemExit("tars_v3.xml missing — run: python v3_model.py")
    xml = path.read_text()
    xml = xml.replace('timestep="0.002"',
                      f'timestep="{dt}" integrator="{integrator}" cone="{cone}"')
    xml = xml.replace('friction="1.0 0.02 0.001" rgba', f'friction="{floor_mu} 0.02 0.001" rgba')
    xml = xml.replace('forcerange="-1.0 1.0"', f'forcerange="-{torque} {torque}"')
    model = mujoco.MjModel.from_xml_string(xml)
    if mass != 1.0:
        b = model.body("body").id
        model.body_mass[b] *= mass
        model.body_inertia[b] *= mass
    return model


def quat_tilt_deg(q) -> float:
    """Angle between a body's up-axis and world up, in degrees (q = w, x, y, z)."""
    w, x, y, z = q
    up_z = 1 - 2 * (x * x + y * y)
    return math.degrees(math.acos(max(-1.0, min(1.0, up_z))))


def tilt_deg(qpos) -> float:
    return quat_tilt_deg(qpos[3:7])


def worst_tilt_deg(model, data) -> float:
    """Largest tilt of the body and the two legs."""
    return max(quat_tilt_deg(data.xquat[model.body(n).id])
               for n in ("body", "left_leg", "right_leg"))


def fallen(model, data) -> bool:
    return worst_tilt_deg(model, data) > MAX_TILT_DEG or data.qpos[2] < MIN_AXLE_Z


def keyframes(vault_deg: float, lift: float, tempo: float):
    """(lift 0..1, swing rad, duration s) — applied to both legs together.
    Positive swing = legs back relative to the body (feet behind the axle)."""
    v = math.radians(vault_deg)
    return [
        (lift, 0.0, 0.40 * tempo),   # 1 press down on vertical legs -> body rises
        (lift, v, 0.60 * tempo),     # 2 vault: body swings forward over the planted feet
        (0.0, v, 0.35 * tempo),      # 3 set the body down ahead
        (0.0, 0.0, 0.45 * tempo),    # 4 swing the unloaded legs forward to vertical
    ]


PHASES = ["press down, body rises", "vault forward", "set down", "swing legs forward"]


class KeyframeGait:
    def __init__(self, frames):
        self.frames = frames
        self.cycle_t = sum(f[2] for f in frames)

    def phase(self, t: float) -> int:
        u = t % self.cycle_t
        for i, (_, _, dur) in enumerate(self.frames):
            if u < dur:
                return i
            u -= dur
        return len(self.frames) - 1

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
    body = model.body("body").id
    x0, y0 = data.subtree_com[body][0], data.qpos[1]
    t0 = data.time
    fell, worst = False, 0.0
    while data.time - t0 < seconds:
        lift, swing = gait.targets(data.time - t0)
        apply(data, act, lift, swing)
        mujoco.mj_step(model, data)
        worst = max(worst, worst_tilt_deg(model, data))
        if fallen(model, data):
            fell = True
            break
    walked = data.subtree_com[body][0] - x0     # centre of mass, not the rocking axle
    t = data.time - t0
    cycles = seconds / gait.cycle_t
    return {
        "walked_cm": 100 * walked,
        "drift_cm": 100 * (data.qpos[1] - y0),
        "fell": fell,
        "fell_at_s": t if fell else None,
        "worst_tilt_deg": worst,
        "cm_per_cycle": 100 * walked / cycles if not fell else 0.0,
        "speed_cm_s": 100 * walked / seconds if not fell else 0.0,
    }


def robust(gait: KeyframeGait, seconds: float) -> bool:
    """Run the same gait across ROBUST_MATRIX; True if it never falls."""
    ok = True
    print(f"{'setting':44s} {'walked':>8} {'worst tilt':>11}  result")
    for cfg in ROBUST_MATRIX:
        r = run(build_model(**cfg), gait, seconds)
        name = ", ".join(f"{k}={v}" for k, v in cfg.items()) or "as built (2 ms, Euler, pyramidal)"
        verdict = f"FELL at {r['fell_at_s']:.1f} s" if r["fell"] else "upright"
        print(f"{name:44s} {r['walked_cm']:7.1f}c {r['worst_tilt_deg']:9.1f}d   {verdict}")
        ok &= not r["fell"]
    print("\nALL SETTINGS UPRIGHT" if ok else "\nSOME SETTINGS FELL — not a robust gait")
    return ok


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
                if fallen(model, data):
                    print(f"fell at x={data.qpos[0]*100:+.1f}cm — resetting")
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
    ap.add_argument("--robust", action="store_true", help="run the gait across solver/physics settings")
    ap.add_argument("--seconds", type=float, default=15.0)
    ap.add_argument("--vault-deg", type=float, default=DEFAULTS["vault_deg"],
                    help="how far the legs rotate back while the body is lifted")
    ap.add_argument("--lift", type=float, default=DEFAULTS["lift"], help="lift height fraction of 35mm travel")
    ap.add_argument("--tempo", type=float, default=DEFAULTS["tempo"], help="cycle time scale (1.0 = 1.8 s/step)")
    ap.add_argument("--dt", type=float, default=0.002, help="MuJoCo time step, s")
    ap.add_argument("--integrator", default="Euler", choices=("Euler", "implicitfast", "RK4"))
    ap.add_argument("--cone", default="pyramidal", choices=("pyramidal", "elliptic"))
    args = ap.parse_args()

    gait = KeyframeGait(keyframes(args.vault_deg, args.lift, args.tempo))

    if args.robust:
        sys.exit(0 if robust(gait, args.seconds) else 1)

    if args.sweep:
        # every candidate is checked at 2 ms AND at 0.5 ms with elliptic cones
        checks = (dict(), dict(dt=0.0005, cone="elliptic"))
        results = []
        for vault in (8, 10, 12, 14, 16, 20):
            for lift in (0.5, 0.7, 0.9):
                for tempo in (0.8, 1.0, 1.4):
                    g = KeyframeGait(keyframes(vault, lift, tempo))
                    rs = [run(build_model(**c), g, args.seconds) for c in checks]
                    results.append(((vault, lift, tempo), rs))
        ok = [x for x in results if not any(r["fell"] for r in x[1])]
        ok.sort(key=lambda x: -min(r["walked_cm"] for r in x[1]))
        print(f"{len(ok)}/{len(results)} stayed upright at both settings; top 10:")
        print(f"{'vault':>6} {'lift':>5} {'tempo':>6} {'walked (2 ms / 0.5 ms ell.)':>28} {'tilt':>6}")
        for (vault, lift, tempo), rs in ok[:10]:
            print(f"{vault:>5.0f}d {lift:>5.1f} {tempo:>6.1f} {rs[0]['walked_cm']:>12.1f}c / {rs[1]['walked_cm']:>6.1f}c "
                  f"{max(r['worst_tilt_deg'] for r in rs):>6.1f}d")
        return

    model = build_model(dt=args.dt, integrator=args.integrator, cone=args.cone)
    if args.gui:
        gui_run(model, gait)
        return
    r = run(model, gait, args.seconds)
    verdict = f"FELL at {r['fell_at_s']:.1f} s" if r["fell"] else "stayed upright"
    print(f"vault={args.vault_deg:.0f}deg lift={args.lift:.1f} tempo={args.tempo:.1f}  ->  "
          f"walked {r['walked_cm']:+.1f}cm ({r['cm_per_cycle']:.1f}cm/cycle, "
          f"{r['speed_cm_s']:.1f}cm/s), drift {r['drift_cm']:+.1f}cm, worst tilt {r['worst_tilt_deg']:.1f}deg, {verdict}")


if __name__ == "__main__":
    main()
