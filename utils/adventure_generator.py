from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from utils.map_renderer import ATMOSPHERE_CLASSES


SCENARIO_TABLE_PATH = Path("apis/scenario_tables.scsv")


@dataclass
class ScenarioOption:
    option_id: int
    name: str
    reference: Optional[int]


@dataclass
class ScenarioCategory:
    category_id: int
    name: str
    phase: int
    options: List[ScenarioOption]


class AdventureGenerator:
    def __init__(self, table_path: Path = SCENARIO_TABLE_PATH) -> None:
        self.categories: Dict[int, ScenarioCategory] = {}
        self._load_tables(table_path)

    def _load_tables(self, table_path: Path) -> None:
        if not table_path.exists():
            raise FileNotFoundError(f"Scenario table not found: {table_path}")

        categories: Dict[int, ScenarioCategory] = {}
        with table_path.open("r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                try:
                    phase = int(row.get("Phase", "0"))
                    category_id = int(row.get("CategoryID", "0"))
                    category_name = row.get("CategoryName", "")
                    option_id = int(row.get("OptionID", "0"))
                    option_name = row.get("OptionName", "")
                    reference_raw = row.get("Reference", "")
                    reference = int(reference_raw) if reference_raw and reference_raw.isdigit() else None
                except ValueError:
                    continue

                category = categories.setdefault(
                    category_id,
                    ScenarioCategory(category_id=category_id, name=category_name, phase=phase, options=[]),
                )
                category.options.append(ScenarioOption(option_id=option_id, name=option_name, reference=reference))

        self.categories = categories

    def generate(self, rng: Optional[random.Random] = None) -> List[Tuple[str, ScenarioOption]]:
        rng = rng or random.Random()
        result: List[Tuple[str, ScenarioOption]] = []
        visited: Set[int] = set()
        queue: List[int] = [1]

        while queue:
            category_id = queue.pop(0)
            if category_id in visited:
                continue
            category = self.categories.get(category_id)
            if not category or not category.options:
                continue

            option = rng.choice(category.options)
            result.append((category.name, option))
            visited.add(category_id)

            if option.reference and option.reference not in visited:
                queue.append(option.reference)

        return result


def format_adventure_outline(outline: List[Tuple[str, ScenarioOption]], context_lines: Optional[List[str]] = None) -> str:
    lines: List[str] = []
    if context_lines:
        lines.extend(context_lines)
        lines.append("")

    lines.append("Adventure Hook Outline:")
    for category_name, option in outline:
        lines.append(f"- {category_name}: {option.name}")

    return "\n".join(lines)


def outline_to_map(outline: List[Tuple[str, ScenarioOption]]) -> Dict[str, List[ScenarioOption]]:
    mapping: Dict[str, List[ScenarioOption]] = {}
    for category, option in outline:
        mapping.setdefault(category, []).append(option)
    return mapping


def generate_adventure_story(
    outline: List[Tuple[str, ScenarioOption]],
    world_info: Optional[Dict[str, object]] = None,
    context_lines: Optional[List[str]] = None,
    rng: Optional[random.Random] = None,
) -> Tuple[str, str]:
    rng = rng or random.Random()
    outline_map = outline_to_map(outline)

    primary_type = _first_option_name(outline_map, "General Type of Scenario", default="Opportunity")
    sub_focus = _first_available(outline_map, [
        "Type of Investigation",
        "Type of Survival",
        "Type of Exploration",
        "Type of Assault",
        "Type of Trade",
        "Type of Sacrifice",
    ])

    weird_item = _first_option_name(outline_map, "Weird item", default=None)
    kidnap = _first_option_name(outline_map, "Kidnap", default=None)
    moved = _first_option_name(outline_map, "Moved", default=None)
    cargo = _first_option_name(outline_map, "Cargo", default=None)

    world_summary, environment_details = _describe_world(world_info)

    title = _compose_title(primary_type, sub_focus, weird_item, world_info, rng)

    lines: List[str] = []
    if context_lines:
        lines.extend(context_lines)
        lines.append("")

    lines.append(f"Title: {title}")
    lines.append("")

    hook = _build_hook(primary_type, sub_focus, moved, weird_item, environment_details, rng)
    lines.append("Hook:")
    lines.append(f"  {hook}")
    lines.append("")

    background = _build_background(outline_map, environment_details, rng)
    lines.append("Background:")
    for paragraph in background:
        lines.append(f"  {paragraph}")
    lines.append("")

    key_npcs = _generate_npcs(primary_type, outline_map, environment_details, rng)
    lines.append("Key NPCs:")
    for npc in key_npcs:
        lines.append(f"  - {npc}")
    lines.append("")

    key_locations = _generate_locations(outline_map, environment_details, rng)
    lines.append("Important Locations:")
    for location in key_locations:
        lines.append(f"  - {location}")
    lines.append("")

    complications = _build_complications(outline_map, environment_details, rng)
    lines.append("Scenes & Complications:")
    for item in complications:
        lines.append(f"  - {item}")
    lines.append("")

    rewards = _build_rewards(outline_map, cargo, world_info, rng)
    lines.append("Rewards & Follow-Ups:")
    for item in rewards:
        lines.append(f"  - {item}")

    if world_summary:
        lines.append("")
        lines.append("World Summary:")
        for entry in world_summary:
            lines.append(f"  - {entry}")

    return title, "\n".join(lines)


def _first_option_name(outline_map: Dict[str, List[ScenarioOption]], key: str, default: Optional[str] = None) -> Optional[str]:
    options = outline_map.get(key)
    if not options:
        return default
    return options[0].name


def _first_available(outline_map: Dict[str, List[ScenarioOption]], keys: List[str]) -> Optional[str]:
    for key in keys:
        name = _first_option_name(outline_map, key)
        if name:
            return name
    return None


SYLLABLES = [
    "ar", "ba", "cor", "dun", "el", "fa", "gan", "hal", "iv", "jor",
    "kel", "lor", "mar", "nel", "or", "pra", "quin", "ron", "sar", "tor",
    "ur", "val", "wyn", "xer", "yor", "zan"
]

SURNAME_FRAGMENTS = [
    "-an", "-es", "-ir", "-on", "-us", "-yr", "-ai", "-en", "-or", "-ul"
]


def _random_name(rng: random.Random) -> str:
    parts = rng.randint(2, 3)
    name = "".join(rng.choice(SYLLABLES) for _ in range(parts))
    surname = rng.choice(SYLLABLES).capitalize() + rng.choice(SURNAME_FRAGMENTS)
    return f"{name.capitalize()} {surname.capitalize()}"


GOVERNMENT_CODES = {
    0: "No government",
    1: "Company/Corporation",
    2: "Participating Democracy",
    3: "Self-perpetuating Oligarchy",
    4: "Representative Democracy",
    5: "Feudal Technocracy",
    6: "Captive Government",
    7: "Balkanized",
    8: "Civil Service Bureaucracy",
    9: "Impersonal Bureaucracy",
    10: "Charismatic Dictator",
    11: "Non-Charismatic Leader",
    12: "Charismatic Oligarchy",
    13: "Religious Dictatorship",
    14: "Religious Autocracy",
    15: "Totalitarian Oligarchy",
}


def _describe_world(world_info: Optional[Dict[str, object]]) -> Tuple[List[str], Dict[str, object]]:
    if not world_info:
        return [], {}

    summary: List[str] = []
    details: Dict[str, object] = {}

    sector_name = world_info.get("sector_name")
    system_hex = world_info.get("system_hex")
    planet_info = world_info.get("planet") or {}

    if sector_name:
        details["sector_name"] = sector_name
    if system_hex:
        details["system_hex"] = system_hex

    if planet_info:
        summary.append(f"Planet: {planet_info.get('name', 'Unnamed')}")
        if planet_info.get("hex"):
            summary.append(f"World Hex: {planet_info['hex']}")
        uwp = planet_info.get("uwp")
        if uwp:
            summary.append(f"UWP: {uwp}")
        parsed = planet_info.get("parsed_uwp")
        if parsed:
            atmos = parsed.get("atmosphere", 0)
            hydro = parsed.get("hydrographics", 0)
            pop = parsed.get("population", 0)
            gov = parsed.get("government", 0)
            atmos_desc = f"Atmosphere: {ATMOSPHERE_CLASSES.get(atmos, 'Unknown')}"
            hydro_desc = f"Hydrographics: {hydro * 10}% water"
            pop_desc = f"Population: {POP_DESCRIPTIONS.get(pop, 'Sparsely inhabited')}"
            gov_desc = f"Government: {GOVERNMENT_CODES.get(gov, 'Unclassified')}"
            summary.extend([atmos_desc, hydro_desc, gov_desc, pop_desc])
            details.update({
                "atmosphere": atmos,
                "hydrographics": hydro,
                "population_code": pop,
                "government": gov,
                "atmosphere_desc": ATMOSPHERE_CLASSES.get(atmos, 'Unknown'),
                "hydro_desc": hydro_desc,
                "population_desc": pop_desc,
                "government_desc": GOVERNMENT_CODES.get(gov, 'Unclassified'),
            })

    return summary, details


def _compose_title(primary_type: str, sub_focus: Optional[str], weird_item: Optional[str], world_info, rng: random.Random) -> str:
    planet_name = None
    if world_info and world_info.get("planet"):
        planet_name = world_info["planet"].get("name")
    base = primary_type or "Adventure"
    if sub_focus:
        base = f"{sub_focus} {base}" if rng.random() < 0.5 else f"{base} of {sub_focus}"
    if planet_name:
        base = f"{base} on {planet_name}"
    if weird_item and rng.random() < 0.6:
        base = f"{base}: {weird_item}"
    return base.title()


def _build_hook(primary_type: str, sub_focus: Optional[str], moved: Optional[str], weird_item: Optional[str], env: Dict[str, object], rng: random.Random) -> str:
    hook_bits = []
    hook_bits.append(f"{primary_type.upper()} assignment calling for skilled Travellers.")
    if sub_focus:
        hook_bits.append(f"Initial objective: {sub_focus.lower()}.")
    if moved:
        hook_bits.append(f"Recent intel suggests the subject was {moved.lower()}.")
    if weird_item:
        hook_bits.append(f"Key element: a {weird_item.lower()} defying local science.")
    if env.get("government_desc"):
        hook_bits.append(f"Authorities ({env['government_desc'].lower()}) are overwhelmed and discreet aid is valued.")
    return " ".join(hook_bits)


def _build_background(outline_map: Dict[str, List[ScenarioOption]], env: Dict[str, object], rng: random.Random) -> List[str]:
    paragraphs: List[str] = []
    investigation = _first_option_name(outline_map, "Type of Investigation")
    assault = _first_option_name(outline_map, "Type of Assault")
    survival = _first_option_name(outline_map, "Type of Survival")
    sacrifice = _first_option_name(outline_map, "Type of Sacrifice")

    core = "Rumours swirl around" if rng.random() < 0.5 else "Recent reports highlight"
    if investigation:
        core += f" a {investigation.lower()} that spiralled beyond control."
    else:
        core += " a dangerous opportunity with unclear stakes."
    paragraphs.append(core)

    if assault:
        paragraphs.append(f"A militant faction is organising a {assault.lower()} while the authorities look the other way.")
    if survival:
        paragraphs.append(f"Civilians on the ground face '{survival.lower()}' conditions and beg for assistance.")
    if sacrifice:
        paragraphs.append(f"Whispers say success demands sacrificing {sacrifice.lower()}.")

    if env.get("hydrographics") is not None:
        water = env["hydrographics"] * 10
        paragraphs.append(f"Local geography is shaped by {water}% water coverage; plan logistics accordingly.")

    return paragraphs


def _generate_npcs(primary_type: str, outline_map: Dict[str, List[ScenarioOption]], env: Dict[str, object], rng: random.Random) -> List[str]:
    npcs: List[str] = []
    roles = ["Point of Contact", "Antagonist", "Complication"]
    descriptors = [
        ("Point of Contact", "desperate official"),
        ("Antagonist", "ambitious rival"),
        ("Complication", "unexpected ally"),
    ]
    for role, archetype in descriptors:
        name = _random_name(rng)
        motivation = rng.choice([
            "protect their family",
            "claim political power",
            "profit from the chaos",
            "shield the innocent",
            "erase past mistakes",
        ])
        skill = rng.choice([
            "Astrogation-1", "Gun Combat-2", "Admin-1", "Science-2", "Streetwise-2", "Broker-1"])
        mission = rng.choice([
            "needs proof before acting",
            "wants the artefact secured",
            "demands justice",
            "offers clandestine support",
            "threatens to expose the Travellers",
        ])
        if role == "Antagonist" and outline_map.get("Murder"):
            mission = f"orchestrated {outline_map['Murder'][0].name.lower()} to justify harsher measures"
        npc_line = f"{role}: {name}, a {archetype} who {motivation}. Skills: {skill}. They {mission}."
        npcs.append(npc_line)
    return npcs


def _generate_locations(outline_map: Dict[str, List[ScenarioOption]], env: Dict[str, object], rng: random.Random) -> List[str]:
    locations: List[str] = []
    base_sites = [
        "labyrinthine industrial warrens",
        "crowded starport concourses",
        "abandoned transit tunnels",
        "orbital freight depots",
        "glass-domed civic plazas",
    ]
    if outline_map.get("Urban"):
        base_sites.insert(0, outline_map["Urban"][0].name.lower())
    if outline_map.get("Type of Exploration"):
        base_sites.insert(0, outline_map["Type of Exploration"][0].name.lower())
    for site in rng.sample(base_sites, k=3):
        hook = rng.choice([
            "guards are bribable",
            "environmental hazards complicate firefights",
            "locals share rumours for a price",
            "surveillance drones track movement",
            "ancient machinery hums ominously",
        ])
        locations.append(f"{site.title()} – {hook}.")
    return locations


def _build_complications(outline_map: Dict[str, List[ScenarioOption]], env: Dict[str, object], rng: random.Random) -> List[str]:
    complications: List[str] = []
    if outline_map.get("Who"):
        complications.append(f"The investigation reveals the culprit is {outline_map['Who'][0].name.lower()}.")
    if outline_map.get("Mental"):
        complications.append(f"Exposure to the artefact triggers {outline_map['Mental'][0].name.lower()} symptoms.")
    if outline_map.get("Hordes of the things"):
        complications.append(f"Enemy reinforcements arrive via {outline_map['Hordes of the things'][0].name.lower()}.")
    if outline_map.get("Kidnap"):
        complications.append(f"A victim ({outline_map['Kidnap'][0].name.lower()}) must be rescued alive.")
    if not complications:
        complications.append("Unexpected patrons offer conflicting rewards, forcing hard choices.")
    return complications


def _build_rewards(outline_map: Dict[str, List[ScenarioOption]], cargo: Optional[str], world_info: Optional[Dict[str, object]], rng: random.Random) -> List[str]:
    rewards: List[str] = []
    if cargo:
        rewards.append(f"Recovered cargo ({cargo.lower()}) can be sold for a tidy profit or returned for favour.")
    rewards.append("Official recognition and future contracts from grateful leaders.")
    rewards.append("Potential access to experimental tech – if the Travellers dare keep a sample.")
    rewards.append("Threat of retaliation from those who lost the artefact, setting up future sessions.")
    return rewards


__all__ = [
    "AdventureGenerator",
    "format_adventure_outline",
    "outline_to_map",
    "generate_adventure_story",
]
POP_DESCRIPTIONS = {
    0: "dozens of inhabitants",
    1: "hundreds of inhabitants",
    2: "thousands of inhabitants",
    3: "tens of thousands of inhabitants",
    4: "hundreds of thousands of inhabitants",
    5: "millions of inhabitants",
    6: "tens of millions of inhabitants",
    7: "hundreds of millions of inhabitants",
    8: "billions of inhabitants",
    9: "tens of billions of inhabitants",
    10: "hundreds of billions of inhabitants",
}
