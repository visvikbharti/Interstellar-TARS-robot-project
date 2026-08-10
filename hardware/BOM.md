# Bill of Materials — TARS mini (India edition)

Prices live-verified on Indian vendor storefronts on **10 Aug 2026** (robu.in
GST-inclusive page prices; Shopify cart prices for Robocraze/ThinkRobotics).
Based on the proven TARS-AI V3 electronics architecture + our additions.

**Revised 10 Aug 2026 (late), after a full pre-order audit:** the original
power chain would not have worked — the LM2596 (3A) servo rail and the
9–24V-input Pi buck are replaced with page-verified 2S-input UBECs, and the
missing 2S charger, 20A BMS, speaker and PETG spool are now line items.

## The buy plan (three orders; robu.in carries ~88%)

**Order 1 — robu.in** (Pune; free shipping >₹999; 2–5 days to Delhi, reliable
per-SKU stock data):

| Item | Spec | ₹ (incl. GST) | Notes |
|---|---|---|---|
| Raspberry Pi 5 — 8GB | the brain | **19,999** | 4GB budget path: see Totals table below |
| Official 27W USB-C PSU (IN plug) | bench power | 1,255 | |
| Official Pi 5 Active Cooler | mandatory in closed torso | 488 | |
| Molicel 2S 7.4V 3500mAh pack | pre-built, A-grade, tabbed+wired | 999 | Skips DIY 18650 spot-welding entirely (Samsung 35E ₹899 alt) |
| UBEC-8A 2–8S Lipo | battery → **servo rail** (set **6.0V**) | 1,579 | 8A cont / 15A burst, input 6–36V ([robu](https://robu.in/product/ubec-8a-6-36v-28s-lipo-esc/)). The ONLY in-stock 2S-input unit ≥8A anywhere on 10 Aug. Add 470–1000µF cap across the rail. 6.0V (not 7.4V) keeps stall current down; if you later want sustained-stall margin, add a second and split 3 servos per UBEC |
| UBEC 5V/5A | battery → **Pi rail** | 392 | Input 5.5–35V, covers 2S sag ([robu SKU 974872](https://robu.in/product/ubec-5v-5a/)). Page says 5.25V±0.5 out — **measure under load before first connecting the Pi**; feed the GPIO 5V pins or a 5A USB-C pigtail; expect the Pi's low-power-supply warning (`usb_max_current_enable=1`). ₹91 MINI560 is an in-stock hedge but has only 0.4V margin at pack floor |
| 2S charger, 8.4V/2A CC/CV | charges the pack through its BMS | 534 | Pro-Range ETC20, barrel plug ([robu](https://robu.in/product/pro-range-battery-charger-2s-li-ion-8-4v-2a-with-dc-5-5mm-2-5mm-male-plug/)). 5.5×2.5mm MALE plug — solder a female barrel pigtail onto the pack's charge leads |
| Creality CR-PETG 1kg, black | load-bearing parts (legs, cranks, drivetrain) | 1,079 | Diaz V1 broke PLA drivetrain parts after ~4 steps — PETG, 3+ walls on load parts ([robu](https://robu.in/product/creality-cr-petg-3d-filament-1-75mm-1kg-black/)) |
| INMP441 I2S MEMS mic | ears | 146 | |
| DFRobot MAX98357A I2S amp | voice amp | 669 | ₹138 more than Engineer Store, saves a third parcel |
| 2.4" ST7789V SPI display 240×320 | face/status | 427 | (V3 stock design uses a 5" screen — see below) |
| 608ZZ bearings ×4 | axle | 62 | |
| M3 bolt+nut sets | assembly | ~250 | Better: M3 assortment box on Amazon.in (~₹400–600) or Lajpat Rai Market |
| Sunlu PLA+ 1kg | chassis/cosmetic parts | 939 | ₹939 = bright colours only (gold/beige/pink…); **black is ₹1,398** and no dark colour is in stock at ₹939 (verified). TARS is black/grey — decide at checkout (+₹459) |
| MPU6050 IMU | balance loop (our addition) | ~150 | |
| **Subtotal** | | **≈ ₹28,970** | with a ₹939-colour PLA+ spool; +₹459 if black |

**Order 2 — Robocraze** (Bangalore; free delivery >₹999):

| Item | Spec | ₹ | Notes |
|---|---|---|---|
| MG996R servo **180°** ×4–6 | leg joints | 292 each | ⚠️ **robu.in's MG996R is the 360° continuous version — wrong for joints. Buy here.** |
| PCA9685 16-ch servo driver | I2C, soldered | 232 | Out of stock at robu |
| SanDisk Ultra 64GB microSD | A1 | 1,536 | A2 cards absent from hobby vendors; A1 is fine for a robot (or SanDisk Extreme A2 on Amazon.in ~₹2k) |
| **Subtotal (6 servos)** | | **≈ ₹3,520** | |

**Order 3 — ThinkRobotics** (the two parts neither robu nor Robocraze stocks
in the right rating — both page-verified in stock 10 Aug, "only a few left"):

| Item | Spec | ₹ | Notes |
|---|---|---|---|
| BMS 2S **20A** | pack protection, 20A cont discharge / 10A charge | 170 | robu's in-stock 2S boards top out at 8A — a multi-servo stall would cut power to everything incl. the Pi (SD-corruption risk). [Product](https://thinkrobotics.com/products/bms-liion-lipo-battery-charger-protection-board) (pick the 2S 20A variant). Cheaper alt if it restocks: Robocraze's ₹65 2S-20A balanced board |
| 2030 cavity speaker 8Ω 2W | voice output — MAX98357A puts ~1.8W into 8Ω | 300 | 20×30×5.5mm, PH1.25 plug (re-terminate). [Product](https://thinkrobotics.com/products/2030-cavity-speaker-8%CF%89-2w). The ideal 4Ω 3W at Robocraze (₹124) is sold out |
| **Subtotal** | | **≈ ₹470** + shipping | |

**Buy offline in Delhi:** 8mm aluminium rod/tube — Lajpat Rai Market /
Bhagirath Palace (Chandni Chowk), by the foot, cheaper than any online option
(ThinkRobotics has 300mm at ₹250 if you'd rather not go).

## Totals

| Build | Total |
|---|---|
| **Pi 5 8GB path (recommended)** | **≈ ₹33,500–33,800** all-in (₹28,970 robu + ₹3,520 Robocraze + ~₹470 ThinkRobotics + ₹500–800 wire/connectors/switch). +₹459 if the PLA+ spool is black; +₹3,216 if swapping to the 5" DSI panel (see display note) |
| Pi 5 **4GB** path | ≈ ₹26,200 (−₹7,370) — but the only in-stock 4GB (₹12,631) is at The Engineer Store, the vendor trap #4 says to verify first; and 4GB squeezes the on-device STT/TTS headroom this build depends on |
| DS3218 20kg servo upgrade ×6 | +₹10,850 (ThinkRobotics ₹2,099 ea — the only in-stock source; robu cheaper but out of stock) |

The Pi is ⅔ of the budget — India's Pi 5 8GB price (~₹20k across vendors) is
much steeper than US pricing. If the total stings, the 4GB is the honest
budget lever, not cheaper servos.

## Traps the research caught (read before ordering!)

1. **robu.in's MG996R is continuous-rotation (360°)** — useless for position
   joints. Buy the explicit "180 Degree" one from Robocraze.
2. **TP4056 chargers cannot charge a 2S pack** (1S only). Charge the 7.4V pack
   through the BMS with an 8.4V CC/CV adapter or a dedicated 2S charger.
3. **Never run servos from the Pi's 5V buck** — 6× MG996R stall at ~2.5A each.
   Separate rails, shared ground only.
4. **The Engineer Store** has the lowest sticker prices (Pi 5 8GB ₹17,967) but
   inflated-MRP discounts, a stock warning on the Pi listing, and unclear GST
   labelling — fine for ₹800 of small parts, verify before an ₹18k order.
5. Amazon.in MG996R "4-packs" at ₹1,749 are the 360° version. Six correct
   singles from Robocraze cost the same.
6. **Check every converter's INPUT range against 2S (6.4–8.4V).** The obvious
   robu 5V/5A buck (SKU 395957, ₹189) specs **9–24V in** — it can never run
   from this pack, and several hobby "UBECs" state 8V/3S minimums despite 2S
   labels. Both converters in Order 1 are page-verified to accept 2S. (The
   original draft of this BOM had the ₹189 buck AND a 3A LM2596 servo rail —
   both caught and replaced in the 10 Aug audit.)

## Display note (V3 stock vs ours — DSI question CLOSED 10 Aug)

The TARS-AI V3 wiki/BOM lists three display options and **all are 5" DSI**
(1024×600 UeeKKoo, 800×480 Hosyond, 800×480 Waveshare), ribbon-connected to
the Pi — the ₹2,470 5" **HDMI** previously found is the wrong interface for
the V3 chassis. In-stock DSI option: **Waveshare 5" DSI 800×480 IPS touch
(thin/light), ₹3,643 at robu** ([product](https://robu.in/product/waveshare-5inch-dsi-display-800-x-480-ips-thin-and-light-design-touch-display/));
the classic 800×480 model the V3 BOM names is ₹4,049 but out of stock.
Decide before ordering: **stock-V3 build → buy the ₹3,643 DSI panel** (matches
the 800×480 screen bracket; print the matching bracket) and skip the ₹427 SPI
unit (net +₹3,216). **Custom-chassis-first → keep the 2.4" SPI.** The V3 wiki
also confirms stock audio = a Waveshare USB sound card bundled with an 8Ω 5W
speaker — our I2S pair is a deliberate deviation (see docs/research-notes.md).

## Power architecture (do not deviate)

```
7.4V 2S pack ──┬── UBEC-8A @ 6.0V ──► PCA9685 V+ ──► servos
 (via 20A BMS) └── UBEC 5V/5A ──────► Raspberry Pi 5 (GPIO 5V pins
                (grounds common,       or a 5A USB-C pigtail)
                 rails separate)

Charging: 8.4V/2A CC/CV adapter ─► female barrel pigtail ─► pack charge
leads (through the BMS). Never a TP4056.
```
