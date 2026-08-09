# TARS — Mini Walking Robot (Interstellar)

A ~25–30cm, 3D-printed, walking and talking replica of TARS from *Interstellar*.
Raspberry Pi brain, servo-driven gait, Claude-powered personality with the
movie's adjustable **humor** and **honesty** settings.

> Cooper: "Hey TARS, what's your honesty parameter?"
> TARS: "Ninety percent."

## Project layout

```
software/    TARS's brain — personality, chat, (soon) voice + servo control
hardware/    Bill of materials, wiring, print settings
docs/        Build plan, research notes, assembly guide
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
- [x] Physics simulation — **it walks!** 51cm/10s in MuJoCo with an IMU
      balance loop (`simulation/`, watch with `mjpython gait_sim.py --gui`)
- [x] Research: proven community design identified (TARS-AI V3, 25.0cm,
      CC-BY-NC) — see `docs/research-notes.md`
- [ ] Parts ordered (`hardware/BOM.md`; India pricing in progress)
- [ ] Chassis printed
- [ ] Voice: wake word → speech-to-text → TARS → text-to-speech
- [ ] Walking gait on real hardware
- [ ] Final assembly: it walks, it talks, it judges your plans
