"""Generate tars.xml (MuJoCo MJCF) from the same dimensions as hardware/cad/tars.scad.

Bodies:
  torso       — spine block (Pi + battery + servo live here), free-floating base
  outer_pair  — the two outer slabs (stance legs), one hinge at the shoulder axle
  inner_pair  — the two inner slabs (driven walkers, 4mm longer), one hinge

MuJoCo computes inertias from the geom masses. Run:  python gen_model.py
"""

from pathlib import Path

MM = 1e-3

# ---- mirrored from tars.scad (mm) — keep in sync ----
SLAB_H, SLAB_W, SLAB_D = 240, 40, 55
SLAB_GAP = 2
INNER_EXTRA = 4
AXLE_FROM_TOP = 25
SPINE_T, SPINE_H = 12, 160
PITCH = SLAB_W + SLAB_GAP
TOTAL_W = 4 * SLAB_W + 3 * SLAB_GAP

# ---- masses (kg, estimates: PLA shells + electronics) ----
M_SPINE = 0.20   # printed spine plate + servos
M_PI = 0.10      # Raspberry Pi + chest plate, FRONT of the slabs
M_CELL = 0.10    # one 18650 cell + holder, in the BOTTOM of each outer slab
M_SLAB = 0.15    # one printed slab

MAX_TORQUE = 1.0  # N*m per joint (MG996R @ 6V rail: ~10-11 kg*cm stall = ~1.0 N*m; DS3218 upgrade ~2.0)
# hobby servos hold position stiffly: high kp, strong damping, gearbox friction
SERVO_KP, SERVO_KV, JOINT_FRICTION = 60.0, 2.0, 0.20

# stand-height of the axle when the (longer) inner pair carries the robot
AXLE_STAND = (SLAB_H + INNER_EXTRA - AXLE_FROM_TOP) * MM


FOOT_R = 6   # mm — fillet radius on the slab's bottom front/back edges:
             # flat bottom = static stability, rounded edges = smooth roll-over
             # (mirror this as a bottom edge fillet in tars.scad before printing)


def slab_geom(length_mm, y_off_mm, sign):
    """One slab = box (raised 1mm) + two rounded edge rails owning the contact."""
    y = sign * y_off_mm * MM
    z_b = (AXLE_FROM_TOP - length_mm) * MM          # true bottom of the slab
    box_len = length_mm - 1
    hx, hy, hz = SLAB_D / 2 * MM, SLAB_W / 2 * MM, box_len / 2 * MM
    zc_box = (AXLE_FROM_TOP - box_len / 2) * MM     # box bottom sits 1mm up
    r = FOOT_R * MM
    x_rail = (SLAB_D / 2 - FOOT_R) * MM
    box_mass, rail_mass = M_SLAB * 0.9, M_SLAB * 0.05
    rails = "".join(
        f'\n        <geom type="cylinder" size="{r:.4f} {hy:.4f}" '
        f'pos="{sx * x_rail:.4f} {y:.4f} {z_b + r:.4f}" euler="1.5708 0 0" mass="{rail_mass}"/>'
        for sx in (-1, 1)
    )
    return (
        f'<geom type="box" size="{hx:.4f} {hy:.4f} {hz:.4f}" '
        f'pos="0 {y:.4f} {zc_box:.4f}" mass="{box_mass}"/>' + rails
    )


def leg_pair(name, length_mm, y_off_mm, cell_mass=0.0):
    g1 = slab_geom(length_mm, y_off_mm, -1)
    g2 = slab_geom(length_mm, y_off_mm, +1)
    cells = "".join(
        f'\n        <geom type="box" size="0.010 0.012 0.035" '
        f'pos="0 {s * y_off_mm * MM:.4f} {(AXLE_FROM_TOP - length_mm + 45) * MM:.4f}" '
        f'mass="{cell_mass}" contype="0" conaffinity="0" rgba="0.2 0.5 0.3 1"/>'
        for s in (-1, 1)
    ) if cell_mass else ""
    return f"""
      <body name="{name}">
        <joint name="{name}_joint" type="hinge" axis="0 1 0" range="-2.0 2.0"
               damping="0.05" frictionloss="{JOINT_FRICTION}"/>
        {g1}
        {g2}{cells}
      </body>"""


def main():
    tx = (SLAB_D / 2 + SPINE_T / 2) * MM
    tz = (AXLE_FROM_TOP - SPINE_H / 2) * MM
    thx, thy, thz = SPINE_T / 2 * MM, TOTAL_W / 2 * MM, SPINE_H / 2 * MM

    xml = f"""<mujoco model="tars_mini">
  <compiler angle="radian"/>
  <option timestep="0.002" gravity="0 0 -9.81"/>
  <default>
    <geom friction="0.9 0.02 0.001"/>
  </default>

  <worldbody>
    <geom name="floor" type="plane" size="10 10 0.1" friction="1.0 0.02 0.001" rgba="0.85 0.82 0.75 1"/>
    <light pos="0 0 2" dir="0 0 -1"/>

    <body name="torso" pos="0 0 {AXLE_STAND + 0.001:.4f}">
      <freejoint/>
      <geom type="box" size="{thx:.4f} {thy:.4f} {thz:.4f}" pos="{tx:.4f} 0 {tz:.4f}" mass="{M_SPINE}" rgba="0.15 0.2 0.2 1"/>
      <!-- Pi on a FRONT chest plate (with the display); cells in the outer slab bottoms -->
      <geom type="box" size="0.008 0.035 0.045" pos="{-tx:.4f} 0 -0.100" mass="{M_PI}" rgba="0.3 0.35 0.35 1" contype="0" conaffinity="0"/>
      {leg_pair("outer_pair", SLAB_H, 1.5 * PITCH, cell_mass=M_CELL)}
      {leg_pair("inner_pair", SLAB_H + INNER_EXTRA, 0.5 * PITCH)}
    </body>
  </worldbody>

  <actuator>
    <position name="outer_servo" joint="outer_pair_joint" kp="{SERVO_KP}" kv="{SERVO_KV}"
              ctrlrange="-2.0 2.0" forcerange="-{MAX_TORQUE} {MAX_TORQUE}"/>
    <position name="inner_servo" joint="inner_pair_joint" kp="{SERVO_KP}" kv="{SERVO_KV}"
              ctrlrange="-2.0 2.0" forcerange="-{MAX_TORQUE} {MAX_TORQUE}"/>
  </actuator>
</mujoco>
"""
    out = Path(__file__).parent / "tars.xml"
    out.write_text(xml)
    print(f"wrote {out}  (axle stand height {AXLE_STAND:.4f} m)")


if __name__ == "__main__":
    main()
