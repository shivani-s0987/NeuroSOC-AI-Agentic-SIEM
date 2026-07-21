from __future__ import annotations

from typing import Any


class AIProvider:
    def generate(self, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "content": f"[Model generated] {prompt}",
            "verified_facts": [],
            "warnings": ["Generated content must be reviewed by an analyst before action."],
        }


def build_assistant_response(prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    provider = AIProvider()
    return provider.generate(prompt, context)
