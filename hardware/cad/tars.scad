// ============================================================
// TARS mini — parametric chassis, v0.3  (sim-validated architecture)
// ============================================================
// Architecture validated in simulation (simulation/v3_sim.py — the
// crutch-vault gait walks 2.4 cm/s and stays upright at every solver
// setting in --robust; audit 2026-09-29) and matching the community
// TARS-AI V3 / Charlie Diaz mechanism:
//
//   BODY  — central chassis styled as the two middle slabs, one print.
//           Holds Pi 5 (vertical), battery, PCA9685, display, speaker.
//           Its bottom TOUCHES THE GROUND between steps (4mm longer
//           than the legs) — the robot never balances.
//   LEGS  — the two outer slabs. Each leg has TWO degrees of freedom:
//           lift  (35mm vertical slide: axle rides in a slot)
//           swing (rotation on the shoulder axle, 608ZZ bearing)
//
// Keep dimensions in sync with simulation/v3_model.py.
// v0.4 TODO: lift crank linkage detail (servo horn + link), lids,
//            wire channels. Wheel mode (4 driven slabs, see
//            simulation/roll_sim.py) is the v2-hardware variant.
// ============================================================

/* ---------- master dimensions (= v3_model.py) ---------- */
slab_w     = 40;    // width of one slab
slab_d     = 55;    // depth (front-to-back)
leg_h      = 240;   // leg slab height
body_extra = 4;     // body is longer -> body carries the robot at rest
body_h     = leg_h + body_extra;
gap        = 2;     // visual gap between slabs
body_w     = 2 * slab_w + gap;   // chassis width (two middle slabs, one print)

axle_from_top = 25; // shoulder axle, below the slab tops
axle_d        = 8;  // 8mm aluminium rod
lift_travel   = 35; // vertical slide range of each leg

foot_r  = 6;        // bottom edge round-over (sim: roll, don't pivot)
chamfer = 4;        // vertical edge chamfer (monolith look)
wall    = 2.4;      // shell wall

/* ---------- COTS parts (check hardware/BOM.md) ---------- */
brg_od = 22; brg_w = 7;             // 608ZZ bearing
servo_l = 40.7; servo_w = 20.1; servo_h = 42.9;  // MG996R + play
pi_w = 56; pi_l = 85; pi_t = 21;    // Pi 5 (mounted vertically)
disp_w = 52; disp_h = 82;           // 2.4" SPI display window w/ margin

/* ---------- derived ---------- */
axle_z  = body_h - axle_from_top - body_extra + body_extra; // = leg pivot height
leg_y   = body_w / 2 + gap + slab_w / 2;
total_w = body_w + 2 * (gap + slab_w);

// "assembly" | "exploded" | "print_body" | "print_leg"
RENDER_MODE = "assembly";

/* ============================================================
   primitives
   ============================================================ */

module chamfered_box(w, d, h, c) {   // chamfered VERTICAL edges
    hull()
        for (x = [-1, 1], y = [-1, 1])
            translate([x * (d/2 - c), y * (w/2 - c), 0])
                cylinder(h = h, r = c, $fn = 32);
}

// cross-section with ROUNDED BOTTOM edges, square top (x-z plane)
module foot_profile(d, h, r) {
    hull() {
        translate([-(d/2 - r), r]) circle(r, $fn = 48);
        translate([ (d/2 - r), r]) circle(r, $fn = 48);
        translate([0, h - 0.5]) square([d, 1], center = true);
    }
}

// slab solid: chamfered verticals AND rounded bottom
module slab_solid(w, d, h) {
    intersection() {
        chamfered_box(w, d, h, chamfer);
        rotate([90, 0, 0])
            linear_extrude(w + 2, center = true)
                foot_profile(d, h, foot_r);
    }
}

module face_panels(w, d, h, rows = 3) {
    ph = (h - 40) / rows - 6;
    for (side = [-1, 1], i = [0 : rows - 1])
        translate([side * (d/2 - 1.2 + 0.01), 0, 15 + i * (ph + 6)])
            rotate([0, side * -90, 0])
                translate([0, 0, -1.2])
                    linear_extrude(1.24)
                        offset(r = 3) offset(r = -3)
                            square([w - 12, ph], center = true);
}

/* ============================================================
   BODY — central chassis (one print, twin-slab facade)
   ============================================================ */
module body() {
    difference() {
        slab_solid(body_w, slab_d, body_h);

        // interior cavity (leave the axle zone solid-ish)
        translate([0, 0, wall])
            chamfered_box(body_w - 2*wall, slab_d - 2*wall,
                          body_h - wall - 55, 2);

        // twin-slab illusion: centre grooves front + back
        for (side = [-1, 1])
            translate([side * (slab_d/2 - 0.75), 0, -1])
                cube([1.6, gap, body_h + 2], center = false);

        face_panels(body_w, slab_d, body_h);

        // display window — upper front chest
        translate([-slab_d/2 - 1, -disp_w/2, body_h - 35 - disp_h])
            cube([wall + 2, disp_w, disp_h]);

        // speaker grille — lower front
        for (gy = [-3 : 3], gz = [0 : 2])
            translate([-slab_d/2 - 1, gy * 6, 45 + gz * 6])
                rotate([0, 90, 0]) cylinder(h = wall + 2, d = 3, $fn = 16);

        // shoulder axle bore straight through
        translate([0, -body_w/2 - gap - 1, axle_z])
            rotate([-90, 0, 0])
                cylinder(h = body_w + 2*gap + 2, d = axle_d + 0.4, $fn = 48);

        // servo bays flanking the axle (2x MG996R per side, lift + swing)
        for (s = [-1, 1])
            translate([-servo_l/2, s * (body_w/2 - servo_w - wall) - (s < 0 ? 0 : 0), axle_z - servo_h + 8])
                cube([servo_l, servo_w, servo_h]);
    }
}

/* ============================================================
   LEG — outer slab: axle SLOT (lift travel) + bearing pocket (swing)
   ============================================================ */
module leg() {
    difference() {
        slab_solid(slab_w, slab_d, leg_h);
        // hollow lower half (battery bay optional in v2; keeps legs light)
        translate([0, 0, wall])
            chamfered_box(slab_w - 2*wall, slab_d - 2*wall, leg_h/2, 2);
        face_panels(slab_w, slab_d, leg_h);

        // vertical SLOT for the axle: the leg slides 35mm on the shoulder
        hull()
            for (dz = [0, lift_travel])
                translate([0, -slab_w/2 - 1, leg_h - axle_from_top - dz])
                    rotate([-90, 0, 0])
                        cylinder(h = slab_w + 2, d = axle_d + 0.6, $fn = 48);

        // bearing pocket at the TOP of the slot (inboard face) — the leg
        // hangs on the bearing; the lift crank (v0.4) pushes it down
        translate([0, slab_w/2 - brg_w + 0.01, leg_h - axle_from_top])
            rotate([-90, 0, 0])
                cylinder(h = brg_w + 0.5, d = brg_od + 0.3, $fn = 64);
    }
}

/* ============================================================
   assembly / print layouts
   ============================================================ */
module assembly(explode = 0) {
    color("gray") translate([0, 0, 0]) body();
    color("dimgray")
        for (s = [-1, 1])
            translate([0, s * (leg_y + explode * 45), body_extra])
                leg();
    color("silver")
        translate([0, -total_w/2 - 5 - explode * 40, axle_z])
            rotate([-90, 0, 0])
                cylinder(h = total_w + 10, d = axle_d, $fn = 48);
}

if (RENDER_MODE == "assembly")   assembly(0);
if (RENDER_MODE == "exploded")   assembly(1);
if (RENDER_MODE == "print_body") rotate([0, -90, 0]) body();  // lies on its back
if (RENDER_MODE == "print_leg")  rotate([0, -90, 0]) leg();
