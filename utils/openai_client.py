from __future__ import annotations

import os
from typing import Dict, Iterable, List, Optional, Tuple

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime
    OpenAI = None  # type: ignore


class OpenAIConfigurationError(RuntimeError):
    """Raised when the OpenAI client is not configured properly."""


class ChatGPTAdventureWriter:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.75,
    ) -> None:
        if OpenAI is None:
            raise ImportError("openai package is not installed. Install it to enable ChatGPT integration.")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise OpenAIConfigurationError(
                "OpenAI API key not configured. Set OPENAI_API_KEY in the environment or config/.env."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.temperature = temperature

    def enhance(
        self,
        outline: List[Tuple[str, object]],
        world_info: Optional[Dict[str, object]] = None,
        draft_text: Optional[str] = None,
    ) -> Tuple[str, str]:
        input_outline = _format_outline(outline)
        context = _format_world_info(world_info or {})
        base_prompt = _compose_prompt(input_outline, context, draft_text)

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": "You are a seasoned Traveller RPG referee who writes concise, game-ready adventure briefs.",
                },
                {
                    "role": "user",
                    "content": base_prompt,
                },
            ],
            temperature=self.temperature,
        )

        output_text = response.output_text.strip()
        title = _extract_title(output_text)
        return title, output_text


def _format_outline(outline: List[Tuple[str, object]]) -> str:
    lines = []
    for category, option in outline:
        name = getattr(option, "name", str(option))
        lines.append(f"{category}: {name}")
    return "\n".join(lines)


def _format_world_info(world_info: Dict[str, object]) -> str:
    parts: List[str] = []
    if sector := world_info.get("sector_name"):
        parts.append(f"Sector: {sector}")
    if system_hex := world_info.get("system_hex"):
        parts.append(f"System Hex: {system_hex}")
    planet = world_info.get("planet") or {}
    if name := planet.get("name"):
        parts.append(f"Planet: {name}")
    if hex_code := planet.get("hex"):
        parts.append(f"Planet Hex: {hex_code}")
    if uwp := planet.get("uwp"):
        parts.append(f"UWP: {uwp}")
    parsed = planet.get("parsed_uwp") or {}
    if parsed:
        parts.append(
            "Atmosphere: "
            + str(parsed.get("atmosphere"))
        )
        parts.append(
            "Hydrographics: "
            + str(parsed.get("hydrographics"))
        )
        parts.append(
            "Population Code: "
            + str(parsed.get("population"))
        )
    return "\n".join(parts)


def _compose_prompt(outline: str, context: str, draft_text: Optional[str]) -> str:
    prompt = [
        "Using the Traveller tabletop RPG tone, expand the following adventure outline into a polished adventure brief.",
        "Include sections: Hook, Background, Key NPCs, Important Locations, Scenes/Complications, Rewards." ,
        "Keep it practical for referees (no excessive prose).",
    ]
    if context:
        prompt.append("World Context:\n" + context)
    prompt.append("Outline:\n" + outline)
    if draft_text:
        prompt.append("Existing Draft (refine and expand it):\n" + draft_text)
    return "\n\n".join(prompt)


def _extract_title(text: str) -> str:
    for line in text.splitlines():
        lower = line.lower()
        if lower.startswith("title:"):
            return line.split(":", 1)[1].strip()
        if lower.startswith("##"):
            return line.lstrip("# ").strip()
    return "Enhanced Adventure"


__all__ = ["ChatGPTAdventureWriter", "OpenAIConfigurationError"]
