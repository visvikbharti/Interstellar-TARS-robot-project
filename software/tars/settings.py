"""TARS's adjustable parameters, straight from the movie.

Cooper: "Humor, seventy-five percent."
TARS:   "Confirmed. Self-destruct sequence in T minus 10, 9, 8..."
Cooper: "Let's make that sixty percent."
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent.parent / "tars_settings.json"


@dataclass
class TarsSettings:
    humor: int = 75    # Cooper dialed it down from 100 after one too many jokes
    honesty: int = 90  # "Absolute honesty isn't always the most diplomatic..."

    def set(self, name: str, value: int) -> None:
        if name not in ("humor", "honesty"):
            raise ValueError(f"No such setting: {name}")
        if not 0 <= value <= 100:
            raise ValueError(f"{name} must be between 0 and 100")
        setattr(self, name, value)

    def save(self, path: Path = SETTINGS_FILE) -> None:
        path.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls, path: Path = SETTINGS_FILE) -> "TarsSettings":
        if path.exists():
            try:
                data = json.loads(path.read_text())
                return cls(**{k: v for k, v in data.items() if k in ("humor", "honesty")})
            except (json.JSONDecodeError, TypeError):
                pass
        return cls()
