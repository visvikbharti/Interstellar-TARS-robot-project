"""Terminal chat with TARS.

Run from the software/ directory:  python -m tars.cli
"""

from __future__ import annotations

import re
import sys

from .brain import MockBrain, make_brain
from .settings import TarsSettings

BANNER = r"""
  _____  _    ____  ____
 |_   _|/ \  |  _ \/ ___|
   | | / _ \ | |_) \___ \
   | |/ ___ \|  _ < ___) |
   |_/_/   \_\_| \_\____/
"""

HELP = """\
Commands:
  /humor <0-100>     set humor level        (movie default: 75)
  /honesty <0-100>   set honesty level      (movie default: 90)
  /settings          show current settings
  /reset             clear conversation history
  /help              this message
  /quit              power down TARS
Anything else is said to TARS.
"""

# Let people talk to TARS the way Cooper does: "humor to 60 percent"
SPOKEN_SETTING = re.compile(
    r"\b(humor|honesty)\b.*?\b(?:to|at|setting)?\s*(\d{1,3})\s*(?:percent|%)", re.IGNORECASE
)


def handle_setting_change(brain, name: str, value: int) -> None:
    try:
        brain.settings.set(name, value)
        brain.settings.save()
        print(f"TARS: Confirmed. {name.capitalize()}, {value} percent.")
    except ValueError as e:
        print(f"TARS: Negative. {e}")


def main() -> None:
    print(BANNER)
    settings = TarsSettings.load()
    brain = make_brain(settings)

    if isinstance(brain, MockBrain):
        print("  [offline mode — no Anthropic credentials found; using canned replies]")
    print(f"  humor {settings.humor}%  |  honesty {settings.honesty}%  |  /help for commands\n")

    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTARS: Powering down. Try not to miss me.")
            break
        if not user:
            continue

        if user.startswith("/"):
            parts = user.split()
            cmd = parts[0].lower()
            if cmd in ("/quit", "/exit"):
                print("TARS: Powering down. See you, Cooper.")
                break
            elif cmd == "/help":
                print(HELP)
            elif cmd == "/settings":
                print(f"TARS: Humor {settings.humor} percent. Honesty {settings.honesty} percent.")
            elif cmd == "/reset":
                brain.reset()
                print("TARS: Memory wiped. Who are you, again?")
            elif cmd in ("/humor", "/honesty") and len(parts) == 2 and parts[1].isdigit():
                handle_setting_change(brain, cmd[1:], int(parts[1]))
            else:
                print("TARS: Unrecognized command. /help lists what I respond to.")
            continue

        # Spoken-style setting changes ("humor to 60 percent") work too
        m = SPOKEN_SETTING.search(user)
        if m:
            handle_setting_change(brain, m.group(1).lower(), int(m.group(2)))
            continue

        print("TARS: ", end="", flush=True)
        for chunk in brain.reply(user):
            print(chunk, end="", flush=True)
        print()


if __name__ == "__main__":
    sys.exit(main())
