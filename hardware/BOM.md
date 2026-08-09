# Bill of Materials — TARS mini (India edition)

Prices live-verified on Indian vendor storefronts on **10 Aug 2026** (robu.in
GST-inclusive page prices; Shopify cart prices for Robocraze/ThinkRobotics).
Based on the proven TARS-AI V3 electronics architecture + our additions.

## The two-vendor buy (covers ~96% of the build)

**Order 1 — robu.in** (Pune; free shipping >₹999; 2–5 days to Delhi, reliable
per-SKU stock data):

| Item | Spec | ₹ (incl. GST) | Notes |
|---|---|---|---|
| Raspberry Pi 5 — 8GB | the brain | **19,999** | See "4GB option" below |
| Official 27W USB-C PSU (IN plug) | bench power | 1,255 | |
| Official Pi 5 Active Cooler | mandatory in closed torso | 488 | |
| Molicel 2S 7.4V 3500mAh pack | pre-built, A-grade, tabbed+wired | 999 | Skips DIY 18650 spot-welding entirely (Samsung 35E ₹899 alt) |
| 2S BMS 10A | pack protection | 69 | |
| 5V/5A 25W step-down | battery → **Pi rail** | 189 | |
| LM2596 buck | battery → **servo rail** (set 6.0V) | 42 | Add 470–1000µF cap across servo rail |
| INMP441 I2S MEMS mic | ears | 146 | |
| DFRobot MAX98357A I2S amp | voice amp | 669 | ₹138 more than Engineer Store, saves a third parcel |
| 2.4" ST7789V SPI display 240×320 | face/status | 427 | (V3 stock design uses a 5" screen — see below) |
| 608ZZ bearings ×4 | axle | 62 | |
| M3 bolt+nut sets | assembly | ~250 | Better: M3 assortment box on Amazon.in (~₹400–600) or Lajpat Rai Market |
| Sunlu PLA+ 1kg | chassis | 939 | Black is ₹1,398 — colour changes price! (PETG preferred for load parts) |
| MPU6050 IMU | balance loop (our addition) | ~150 | |
| **Subtotal** | | **≈ ₹25,700** | |

**Order 2 — Robocraze** (Bangalore; free delivery >₹999):

| Item | Spec | ₹ | Notes |
|---|---|---|---|
| MG996R servo **180°** ×4–6 | leg joints | 292 each | ⚠️ **robu.in's MG996R is the 360° continuous version — wrong for joints. Buy here.** |
| PCA9685 16-ch servo driver | I2C, soldered | 232 | Out of stock at robu |
| SanDisk Ultra 64GB microSD | A1 | 1,536 | A2 cards absent from hobby vendors; A1 is fine for a robot (or SanDisk Extreme A2 on Amazon.in ~₹2k) |
| **Subtotal (6 servos)** | | **≈ ₹3,520** | |

**Buy offline in Delhi:** 8mm aluminium rod/tube — Lajpat Rai Market /
Bhagirath Palace (Chandni Chowk), by the foot, cheaper than any online option
(ThinkRobotics has 300mm at ₹250 if you'd rather not go).

## Totals

| Build | Total |
|---|---|
| **Pi 5 8GB path (recommended)** | **≈ ₹30,000–30,500** all-in (incl. ~₹500–800 wire/connectors/switch) |
| Pi 5 **4GB** path | ≈ ₹22,600 (−₹7,370; TARS-AI's stated minimum — loses camera/face features + headroom) |
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

## Display note (V3 stock vs ours)

TARS-AI V3's printed chassis fits a **5" DSI 800×480** panel. India pricing
found: 5" HDMI 800×480 at ₹2,470 (robu, in stock). If we build stock V3,
budget ~₹2.5k for the 5" panel instead of the ₹427 SPI unit and check DSI vs
HDMI variant fit. Our custom chassis targets the 2.4" SPI face.

## Power architecture (do not deviate)

```
7.4V 2S pack ──┬── LM2596 @ 6.0V ───────► PCA9685 V+ ──► servos
   (via BMS)   └── 5V/5A 25W step-down ──► Raspberry Pi 5
                     (grounds common, rails separate)
```
