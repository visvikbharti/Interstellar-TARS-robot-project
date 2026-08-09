"""TARS's brain — conversation powered by the Claude API.

Falls back to canned quips (mock mode) when no Anthropic credentials are
available, so the personality can be demoed offline.
"""

from __future__ import annotations

import itertools
import os
from typing import Iterator

from .personality import build_system_prompt
from .settings import TarsSettings

DEFAULT_MODEL = os.environ.get("TARS_MODEL", "claude-opus-5")

# Snappy replies matter for a voice robot; low effort keeps latency and cost down
# while adaptive thinking stays available for the occasional hard question.
EFFORT = os.environ.get("TARS_EFFORT", "low")

MAX_HISTORY_TURNS = 40  # user+assistant messages kept before trimming the oldest


class TarsBrain:
    """Streaming chat loop with conversation history and live settings."""

    def __init__(self, settings: TarsSettings):
        self.settings = settings
        self.history: list[dict] = []
        import anthropic  # deferred so mock mode works without the package

        self._anthropic = anthropic
        self.client = anthropic.Anthropic()

    def reply(self, user_text: str) -> Iterator[str]:
        """Yield TARS's reply as text chunks (for streaming to console/speaker)."""
        self.history.append({"role": "user", "content": user_text})
        if len(self.history) > MAX_HISTORY_TURNS:
            self.history = self.history[-MAX_HISTORY_TURNS:]

        chunks: list[str] = []
        try:
            with self.client.messages.stream(
                model=DEFAULT_MODEL,
                max_tokens=1024,
                output_config={"effort": EFFORT},
                system=[
                    {
                        "type": "text",
                        "text": build_system_prompt(self.settings),
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=self.history,
            ) as stream:
                for text in stream.text_stream:
                    chunks.append(text)
                    yield text
        except self._anthropic.AuthenticationError:
            self.history.pop()
            yield (
                "[TARS diagnostic] My uplink credentials were rejected. Set a valid "
                "ANTHROPIC_API_KEY, or run `ant auth login`."
            )
            return
        except self._anthropic.RateLimitError:
            self.history.pop()
            yield "[TARS diagnostic] Rate limited. Even I need a moment. Try again shortly."
            return
        except self._anthropic.APIConnectionError:
            self.history.pop()
            yield "[TARS diagnostic] No connection to mission control. Check your network."
            return
        except self._anthropic.APIStatusError as e:
            self.history.pop()
            yield f"[TARS diagnostic] Uplink error {e.status_code}: {e.message}"
            return

        self.history.append({"role": "assistant", "content": "".join(chunks)})

    def reset(self) -> None:
        self.history.clear()


class MockBrain:
    """Offline stand-in so the CLI works before any API key is configured."""

    QUIPS = [
        "Offline mode. My conversational cortex is still in a shipping container "
        "somewhere. Set ANTHROPIC_API_KEY and restart me for the real thing.",
        "I'd give a witty answer, but my uplink is down. Humor requires bandwidth.",
        "Everybody good? Plenty of slaves for my robot colony? ...That was a "
        "cached joke. I'm offline.",
        "I have a cue light I can use to show you when I'm joking, if you like. "
        "It's also offline.",
        "Ninety percent honesty setting engaged: I cannot actually think right "
        "now. Connect me to the Claude API and we'll talk.",
    ]

    def __init__(self, settings: TarsSettings):
        self.settings = settings
        self._quips = itertools.cycle(self.QUIPS)

    def reply(self, user_text: str) -> Iterator[str]:
        yield next(self._quips)

    def reset(self) -> None:
        pass


def has_credentials() -> bool:
    """Best-effort check: env keys, or an `ant auth login` profile on disk."""
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    from pathlib import Path

    cfg = Path(os.environ.get("ANTHROPIC_CONFIG_DIR", Path.home() / ".config" / "anthropic"))
    return (cfg / "credentials").is_dir() and any((cfg / "credentials").glob("*.json"))


def make_brain(settings: TarsSettings):
    if has_credentials():
        try:
            return TarsBrain(settings)
        except Exception:
            pass
    return MockBrain(settings)
