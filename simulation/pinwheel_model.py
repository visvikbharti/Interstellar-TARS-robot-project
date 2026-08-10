"""Generate tars_wheel.xml — TARS's Miller's-planet WHEEL MODE.

The movie robot splays its four slabs into a pinwheel and cartwheels. The
research-proven mechanism (TARS3D, arXiv 2510.05001) is a **double rimless
wheel**: each slab is driven independently around the shoulder axle, and the
two slab pairs run 90 degrees out of phase — the robot rolls in 90 degree
tip-overs, alternating support between the pairs.

Hardware note: this needs 4 independently-driven slabs on one axle with
continuous rotation — serial-bus servos (LX-16A class) planned for v2,
mounted in a central hub. That is the **v2 hardware** goal;
the v1 build (TARS-AI V3 architecture) cannot do wheel mode.

Run:  python pinwheel_model.py
"""

from pathlib import Path

MM = 1e-3

SLAB_W, SLAB_D, SLAB_H = 40, 55, 240
GAP = 2
AXLE_FROM_TOP = 25          # pivot 25mm from slab top -> long spoke = 215mm
SPOKE = (SLAB_H - AXLE_FROM_TOP) * MM

HUB_R = 15 * MM             # central hub (holds the bus servos + electronics)
M_HUB = 0.45
M_SLAB = 0.21               # slabs carry their own battery cells in v2

SERVO_TORQUE = 1.7          # N*m  (LX-16A: 17 kg*cm)
SERVO_MAX_W = 7.0           # rad/s no-load-ish

SLAB_Y = [-1.5, -0.5, 0.5, 1.5]  # x (SLAB_W + GAP)


def slab(i):
    y = SLAB_Y[i] * (SLAB_W + GAP) * MM
    box_len = SLAB_H - 1
    hx, hy, hz = SLAB_D / 2 * MM, SLAB_W / 2 * MM, box_len / 2 * MM
    zc = (AXLE_FROM_TOP - box_len / 2) * MM     # box bottom sits 1mm up
    r = 6 * MM
    x_rail = SLAB_D / 2 * MM - r
    z_b = (AXLE_FROM_TOP - SLAB_H) * MM
    rails = "".join(
        f'\n        <geom type="cylinder" size="{r:.4f} {hy:.4f}" '
        f'pos="{sx * x_rail:.4f} 0 {z_b + r:.4f}" euler="1.5708 0 0" mass="0.005" '
        f'friction="1.3 0.02 0.001"/>'
        for sx in (-1, 1)
    )
    return f"""
      <body name="slab{i}" pos="0 {y:.4f} 0">
        <joint name="slab{i}_hinge" type="hinge" axis="0 1 0" limited="false"
               damping="0.05" frictionloss="0.15"/>
        <geom type="box" size="{hx:.4f} {hy:.4f} {hz:.4f}" pos="0 0 {zc:.4f}" mass="{M_SLAB}"/>{rails}
      </body>"""


def main():
    total_w = (4 * SLAB_W + 3 * GAP) * MM
    xml = f"""<mujoco model="tars_wheel">
  <compiler angle="radian"/>
  <option timestep="0.002" gravity="0 0 -9.81"/>
  <default>
    <geom friction="0.9 0.02 0.001"/>
  </default>

  <worldbody>
    <geom name="floor" type="plane" size="30 30 0.1" friction="1.0 0.02 0.001" rgba="0.85 0.82 0.75 1"/>
    <light pos="0 0 3" dir="0 0 -1"/>

    <body name="hub" pos="0 0 {SPOKE + 0.002:.4f}">
      <freejoint/>
      <geom type="cylinder" size="{HUB_R:.4f} {total_w / 2:.4f}" euler="1.5708 0 0"
            mass="{M_HUB}" rgba="0.2 0.22 0.25 1"/>
      {slab(0)}{slab(1)}{slab(2)}{slab(3)}
    </body>
  </worldbody>

  <actuator>
    <!-- intvelocity = bus servo in continuous mode: tracks a position target
         that advances at the commanded velocity; HOLDS position at cmd=0 -->
    <intvelocity name="w0" joint="slab0_hinge" kp="60" kv="3" actrange="-1000 1000" ctrlrange="-{SERVO_MAX_W} {SERVO_MAX_W}" forcerange="-{SERVO_TORQUE} {SERVO_TORQUE}"/>
    <intvelocity name="w1" joint="slab1_hinge" kp="60" kv="3" actrange="-1000 1000" ctrlrange="-{SERVO_MAX_W} {SERVO_MAX_W}" forcerange="-{SERVO_TORQUE} {SERVO_TORQUE}"/>
    <intvelocity name="w2" joint="slab2_hinge" kp="60" kv="3" actrange="-1000 1000" ctrlrange="-{SERVO_MAX_W} {SERVO_MAX_W}" forcerange="-{SERVO_TORQUE} {SERVO_TORQUE}"/>
    <intvelocity name="w3" joint="slab3_hinge" kp="60" kv="3" actrange="-1000 1000" ctrlrange="-{SERVO_MAX_W} {SERVO_MAX_W}" forcerange="-{SERVO_TORQUE} {SERVO_TORQUE}"/>
  </actuator>
</mujoco>
"""
    out = Path(__file__).parent / "tars_wheel.xml"
    out.write_text(xml)
    print(f"wrote {out}  (spoke length {SPOKE:.3f}m)")


if __name__ == "__main__":
    main()
