# TARS — Mini Walking Robot (Interstellar)

A ~25–30cm, 3D-printed, walking and talking replica of TARS from *Interstellar*.
Raspberry Pi brain, servo-driven gait, Claude-powered personality with the
movie's adjustable **humor** and **honesty** settings.

> Cooper: "Hey TARS, what's your honesty parameter?"
> TARS: "Ninety percent."

## Project layout

```
software/    TARS's brain — personality, chat, (soon) voice + servo control
hardware/    Bill of materials, parametric CAD, print plan (wiring doc to come)
docs/        Design decisions, research notes, India sourcing report
```

## Quick start (talk to TARS today, no hardware needed)

```sh
cd software
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # or `ant auth login`
python -m tars.cli
```

Then chat:

```
You: /humor 100
TARS: Confirmed. Humor, 100 percent.
You: what are our odds of finishing this robot?
```

Without an API key it runs in offline mode with canned TARS quips, so you can
test the CLI immediately.

## Build status

- [x] Personality core (humor/honesty settings, Claude-powered chat, CLI)
- [x] Parametric CAD (`hardware/cad/tars.scad`, OpenSCAD)
- [x] Physics simulation — **it walks, robustly.** The build-target V3
      lift-and-swing gait, reworked into a crutch vault on 29 Sep 2026,
      walks 36 cm in 15 s (2.4 cm/s) at true MG996R torque and stays upright
      at every solver setting tested (`python v3_sim.py --robust`: time steps
      2 to 0.25 ms, three integrators, both friction cones, floor friction
      0.5-1.3, 20% weaker servos, body mass -10%/+20%). The IMU-balance walker
      and wheel mode do not work yet (`simulation/README.md`)
- [x] Research: proven community design identified (TARS-AI V3, 25.0cm,
      CC-BY-NC) — see `docs/research-notes.md`
- [ ] Parts ordered (`hardware/BOM.md`; prices live-verified 10 Aug 2026 — ready to order)
- [ ] Chassis printed (outsourced — `hardware/print-plan.md`)
- [ ] Voice: wake word → speech-to-text → TARS → text-to-speech
- [ ] Walking gait on real hardware
- [ ] Final assembly: it walks, it talks, it judges your plans
