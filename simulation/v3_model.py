"""Generate tars_v3.xml — the TARS-AI V3 / Charlie Diaz morphology.

Architecture (the proven one):
  body       — the central chassis (looks like the two middle slabs), holds
               Pi + battery + servos. Its bottom TOUCHES THE GROUND between
               steps, so the robot never has to balance.
  left_leg / right_leg — outer slabs, each with TWO joints:
               lift  (slide, vertical): pushes the leg down -> raises the body
               swing (hinge, pitch):    swings the leg fore/aft

Walking = lift body on legs -> rotate hinges (body vaults over planted feet)
-> set body down -> swing unloaded legs forward -> repeat. Quasi-static.

Run:  python v3_model.py
"""

from pathlib import Path

MM = 1e-3

# ---- dimensions (mm) — mirror into hardware/cad/tars.scad v0.3 ----
SLAB_W, SLAB_D = 40, 55
LEG_H = 240
BODY_EXTRA = 4          # body is 4mm LONGER than legs at lift=0 (body carries)
BODY_H = LEG_H + BODY_EXTRA
BODY_W = 2 * SLAB_W + 2  # two middle slabs + groove = one printed chassis
GAP = 2
AXLE_FROM_TOP = 25       # axle below the slab tops
LIFT_TRAVEL = 0.035      # legs can push 35mm below the body bottom

FOOT_R = 6               # rounded bottom edge rails (see gait findings)

# ---- masses (kg) ----
M_BODY = 0.95            # chassis + Pi + battery + 4 servos (all central & low)
M_LEG = 0.16             # one printed slab + bearing

HINGE_TORQUE = 2.5       # N*m  (MG996R-class)
LIFT_FORCE = 55.0        # N    (MG996R 9.4kg*cm through a ~15mm crank arm)

AXLE_Z = (LEG_H - AXLE_FROM_TOP + BODY_EXTRA) * MM   # axle height above body bottom
LEG_Y = (BODY_W / 2 + GAP + SLAB_W / 2) * MM         # leg centreline offset


def rails(hy, z_b, x_half):
    r = FOOT_R * MM
    x_rail = (x_half - FOOT_R * MM)
    return "".join(
        f'\n        <geom type="cylinder" size="{r:.4f} {hy:.4f}" '
        f'pos="{sx * x_rail:.4f} 0 {z_b + r:.4f}" euler="1.5708 0 0" mass="0.005" friction="1.3 0.02 0.001"/>'
        for sx in (-1, 1)
    )


def leg(name, y_sign):
    hx, hy, hz = SLAB_D / 2 * MM, SLAB_W / 2 * MM, (LEG_H - 1) / 2 * MM
    z_top = AXLE_FROM_TOP * MM                 # leg top relative to axle
    zc = z_top - (LEG_H - 1) / 2 * MM          # box centre (bottom 1mm up, rails own contact)
    z_b = z_top - LEG_H * MM                   # true leg bottom
    return f"""
      <body name="{name}" pos="0 {y_sign * LEG_Y:.4f} 0">
        <joint name="{name}_lift" type="slide" axis="0 0 1" range="-{LIFT_TRAVEL} 0"
               damping="8" frictionloss="4"/>
        <joint name="{name}_swing" type="hinge" axis="0 1 0" range="-1.75 1.75"
               damping="0.05" frictionloss="0.2"/>
        <geom type="box" size="{hx:.4f} {hy:.4f} {hz:.4f}" pos="0 0 {zc:.4f}" mass="{M_LEG}"/>{rails(hy, z_b, hx)}
      </body>"""


def main():
    bhx, bhy = SLAB_D / 2 * MM, BODY_W / 2 * MM
    bhz = (BODY_H - 1) / 2 * MM
    b_zc = -AXLE_Z + 1 * MM + bhz              # body box centre (z rel. axle-origin... )
    # body frame origin = axle height; body spans from -AXLE_Z (bottom) upward
    z_bot = -AXLE_Z
    bz_c = z_bot + 1 * MM + bhz

    xml = f"""<mujoco model="tars_v3">
  <compiler angle="radian"/>
  <option timestep="0.002" gravity="0 0 -9.81"/>
  <default>
    <geom friction="0.9 0.02 0.001"/>
  </default>

  <worldbody>
    <geom name="floor" type="plane" size="10 10 0.1" friction="1.0 0.02 0.001" rgba="0.85 0.82 0.75 1"/>
    <light pos="0 0 2" dir="0 0 -1"/>

    <body name="body" pos="0 0 {AXLE_Z + 0.001:.4f}">
      <freejoint/>
      <geom type="box" size="{bhx:.4f} {bhy:.4f} {bhz:.4f}" pos="0 0 {bz_c:.4f}" mass="{M_BODY * 0.55:.3f}" rgba="0.25 0.28 0.3 1"/>{rails(bhy, z_bot, bhx)}
      <!-- battery + Pi modelled low in the chassis -->
      <geom type="box" size="0.020 0.030 0.040" pos="0 0 {z_bot + 0.055:.4f}" mass="{M_BODY * 0.45:.3f}" contype="0" conaffinity="0" rgba="0.2 0.5 0.3 1"/>
      {leg("left_leg", -1)}
      {leg("right_leg", +1)}
    </body>
  </worldbody>

  <actuator>
    <position name="left_lift"   joint="left_leg_lift"   kp="3000" kv="80"
              ctrlrange="-{LIFT_TRAVEL} 0" forcerange="-{LIFT_FORCE} {LIFT_FORCE}"/>
    <position name="right_lift"  joint="right_leg_lift"  kp="3000" kv="80"
              ctrlrange="-{LIFT_TRAVEL} 0" forcerange="-{LIFT_FORCE} {LIFT_FORCE}"/>
    <position name="left_swing"  joint="left_leg_swing"  kp="60" kv="2"
              ctrlrange="-1.75 1.75" forcerange="-{HINGE_TORQUE} {HINGE_TORQUE}"/>
    <position name="right_swing" joint="right_leg_swing" kp="60" kv="2"
              ctrlrange="-1.75 1.75" forcerange="-{HINGE_TORQUE} {HINGE_TORQUE}"/>
  </actuator>
</mujoco>
"""
    out = Path(__file__).parent / "tars_v3.xml"
    out.write_text(xml)
    print(f"wrote {out}")
    print(f"body stands {AXLE_Z:.3f}m at the axle; legs can lift it {LIFT_TRAVEL*1000:.0f}mm")


if __name__ == "__main__":
    main()
