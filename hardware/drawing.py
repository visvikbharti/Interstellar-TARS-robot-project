"""Dimensioned three-view engineering drawing of the TARS mini chassis (v0.3.1).

Renders hardware/tars_drawing.png (landscape, 160 dpi). Every dimension is read
from hardware/cad/tars.scad, whose master numbers mirror simulation/v3_model.py,
so the drawing cannot drift from the model.

Views (all mm, not to scale): FRONT (the display side, -x, looking towards +x),
SIDE (from +y: the right leg's outer face, the body behind it in hidden lines)
and TOP (looking down, display side at the bottom of the page).

Needs matplotlib (pip install matplotlib). Run from the project root:
    python hardware/drawing.py
"""
from __future__ import annotations

import os
import re

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
SCAD = os.path.join(HERE, "cad", "tars.scad")
OUT_PNG = os.path.join(HERE, "tars_drawing.png")

# ----------------------------------------------------------------------------
# Governing numbers, read from tars.scad (plain `name = number;` assignments)
# ----------------------------------------------------------------------------
_src = open(SCAD, encoding="utf-8").read()
_vals = {m.group(1): float(m.group(2))
         for m in re.finditer(r"\b([a-z_]+)\s*=\s*(-?[0-9]+(?:\.[0-9]+)?)\s*;", _src)}


def v(name: str) -> float:
    if name not in _vals:
        raise SystemExit(f"tars.scad has no numeric '{name}'")
    return _vals[name]


SLAB_W, SLAB_D, LEG_H = v("slab_w"), v("slab_d"), v("leg_h")
BODY_EXTRA, GAP = v("body_extra"), v("gap")
BODY_H = LEG_H + BODY_EXTRA                   # body_h = leg_h + body_extra
BODY_W = 2 * SLAB_W + GAP                     # body_w = 2 * slab_w + gap
AXLE_FROM_TOP, AXLE_D, LIFT = v("axle_from_top"), v("axle_d"), v("lift_travel")
FOOT_R, EDGE_R, WALL = v("foot_r"), v("chamfer"), v("wall")
BRG_OD, BRG_W = v("brg_od"), v("brg_w")
SERVO_L, SERVO_W, SERVO_H = v("servo_l"), v("servo_w"), v("servo_h")
DISP_W, DISP_H = v("disp_w"), v("disp_h")

AXLE_Z = BODY_H - AXLE_FROM_TOP               # 219 above the ground
LEG_Y = BODY_W / 2 + GAP + SLAB_W / 2         # 63, leg centre
TOTAL_W = BODY_W + 2 * (GAP + SLAB_W)         # 166
AXLE_L = TOTAL_W + 10                         # 176, 5 mm proud each side
DISP_Z0 = BODY_H - 35 - DISP_H                # display window 127 .. 209
GRILLE_Z = [45 + 6 * k for k in range(3)]     # 7 x 3 holes, 3 mm, 6 mm pitch
GRILLE_U = [6 * k for k in range(-3, 4)]
BAY_Z0 = AXLE_Z - SERVO_H + 8                 # servo bays 184.1 .. 227


def panel_rows(h: float, z0: float):
    """tars.scad face_panels: 3 rows of (h-40)/3-6, 6 apart, from 15 up."""
    ph = (h - 40) / 3 - 6
    return [(z0 + 15 + i * (ph + 6), z0 + 15 + i * (ph + 6) + ph) for i in range(3)]


INK = "#141414"       # primary linework
MID = "#4d4d4d"       # secondary linework and leaders
GHOST = "#8c8c8c"     # phantom and hidden lines
FAINT = "#a9a9a9"     # tangent edges of rounded corners
ACC = "#0E63B4"       # accent: dimension lines only
HIDDEN = (0, (4, 2.5))
CENTRE = (0, (10, 3, 2, 3))

# ----------------------------------------------------------------------------
# Drafting helpers (as in the quadrotor project's hardware/drawing.py)
# ----------------------------------------------------------------------------


def dim(ax, p1, p2, offset, text, *, text_pos=None, text_rot=None, fs=8.2,
        gap1=1.5, gap2=1.5, over=2.2, tshift=4.2, outside=False, arrow_len=7.0):
    """Linear dimension between p1 and p2, dimension line offset perpendicular."""
    p1 = np.asarray(p1, float)
    p2 = np.asarray(p2, float)
    u = (p2 - p1) / np.hypot(*(p2 - p1))
    n = np.array([-u[1], u[0]])
    q1, q2 = p1 + offset * n, p2 + offset * n
    ne = n * (1.0 if offset >= 0 else -1.0)
    for p, q, g in ((p1, q1, gap1), (p2, q2, gap2)):
        a, b = p + g * ne, q + over * ne
        ax.plot([a[0], b[0]], [a[1], b[1]], color=ACC, lw=0.7, zorder=6)
    kw = dict(color=ACC, lw=0.9, mutation_scale=10, shrinkA=0, shrinkB=0)
    if outside:
        ax.plot([q1[0], q2[0]], [q1[1], q2[1]], color=ACC, lw=0.9, zorder=6)
        for q, sgn in ((q1, -1.0), (q2, 1.0)):
            ax.annotate("", xy=q, xytext=q + sgn * arrow_len * u, zorder=6,
                        arrowprops=dict(arrowstyle="-|>", **kw))
    else:
        ax.annotate("", xy=q1, xytext=q2, zorder=6, arrowprops=dict(arrowstyle="<|-|>", **kw))
    if text_pos is None:
        text_pos = 0.5 * (q1 + q2) + tshift * ne
    if text_rot is None:
        ang = np.degrees(np.arctan2(u[1], u[0]))
        text_rot = ang - 180 if ang > 90.01 else ang + 180 if ang < -90.01 else ang
    ax.text(text_pos[0], text_pos[1], text, rotation=text_rot, fontsize=fs, color=ACC,
            ha="center", va="center", zorder=8, bbox=dict(fc="white", ec="none", pad=0.6))


def leader(ax, tip, txt_xy, text, *, fs=7.0, ha="left", color=MID):
    ax.annotate(text, xy=tip, xytext=txt_xy, fontsize=fs, color=INK, ha=ha, va="center",
                zorder=8, bbox=dict(fc="white", ec="none", pad=0.4),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=0.8, mutation_scale=8,
                                shrinkA=1, shrinkB=1))


def rrect(ax, x0, y0, w, h, r, *, ec=INK, lw=1.3, ls="solid", fc="white", z=3):
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))


def rect(ax, x0, y0, w, h, *, ec=INK, lw=1.3, ls="solid", fc="none", z=3):
    ax.add_patch(Rectangle((x0, y0), w, h, fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))


def hline(ax, x0, x1, y, **kw):
    ax.plot([x0, x1], [y, y], **kw)


def vline(ax, x, y0, y1, **kw):
    ax.plot([x, x], [y0, y1], **kw)


def slab_front(ax, u0, w, z0, h):
    """A slab seen from the front: outline with rounded foot, tangent edges of the rounded corners."""
    rrect(ax, u0, z0, w, h, 0.01)
    hline(ax, u0, u0 + w, z0 + FOOT_R, color=FAINT, lw=0.7, zorder=3.5)           # foot round-over starts
    for x in (u0 + EDGE_R, u0 + w - EDGE_R):                                      # vertical edges, R4
        vline(ax, x, z0, z0 + h, color=FAINT, lw=0.7, zorder=3.5)


def foot_outline(ax, x0, w, z0, h, r, *, z=3):
    """A slab seen from the side: square top, bottom edges rounded to r (tars.scad foot_profile)."""
    a1 = np.linspace(np.pi, 1.5 * np.pi, 16)
    a2 = np.linspace(1.5 * np.pi, 2 * np.pi, 16)
    xs = np.concatenate([[x0, x0], x0 + r + r * np.cos(a1), x0 + w - r + r * np.cos(a2), [x0 + w, x0]])
    ys = np.concatenate([[z0 + h, z0 + r], z0 + r + r * np.sin(a1), z0 + r + r * np.sin(a2), [z0 + h, z0 + h]])
    ax.fill(xs, ys, fc="white", ec="none", zorder=z)
    ax.plot(xs, ys, color=INK, lw=1.3, zorder=z + 0.05)


def slot(ax, cx, z_top, z_bot, d, **kw):
    """A slot of width d from z_bot to z_top, round ends (side view)."""
    r = d / 2
    th = np.linspace(0, np.pi, 40)
    xs = np.concatenate([cx + r * np.cos(th), cx - r * np.cos(th)])
    ys = np.concatenate([z_top + r * np.sin(th), z_bot - r * np.sin(th)])
    ax.plot(np.append(xs, xs[0]), np.append(ys, ys[0]), **kw)


def view(ax, xlim, ylim):
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)


# ----------------------------------------------------------------------------
# Figure & sheet
# ----------------------------------------------------------------------------
fig = plt.figure(figsize=(16.5, 10.4), facecolor="white")
fig.add_artist(Rectangle((0.005, 0.005), 0.990, 0.990, transform=fig.transFigure,
                         fill=False, ec=INK, lw=1.5))

# ============================================================================
# FRONT VIEW  (page x = -y: seen from the front, +y is on the viewer's left)
# ============================================================================
ax = fig.add_axes([0.012, 0.118, 0.345, 0.862])
view(ax, (-150, 118), (-44, 318))

ground_kw = dict(color=GHOST, lw=0.9, ls=CENTRE, zorder=2)
hline(ax, -118, 112, 0, **ground_kw)
ax.text(108, -6.5, "GROUND", fontsize=6.4, color=MID, ha="right", va="center")
vline(ax, 0, -14, BODY_H + 14, color=GHOST, lw=0.8, ls=CENTRE, zorder=2)          # centreline

# axle: hidden through the slabs, proud 5 mm beyond each leg
for zz in (AXLE_Z - AXLE_D / 2, AXLE_Z + AXLE_D / 2):
    hline(ax, -TOTAL_W / 2, TOTAL_W / 2, zz, color=GHOST, lw=0.9, ls=HIDDEN, zorder=4)
for sgn in (-1, 1):
    rect(ax, sgn * TOTAL_W / 2 if sgn > 0 else -AXLE_L / 2, AXLE_Z - AXLE_D / 2, 5, AXLE_D, lw=1.1, fc="white")

# slabs: legs 4 mm up (the body carries the robot at rest), body = two slabs + groove
for sgn in (-1, 1):
    slab_front(ax, sgn * LEG_Y - SLAB_W / 2, SLAB_W, BODY_EXTRA, LEG_H)
slab_front(ax, -BODY_W / 2, BODY_W, 0, BODY_H)
for x in (-GAP / 2, GAP / 2):
    vline(ax, x, 0, BODY_H, color=INK, lw=0.9, zorder=4)

# face panels (1.2 mm recesses): 3 rows per slab, w - 12 wide
for z0, z1 in panel_rows(BODY_H, 0):
    rrect(ax, -(BODY_W - 12) / 2, z0, BODY_W - 12, z1 - z0, 3, ec=MID, lw=0.8, fc="none", z=3.6)
for sgn in (-1, 1):
    for z0, z1 in panel_rows(LEG_H, BODY_EXTRA):
        rrect(ax, sgn * LEG_Y - (SLAB_W - 12) / 2, z0, SLAB_W - 12, z1 - z0, 3, ec=MID, lw=0.8, fc="none", z=3.6)

# display window and speaker grille
rect(ax, -DISP_W / 2, DISP_Z0, DISP_W, DISP_H, lw=1.6, fc="white", z=4.2)
ax.text(0, DISP_Z0 + DISP_H / 2, "DISPLAY\nWINDOW", fontsize=6.6, color=MID, ha="center",
        va="center", zorder=5, linespacing=1.3)
for gz in GRILLE_Z:
    for gu in GRILLE_U:
        ax.add_patch(Circle((gu, gz), 1.5, fc="white", ec=INK, lw=0.8, zorder=4.4))

# dimensions
top = BODY_H
dim(ax, (-TOTAL_W / 2, top), (TOTAL_W / 2, top), 40, f"{TOTAL_W:.0f}")
dim(ax, (LEG_Y - SLAB_W / 2, top), (LEG_Y + SLAB_W / 2, top), 18, f"{SLAB_W:.0f}", tshift=4.4)
dim(ax, (-BODY_W / 2, top), (BODY_W / 2, top), 18, f"{BODY_W:.0f}", tshift=4.4)
dim(ax, (-TOTAL_W / 2, 0), (-TOTAL_W / 2, BODY_H), 22, f"{BODY_H:.0f}", gap1=0.0)
dim(ax, (-TOTAL_W / 2, 0), (-TOTAL_W / 2, AXLE_Z), 44, f"AXLE {AXLE_Z:.0f}", gap1=0.0)
dim(ax, (TOTAL_W / 2, BODY_EXTRA), (TOTAL_W / 2, BODY_EXTRA + LEG_H), -22, f"{LEG_H:.0f}")
dim(ax, (DISP_W / 2, DISP_Z0), (DISP_W / 2, DISP_Z0 + DISP_H), -12, f"{DISP_H:.0f}", fs=7.6)
dim(ax, (-DISP_W / 2, DISP_Z0), (DISP_W / 2, DISP_Z0), 7, f"{DISP_W:.0f}", fs=7.6, tshift=3.6)
dim(ax, (DISP_W / 2, DISP_Z0 + DISP_H), (DISP_W / 2, BODY_H), -12, f"{BODY_H - DISP_Z0 - DISP_H:.0f}", fs=7.6)
leader(ax, (GRILLE_U[-1] + 1.5, GRILLE_Z[0]), (58, 22), "SPEAKER GRILLE\n7 × 3 HOLES Ø3 @ 6")
leader(ax, (-BODY_W / 2 + 6, 100), (-112, 150), "FACE PANELS\n1.2 DEEP, 3 ROWS\nPER SLAB", ha="center")
leader(ax, (TOTAL_W / 2 + 4, AXLE_Z + 1), (104, 262), f"AXLE Ø{AXLE_D:.0f}\nALUMINIUM", ha="center")
leader(ax, (GAP / 2, 30), (26, -24), f"CENTRE GROOVE {GAP:.0f}\n(TWIN-SLAB FACADE)", ha="left")

ax.text(-146, 311, "FRONT VIEW", fontsize=12, fontweight="bold", color=INK, ha="left", va="center")
ax.text(-146, 303, "DISPLAY SIDE (−x) · LEGS 4 mm ABOVE THE GROUND", fontsize=7.3, color=MID,
        ha="left", va="top")

# ============================================================================
# SIDE VIEW  (from +y; page x = -x, so the display side is on the right)
# ============================================================================
sx = fig.add_axes([0.365, 0.118, 0.245, 0.862])
view(sx, (-78, 112), (-44, 318))
hline(sx, -60, 64, 0, **ground_kw)
vline(sx, 0, -10, BODY_H + 18, color=GHOST, lw=0.8, ls=CENTRE, zorder=2)

# the body's bottom shows under the leg (it is 4 mm longer); the leg in front
foot_outline(sx, -SLAB_D / 2, SLAB_D, 0, 30, FOOT_R, z=2.6)
foot_outline(sx, -SLAB_D / 2, SLAB_D, BODY_EXTRA, LEG_H, FOOT_R, z=3)
for x in (-SLAB_D / 2 + EDGE_R, SLAB_D / 2 - EDGE_R):                                # R4 tangent edges
    vline(sx, x, BODY_EXTRA + FOOT_R, BODY_EXTRA + LEG_H, color=FAINT, lw=0.7, zorder=3.3)

# hidden: the leg's hollow lower half, the bearing seat, the body's lift slot and servo bays
hid = dict(color=GHOST, lw=0.9, ls=HIDDEN, zorder=3.6)
rect(sx, -(SLAB_D / 2 - WALL), BODY_EXTRA + WALL, SLAB_D - 2 * WALL, LEG_H / 2, ec=GHOST, lw=0.9, ls=HIDDEN, z=3.5)
sx.add_patch(Circle((0, AXLE_Z), (BRG_OD + 0.3) / 2, fill=False, ec=GHOST, lw=0.9, ls=HIDDEN, zorder=3.6))
slot(sx, 0, AXLE_Z, AXLE_Z - LIFT, AXLE_D + 0.6, **hid)
rect(sx, -SERVO_L / 2, BAY_Z0, SERVO_L, SERVO_H, ec=GHOST, lw=0.9, ls=HIDDEN, z=3.5)

# the axle end, proud of the leg
sx.add_patch(Circle((0, AXLE_Z), AXLE_D / 2, fc="white", ec=INK, lw=1.3, zorder=4))
for d in ((-3.2, 0, 3.2, 0), (0, -3.2, 0, 3.2)):
    sx.plot([d[0], d[2]], [AXLE_Z + d[1], AXLE_Z + d[3]], color=INK, lw=0.6, zorder=4.2)

# dimensions
dim(sx, (-SLAB_D / 2, 0), (SLAB_D / 2, 0), -20, f"{SLAB_D:.0f}", gap1=4.0, gap2=4.0)
dim(sx, (SLAB_D / 2, AXLE_Z), (SLAB_D / 2, BODY_H), -14, f"{AXLE_FROM_TOP:.0f}", fs=7.8)
dim(sx, (SLAB_D / 2, AXLE_Z - LIFT), (SLAB_D / 2, AXLE_Z), -14, f"LIFT {LIFT:.0f}", fs=7.8)
dim(sx, (SLAB_D / 2, 0), (SLAB_D / 2, BODY_EXTRA), -14, f"{BODY_EXTRA:.0f}", fs=7.8, outside=True,
    arrow_len=6.0, text_pos=(SLAB_D / 2 + 21.5, 13.5), text_rot=0)
leader(sx, (-1.5, AXLE_Z + AXLE_D / 2 + 0.5), (-62, 282), f"AXLE Ø{AXLE_D:.0f}")
leader(sx, (-(BRG_OD / 2) * 0.72, AXLE_Z + (BRG_OD / 2) * 0.7), (-62, 266),
       f"608ZZ Ø{BRG_OD:.0f} × {BRG_W:.0f}\nSEAT, INBOARD FACE")
leader(sx, (0, AXLE_Z - LIFT - 4.5), (-62, 150), "LIFT SLOT IN THE BODY\n(HIDDEN): THE BODY\nRISES UP TO 35")
leader(sx, (SERVO_L / 2, BAY_Z0 + 6), (-62, 118), "SERVO BAY (HIDDEN)\nMG996R + PLAY, EACH SIDE", color=MID)
leader(sx, (-SLAB_D / 2 + 1.8, 1.8), (-62, 40), f"FOOT R{FOOT_R:.0f}: ROLLS\nOVER, DOESN'T PIVOT")
leader(sx, (SLAB_D / 2 - 10, 2.0), (62, -30), "BODY 4 LONGER:\nCARRIES THE ROBOT\nAT REST", ha="center")

sx.text(-76, 311, "SIDE VIEW", fontsize=12, fontweight="bold", color=INK, ha="left", va="center")
sx.text(-76, 303, "FROM +y · HIDDEN LINES DASHED", fontsize=7.3, color=MID, ha="left", va="top")

# ============================================================================
# TOP VIEW  (page x = -y as in the front view; display side (-x) at the bottom)
# ============================================================================
tx = fig.add_axes([0.618, 0.585, 0.374, 0.395])
view(tx, (-120, 120), (-58, 74))
for sgn in (-1, 1):
    rrect(tx, sgn * LEG_Y - SLAB_W / 2, -SLAB_D / 2, SLAB_W, SLAB_D, EDGE_R)
rrect(tx, -BODY_W / 2, -SLAB_D / 2, BODY_W, SLAB_D, EDGE_R)
for yy in (-SLAB_D / 2, SLAB_D / 2 - 1.6):                                           # grooves, front + back
    rect(tx, -GAP / 2, yy, GAP, 1.6, lw=0.9, fc="white", z=3.4)
for zz in (-AXLE_D / 2, AXLE_D / 2):
    hline(tx, -TOTAL_W / 2, TOTAL_W / 2, zz, color=GHOST, lw=0.9, ls=HIDDEN, zorder=4)
for sgn in (-1, 1):
    rect(tx, TOTAL_W / 2 if sgn > 0 else -AXLE_L / 2, -AXLE_D / 2, 5, AXLE_D, lw=1.1, fc="white", z=4)
hline(tx, -AXLE_L / 2 - 8, AXLE_L / 2 + 8, 0, color=GHOST, lw=0.8, ls=CENTRE, zorder=2)
tx.text(0, -SLAB_D / 2 - 5, "DISPLAY SIDE", fontsize=6.4, color=MID, ha="center", va="top")

dim(tx, (-TOTAL_W / 2, SLAB_D / 2), (TOTAL_W / 2, SLAB_D / 2), 13, f"{TOTAL_W:.0f}")
dim(tx, (-AXLE_L / 2, SLAB_D / 2), (AXLE_L / 2, SLAB_D / 2), 27, f"AXLE {AXLE_L:.0f}")
dim(tx, (TOTAL_W / 2, -SLAB_D / 2), (TOTAL_W / 2, SLAB_D / 2), -13, f"{SLAB_D:.0f}")
leader(tx, (-(BODY_W / 2 + GAP / 2), -SLAB_D / 2 + 3), (-104, -48), f"GAP {GAP:.0f}")
leader(tx, (-LEG_Y - SLAB_W / 2 + 1.2, SLAB_D / 2 - 1.2), (-110, 44), f"R{EDGE_R:.0f}")

tx.text(-118, 70, "TOP VIEW", fontsize=12, fontweight="bold", color=INK, ha="left", va="center")
tx.text(-118, 63, "LOOKING DOWN · AXLE HIDDEN, 5 PROUD EACH SIDE", fontsize=7.3, color=MID,
        ha="left", va="top")

# ============================================================================
# NOTES
# ============================================================================
nx = fig.add_axes([0.618, 0.118, 0.374, 0.452])
nx.axis("off")
nx.set_xlim(0, 1)
nx.set_ylim(0, 1)
nx.add_patch(Rectangle((0, 0), 1, 1, fill=False, ec=INK, lw=1.0))
nx.text(0.03, 0.955, "NOTES — PARTS & CONSISTENCY", fontsize=9.5, fontweight="bold",
        color=INK, ha="left", va="top")
notes = (
    f"1. MATCHES simulation/v3_model.py: SLABS {SLAB_W:.0f} × {SLAB_D:.0f}, LEGS {LEG_H:.0f}, BODY\n"
    f"   +{BODY_EXTRA:.0f} (CARRIES THE ROBOT AT REST), AXLE {AXLE_FROM_TOP:.0f} BELOW THE TOPS, LIFT {LIFT:.0f}.\n"
    f"2. LIFT: THE Ø{AXLE_D:.0f} AXLE RIDES A {LIFT:.0f} mm VERTICAL SLOT IN THE BODY; PRESSING\n"
    "   THE LEGS DOWN RAISES THE BODY.  SWING: EACH LEG TURNS ON A 608ZZ\n"
    f"   (Ø{BRG_OD:.0f} × Ø8 × {BRG_W:.0f}) SEATED IN ITS INBOARD FACE.\n"
    "3. BODY HOLDS: RASPBERRY PI 5 (VERTICAL), 2S BATTERY, PCA9685, 2.4\" SPI\n"
    f"   DISPLAY (WINDOW {DISP_W:.0f} × {DISP_H:.0f}), SPEAKER, 4 × MG996R (LIFT + SWING, EACH\n"
    f"   SIDE).  BAYS {SERVO_L} × {SERVO_W} × {SERVO_H} AGAINST EACH INNER WALL; CRANK IS v0.4.\n"
    f"4. WALL {WALL}.  VERTICAL EDGES R{EDGE_R:.0f}.  BOTTOM EDGES R{FOOT_R:.0f}: THE SLABS ROLL\n"
    "   OVER THE STANCE FOOT INSTEAD OF PIVOTING ON AN EDGE.\n"
    "5. GAIT (simulation/v3_sim.py): CRUTCH VAULT — PRESS DOWN ON VERTICAL\n"
    "   LEGS, VAULT 12°, SET DOWN, SWING.  36 cm IN 15 s, UPRIGHT AT ALL 15\n"
    "   SOLVER AND PHYSICS SETTINGS OF --robust.\n"
    "6. v0.3.1: LIFT SLOT MOVED FROM THE LEGS TO THE BODY; RIGHT LEG\n"
    "   MIRRORED; SERVO BAYS SYMMETRIC; FACE PANELS AS THE FORMULA INTENDS.\n"
    "7. ALL DIMENSIONS mm.  THE FIRST BUILD USES THE TARS-AI V3 CHASSIS;\n"
    "   THIS MODEL IS THE PLATFORM FOR A LATER VERSION."
)
nx.text(0.03, 0.885, notes, fontsize=7.5, color=INK, ha="left", va="top", linespacing=1.55)

# ============================================================================
# TITLE BLOCK
# ============================================================================
tb = fig.add_axes([0.008, 0.010, 0.984, 0.096])
tb.axis("off")
tb.set_xlim(0, 1)
tb.set_ylim(0, 1)
tb.add_patch(Rectangle((0, 0), 1, 1, fill=False, ec=INK, lw=1.5))
for xdiv in (0.40, 0.70, 0.795, 0.90):
    tb.plot([xdiv, xdiv], [0, 1], color=INK, lw=1.0)
tb.text(0.012, 0.66, "INTERSTELLAR-TARS-ROBOT-PROJECT", fontsize=13, fontweight="bold",
        color=INK, ha="left", va="center")
tb.text(0.012, 0.24, "TARS MINI — PARAMETRIC CHASSIS v0.3.1: SLABS, LIFT & SWING",
        fontsize=7.8, color=MID, ha="left", va="center")
tb.text(0.55, 0.66, f"matches v3_model.py: slabs {SLAB_W:.0f} × {SLAB_D:.0f}, legs {LEG_H:.0f} mm",
        fontsize=8.6, fontweight="bold", color=INK, ha="center", va="center")
tb.text(0.55, 0.24, f"axle {AXLE_FROM_TOP:.0f} below the tops  ·  lift {LIFT:.0f} mm  ·  608ZZ swing  ·  read from tars.scad",
        fontsize=7.6, color=MID, ha="center", va="center")
tb.text(0.7475, 0.66, "DATE: 2026-09-29", fontsize=8.2, color=INK, ha="center", va="center")
tb.text(0.7475, 0.24, "UNITS: mm", fontsize=8.2, color=INK, ha="center", va="center")
tb.text(0.8475, 0.66, "SCALE: NTS", fontsize=8.2, color=INK, ha="center", va="center")
tb.text(0.8475, 0.24, "SHEET 1 OF 1", fontsize=8.2, color=INK, ha="center", va="center")
tb.text(0.95, 0.66, "DWG TARS26-HW-001", fontsize=7.6, color=INK, ha="center", va="center")
tb.text(0.95, 0.24, "REV A", fontsize=8.2, color=INK, ha="center", va="center")

fig.savefig(OUT_PNG, dpi=160, facecolor="white")
print(f"wrote {OUT_PNG}")
