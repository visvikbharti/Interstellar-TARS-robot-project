// ============================================================
// TARS mini — parametric chassis, v0.1
// ============================================================
// Four vertical slabs, movie proportions. The two INNER slabs are
// the driven "walker" pair (keyed to the axle, swung by a servo in
// the spine). The two OUTER slabs are the stance pair, riding on
// 608ZZ bearings so the axle turns freely inside them.
//
// All dimensions in mm. Keep these in sync with simulation/gen_model.py.
//
// v0.2 design notes (from MuJoCo gait simulation, 2026-08-10):
//  * slab_d 50->55: deeper feet = bigger fore-aft tip margin
//  * bottom front/back edges get a ~6mm round-over so the robot ROLLS
//    over the stance foot instead of pivoting on a sharp edge
//  * one 18650 cell low in EACH OUTER SLAB + Pi on a FRONT chest plate:
//    drops the COM to ~11cm and centers it (stand + walk verified in sim)
//  * walking requires the MPU6050 IMU balance loop (see simulation/) —
//    open-loop gaits fall over; the proven TARS-AI V3 alternative instead
//    adds torso-lift servos and rests the torso on the ground between steps
// ============================================================

/* ---------- master dimensions ---------- */
slab_h      = 240;   // slab height (robot stands ~240mm + foot clearance)
slab_w      = 40;    // width of one slab
slab_d      = 55;    // depth (front-to-back) — v0.2: was 50, deeper = more stable
slab_gap    = 2;     // air gap between slabs
chamfer     = 4;     // edge chamfer for the monolith look
wall        = 2.4;   // shell wall thickness (print in PLA/PETG, 3+ walls)

inner_extra = 4;     // inner pair is slightly LONGER -> deterministic
                     // support handoff while rocking (gait trick)

axle_from_top = 25;  // axle centreline, measured down from slab top
axle_d        = 8;   // 8mm aluminium rod/tube

/* ---------- bearings & servo (check against BOM) ---------- */
brg_od = 22;  brg_w = 7;          // 608ZZ bearing
servo_l = 40.7; servo_w = 19.7;   // MG996R body
servo_h = 42.9; servo_flange = 54.5;

/* ---------- spine (back plate joining the outer slabs, holds Pi/servo/battery) ---------- */
spine_t = 12;                     // spine plate thickness
spine_h = 160;                    // spine height — v0.2: extended for wiring + low mounting

/* ---------- face detailing ---------- */
panel_inset = 1.2;                // shallow pockets for the segmented TARS look
panel_rows  = 3;

/* ---------- derived ---------- */
pitch   = slab_w + slab_gap;                 // slab-to-slab spacing
total_w = 4 * slab_w + 3 * slab_gap;         // full robot width (166mm default)
axle_z  = slab_h - axle_from_top;            // axle height above slab bottom
slab_y  = [ -1.5*pitch, -0.5*pitch, 0.5*pitch, 1.5*pitch ];  // slab centres

// What to show: "assembly" | "exploded" | "print_outer" | "print_inner" | "print_spine"
RENDER_MODE = "assembly";

/* ============================================================
   primitives
   ============================================================ */

// box with chamfered vertical edges (the monolith profile)
module chamfered_box(w, d, h, c) {
    hull()
        for (x = [-1, 1], y = [-1, 1])
            translate([x*(d/2 - c), y*(w/2 - c), 0])
                cylinder(h = h, r = c, $fn = 32);
}

// shallow rectangular pockets on both faces — TARS's segmented panels
module face_panels(w, d, h) {
    rows = panel_rows;
    ph = (h - 40) / rows - 6;
    for (side = [-1, 1], i = [0 : rows - 1])
        translate([side * (d/2 - panel_inset + 0.01), 0, 15 + i * (ph + 6)])
            rotate([0, side * -90, 0])
                translate([0, 0, -panel_inset])
                    linear_extrude(panel_inset + 0.02)
                        offset(r = 3) offset(r = -3)
                            square([w - 12, ph], center = true);
}

/* ============================================================
   slabs
   ============================================================ */

// common slab body: chamfered block, hollowed, panelled, axle bore
module slab_body(len, bore_d) {
    difference() {
        chamfered_box(slab_w, slab_d, len, chamfer);
        // hollow interior (leave solid 30mm around the axle zone)
        translate([0, 0, wall])
            chamfered_box(slab_w - 2*wall, slab_d - 2*wall,
                          len - wall - 45, max(chamfer - wall, 1));
        face_panels(slab_w, slab_d, len);
        // axle bore, full width
        translate([0, -slab_w/2 - 1, len - axle_from_top])
            rotate([-90, 0, 0])
                cylinder(h = slab_w + 2, d = bore_d, $fn = 48);
    }
}

// OUTER slab: rides on a 608ZZ bearing (pocket on the inboard face)
module outer_slab() {
    difference() {
        slab_body(slab_h, axle_d + 1.0);   // loose bore; bearing takes the load
        // bearing pocket, inboard side
        translate([0, slab_w/2 - brg_w + 0.01, slab_h - axle_from_top])
            rotate([-90, 0, 0])
                cylinder(h = brg_w + 0.5, d = brg_od + 0.3, $fn = 64);
    }
}

// INNER slab: keyed to the axle (D-flat bore) so the servo drives it
module inner_slab() {
    len = slab_h + inner_extra;
    difference() {
        slab_body(len, axle_d + 0.3);      // snug bore
        // (D-flat: flatten the bore by 1mm — cut a shallow slot keyway instead
        //  if your rod is round; grub-screw boss is the v0.2 refinement)
    }
    // grub screw boss under the axle
    translate([0, 0, len - axle_from_top - 10])
        difference() {
            cube([14, slab_w - 2*wall, 8], center = true);
            rotate([0, 0, 0]) cylinder(h = 10, d = 2.8, center = true, $fn = 24); // M3 tap
        }
}

/* ============================================================
   spine — back plate joining the two outer slabs; mounts the
   drive servo (nose through the plate onto the axle), Pi + battery
   ============================================================ */
module spine() {
    difference() {
        // plate spanning the outer slabs, sitting behind the robot
        translate([slab_d/2 + spine_t/2, 0, slab_h - spine_h])
            chamfered_box(total_w, spine_t, spine_h, 3);
        // servo cutout centred on the axle line
        translate([slab_d/2 - 1, 0, axle_z])
            rotate([0, 90, 0])
                cube([servo_w + 0.6, servo_l + 0.6, spine_t + 14], center = true);
        // wiring pass-throughs
        for (y = [-pitch, pitch])
            translate([slab_d/2 + spine_t/2, y, slab_h - spine_h + 20])
                rotate([0, 90, 0])
                    cylinder(h = spine_t + 2, d = 10, center = true, $fn = 32);
    }
}

/* ============================================================
   assembly / print layouts
   ============================================================ */
module assembly(explode = 0) {
    color("dimgray")  for (i = [0, 3]) translate([0, slab_y[i], 0]) outer_slab();
    color("gray")     for (i = [1, 2])
        translate([0, slab_y[i] * (1 + explode * 0.4), -inner_extra]) inner_slab();
    color("silver")   // axle
        translate([0, -total_w/2 - 5 - explode * 30, axle_z])
            rotate([-90, 0, 0]) cylinder(h = total_w + 10, d = axle_d, $fn = 48);
    color("darkslategray") translate([explode * 40, 0, 0]) spine();
}

if (RENDER_MODE == "assembly")     assembly(0);
if (RENDER_MODE == "exploded")     assembly(1);
if (RENDER_MODE == "print_outer")  rotate([0, -90, 0]) outer_slab();   // lie flat
if (RENDER_MODE == "print_inner")  rotate([0, -90, 0]) inner_slab();
if (RENDER_MODE == "print_spine")  rotate([0, 90, 0])  spine();
