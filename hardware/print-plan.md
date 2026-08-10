# Print Plan — TARS-AI V3 chassis via 3D-printing service

No home printer — the chassis is printed by an online service, the same way
the micro-quad frame was done (ZBOTiC order placed and delivered within the
week, 10 Aug 2026; received part matched CAD, press-fit bores printed true).

## STL source (pinned)

- Repo: **github.com/TARS-AI-Community/TARS-AI**, branch **V3**
  (do NOT use `main` — obsolete V1/V2 tooling).
- Pinned at download time: commit **`7593f8c8b63c35e3c07cc98665970fe55cee2c23`**
  (branch head as of 13 Apr 2026, unchanged when checked 10 Aug 2026).
- ~130 pre-oriented STLs; assembly footprint 241.8 × 250.1 × 65.4 mm.
  **Print at 100% — do not rescale**; every fit is dimensioned around COTS
  parts (MG996R pockets, 608ZZ seats, the 5" DSI screen bracket).
- License CC-BY-NC 4.0 — personal build fine; attribution: Charlie Diaz /
  TARS-AI Community / AtomikSpace. Selling prints is not allowed.

## Material split (the one thing to get right in the order)

Diaz's V1 broke its printed drivetrain after ~4 steps — heavy torso, PLA
load parts. So:

| Part class | Material | Walls / infill |
|---|---|---|
| Load parts: legs, lift arms/cranks, servo mounts, axle/bearing blocks, anything the torso's weight passes through | **PETG, black** | 3+ walls, ≥30% infill |
| Cosmetic: torso slabs, facade panels, lids, screen bezel | **PLA, black** | 2–3 walls, 15–20% infill |

Layer 0.2 mm, no rescale, keep the STLs' pre-orientation (they ship
print-ready). If the service balks at a per-part material mapping, order as
two batches (one PETG, one PLA) — sort the STLs into two folders before
upload. The exact part-to-class sort happens at download time against the
V3 assembly wiki.

## Where to order (Delhi, carried over from the quad-frame build)

- **[ZBOTiC](https://zbotic.in/product/online-3d-printing-service/)** —
  incumbent; already delivered our quad frame (upload STL → quote).
- [DWart Industries](https://dwartindustries.com/shop/additive-manufacturing/fdm-3d-printing-services/)
  — ₹199 minimum, good for a small test batch.
- [RoboThings](https://robothings.in/online-3d-printing-service-in-india/) (Delhi/NCR),
  [iamRapid](https://iamrapid.com/3d-printing-services-in-delhi/) (1–2 day Delhi delivery).
- Walk-in: [SOCH3D](https://soch3d.com/3d-printing-service/delhi),
  ElectronifyIndia.

Cost is a **quote at upload** (per-gram rate × ~a robot's worth of plastic +
minimums; get two quotes — at 130 parts the per-gram rate dominates).
Sequencing tip from the quad build: the fit-critical parts arrive before the
servos are needed, so order the print set the same day as the electronics.

## On receipt — check before assembly

1. Servo pockets: an MG996R body (40.7 × 19.7 mm) press-fits without force.
2. 608ZZ bearing seats: 22 mm bearing seats snugly (light tap OK, no gap).
3. Axle/lift slots: 35 mm travel is free over the full stroke.
4. Screen bracket matches the panel actually bought (800×480 DSI vs 2.4" SPI).
5. Layer adhesion on PETG load parts: try to flex a leg by hand — no cracking.

Calibrate servos DURING assembly (preset before pressing horns on — see
docs/research-notes.md), and route arm-servo cables through the torso even
though arms come later.
