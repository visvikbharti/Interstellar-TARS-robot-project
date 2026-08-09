# Research Notes — TARS builds landscape (2026-08-10)

Digest of a 10-agent research sweep (5 topics + critic + 4 follow-ups), all
claims verified on fetched pages. Full raw report archived in the session.

## The one proven base: TARS-AI Community V3

- **github.com/TARS-AI-Community/TARS-AI** — 574★, active (last push Apr 2026),
  the de-facto continuation of Charlie Diaz's original design. Default branch
  is **V3** (do NOT use `main` — it carries obsolete V1/V2 tooling).
- **Exactly 25.0cm tall** (an agent downloaded their official STEP assembly and
  measured it: 241.8 × 250.1 × 65.4 mm). Print at 100% — do not rescale, every
  fit is dimensioned around COTS parts.
- ~130 pre-oriented STLs, full BOM, assembly wiki. License **CC-BY-NC 4.0**:
  personal building/modifying is explicitly fine (attribution: Charlie Diaz /
  TARS-AI Community / AtomikSpace); selling prints is not.
- Survey verdict: **no alternative walkable STL set exists anywhere** —
  everything else is static display models, closed research (TARS3D), or
  software stacks reusing this same chassis.

## How the proven design walks (important!)

V3 uses **4 servos**: left/right torso-LIFT + left/right leg-SWING. The gait
never balances — it lifts the torso, swings legs, and **rests the torso on the
ground** while repositioning. Quasi-static keyframe tables (percent coords in
`module_movements.py`), tuned via config.ini PWM endpoints + offsets.
Calibration: official video "Getting TARS Moving Right" (youtube We_4mcOO7hI)
by the V3 hardware author + `app-servotester.py` (GUI/terminal). Calibrate
DURING assembly (preset servos before pressing horns on, never rotate a powered
servo by hand). Our MuJoCo sim independently confirmed *why* the lift DOF
exists: without it, an open-loop 2-servo gait always tips over — we made
2-servo walking work only by adding an IMU balance loop.

## Voice stack (2026 state of the art on Pi)

| Layer | Choice | Notes |
|---|---|---|
| Wake word | openWakeWord, custom "Hey TARS" (or TARS-AI's Atomik) | Train free in Colab from synthetic speech, <1h |
| STT | sherpa-onnx (TARS-AI default) or Moonshine (MIT, 237ms on Pi 5) | Fully local on Pi 5 |
| TTS | Piper (local, free; now OHF-Voice/piper1-gpl) | ElevenLabs voice-clone of the movie voice is the community method for authenticity (~$6/mo; ToS caveat — cloning an actor's voice) |
| LLM | **Claude API** (our personality core) | Precedent: "Claudia" project runs Claude on a Pi Zero 2 W, <2s end-to-end. TARS-AI's backends are OpenAI-compatible → we write a thin adapter or our own ~200-line loop |

**The latency law**: stream the LLM reply and speak sentence-by-sentence
(start TTS after the first sentence). This is what turns 8–15s perceived
latency into ~2s. Design target: wake→speech ≈ 1.5–4s.

## Pi 4 vs Pi 5 (contradiction resolved by reading their code)

The wiki documents only Pi 5, but `Install.sh` + `module_config.py` on V3 have
a first-class **Pi 4 profile** (local STT/TTS/wake word all allowed; loses
camera vision, face/emotion, half the STT threads, 8k vs 16k context). Pi 3 /
Zero 2 = cloud-only mode. → For a new purchase, Pi 5 8GB is the clear choice.

## Audio amp question (resolved)

The BOM's Waveshare USB audio dongle has an **onboard 2.6W amplifier** driving
the speaker directly — no MAX98357A needed. If quiet: internal trim screw +
alsamixer.

## Key pitfalls from the Diaz lineage

- Diaz's V1 broke printed drivetrain parts after ~4 steps — heavy batteries +
  torso-heavy mass. Keep mass low and light; PETG 3+ walls on load parts.
- Route arm servo cables through the torso during initial assembly even if
  arms come later (otherwise: full disassembly).
- Gentler gait = pull in the lift endpoints in config.ini, not new phase tables.
- Support runs on Discord (discord.gg/AmE2Gv9EUt); GitHub issues are locked.
