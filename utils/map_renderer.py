from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import requests
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap


# ---------------------------------------------------------------------------
# UWP helpers
# ---------------------------------------------------------------------------


ATMOSPHERE_CLASSES = {
    0: "Vacuum",
    1: "Trace",
    2: "Very Thin",
    3: "Very Thin/Tainted",
    4: "Thin",
    5: "Thin/Tainted",
    6: "Standard",
    7: "Standard/Tainted",
    8: "Dense",
    9: "Dense/Tainted",
    10: "Dense/High",
    11: "Exotic",
    12: "Corrosive",
    13: "Insidious",
    14: "Low",
    15: "Unusual",
}


def parse_uwp(uwp: str) -> Dict[str, object]:
    uwp = uwp.strip().upper()
    if len(uwp) < 9 or "-" not in uwp:
        raise ValueError(f"Invalid UWP string: {uwp}")

    body, _, tech = uwp.partition("-")
    body = body.ljust(8, "0")

    def hx(char: str) -> int:
        try:
            return int(char, 16)
        except ValueError:
            return 0

    return {
        "starport": body[0],
        "size": hx(body[1]),
        "atmosphere": hx(body[2]),
        "hydrographics": hx(body[3]),
        "population": hx(body[4]),
        "government": hx(body[5]),
        "law": hx(body[6]),
        "tech": hx(tech[0]) if tech else 0,
    }


def world_radius_km(size: int) -> int:
    lookup = {
        0: 800,
        1: 1600,
        2: 2400,
        3: 3200,
        4: 4000,
        5: 4800,
        6: 5600,
        7: 6400,
        8: 7200,
        9: 8000,
        10: 8800,
    }
    return lookup.get(max(0, min(size, 10)), 7200)


def estimate_base_temperature(size: int, atmo: int) -> float:
    t = -10.0 + (size / 10.0) * 20.0
    if atmo in {0, 1, 2, 3}:
        t -= 20
    if atmo in {10}:
        t += 10
    if atmo in {11, 12, 13}:
        t += 25
    return max(-30.0, min(t + 10.0, 45.0))


# ---------------------------------------------------------------------------
# Hex grid helpers
# ---------------------------------------------------------------------------


@dataclass
class HexCell:
    q: int
    r: int
    elevation: float = 0.0
    is_ocean: bool = False
    temperature: float = 0.0
    moisture: float = 0.0
    terrain: str = "Bare Rock"
    color: str = "#A59B8F"
    feature: Optional[str] = None


class HexGrid:
    def __init__(self, cols: int, rows: int, wrap: bool = True) -> None:
        self.cols = cols
        self.rows = rows
        self.wrap = wrap
        self.cells: Dict[Tuple[int, int], HexCell] = {}
        for r in range(rows):
            for q in range(cols):
                self.cells[(q, r)] = HexCell(q=q, r=r)

    def __iter__(self):
        return iter(self.cells.values())

    def get(self, q: int, r: int) -> HexCell:
        if self.wrap:
            q %= self.cols
        if not (0 <= r < self.rows):
            raise KeyError((q, r))
        return self.cells[(q, r)]


# ---------------------------------------------------------------------------
# Noise utilities
# ---------------------------------------------------------------------------


def hash_noise(seed: int, x: int, y: int) -> float:
    h = seed
    h ^= (x + 0x9e3779b9 + (h << 6) + (h >> 2))
    h ^= (y + 0x9e3779b9 + (h << 6) + (h >> 2))
    h &= 0xFFFFFFFF
    return (h / 0xFFFFFFFF) * 2.0 - 1.0


def fbm_noise(seed: int, x: float, y: float, octaves: int = 4, lacunarity: float = 2.0, gain: float = 0.5) -> float:
    value = 0.0
    amplitude = 1.0
    freq = 1.0
    for _ in range(octaves):
        xi = int(x * freq)
        yi = int(y * freq)
        value += amplitude * hash_noise(seed, xi, yi)
        freq *= lacunarity
        amplitude *= gain
    return value


# ---------------------------------------------------------------------------
# Planet map generation
# ---------------------------------------------------------------------------


TERRAIN_COLORS = {
    "Deep Ocean": "#0B3D91",
    "Shallow Sea": "#1F78B4",
    "Ice Cap": "#B5E3F4",
    "Glacier": "#D6F0FF",
    "Tundra": "#C7D9B7",
    "Bare Rock": "#A59B8F",
    "Desert": "#E7C873",
    "Semi-Arid": "#D9BA7D",
    "Savanna": "#C3C66A",
    "Grassland": "#9CCD6D",
    "Light Forest": "#6FB96F",
    "Dense Forest": "#3A8F52",
    "Jungle": "#1F6F45",
    "Swamp": "#4C8C72",
    "Hills": "#9F8E6B",
    "Mountains": "#7B6A58",
    "Volcanic": "#5A3A3A",
    "Salt Flat": "#EDE6D9",
    "Urban/Metro": "#6E6E6E",
    "Starport": "#444444",
}


def generate_planet_hex_map(planet: Dict[str, object], width: int = 48, height: int = 32) -> Dict[str, object]:
    uwp = parse_uwp(str(planet.get("UWP", planet.get("uwp", ""))))
    world_name = str(planet.get("name", planet.get("Name", ""))) or "Unnamed"

    seed = _seed_from_identifiers(world_name, str(planet.get("sector_id", "")), str(planet.get("hex", "")))
    rng = random.Random(seed)

    grid = HexGrid(width, height, wrap=True)

    radius = world_radius_km(uwp["size"])
    hydro_fraction = max(0.0, min(uwp["hydrographics"] / 10.0, 1.0))
    base_temp = estimate_base_temperature(uwp["size"], uwp["atmosphere"])

    plate_seed = [_random_vec2(rng) for _ in range(max(4, min(10, int(radius / 1600))))]

    base_heights: Dict[Tuple[int, int], float] = {}
    min_h = float("inf")
    max_h = float("-inf")
    for cell in grid:
        h = _plate_height(cell.q, cell.r, plate_seed)
        h += fbm_noise(seed, cell.q / width, cell.r / height, octaves=5)
        base_heights[(cell.q, cell.r)] = h
        min_h = min(min_h, h)
        max_h = max(max_h, h)

    # Normalize heights 0..1
    for key, h in base_heights.items():
        base_heights[key] = (h - min_h) / (max_h - min_h + 1e-6)

    threshold = _find_height_threshold(base_heights.values(), hydro_fraction)
    for cell in grid:
        h = base_heights[(cell.q, cell.r)]
        cell.elevation = h - threshold
        cell.is_ocean = cell.elevation < 0

    # Temperature and moisture
    for cell in grid:
        lat = _latitude_from_row(cell.r, grid.rows)
        lapse = -12.0 * max(0.0, cell.elevation)
        atmo_mod = _atmosphere_temp_modifier(uwp["atmosphere"])
        cell.temperature = base_temp + _latitudinal_profile(lat) + lapse + atmo_mod
        cell.moisture = _approx_moisture(cell, base_heights, grid, hydro_fraction)

    _assign_biomes(grid, rng, uwp)
    _add_urban_features(grid, rng, uwp)

    hexes = []
    for cell in grid:
        hexes.append({
            "q": cell.q,
            "r": cell.r,
            "terrain": cell.terrain,
            "color": TERRAIN_COLORS.get(cell.terrain, "#000000"),
            "elev": round(cell.elevation, 3),
            "temp": round(cell.temperature, 1),
            "moist": round(cell.moisture, 2),
            "feature": cell.feature,
        })

    return {
        "seed": seed,
        "uwp": planet.get("UWP", planet.get("uwp", "")),
        "cols": width,
        "rows": height,
        "wrap": "cylindrical",
        "hexes": hexes,
    }


def render_planet_hex_map_hexes(hex_map: Dict[str, object], tile_size: int = 18) -> QPixmap:
    cols = hex_map["cols"]
    rows = hex_map["rows"]
    width = int(tile_size * 1.5 * cols + tile_size)
    height = int(math.sqrt(3) * tile_size * (rows + 1))

    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor("#000000"))

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    for hex in hex_map["hexes"]:
        center = _hex_to_pixel(hex["q"], hex["r"], tile_size)
        polygon = _hexagon(center, tile_size - 1)
        color = QColor(hex["color"])
        painter.setBrush(color)
        painter.setPen(QPen(QColor("#202020"), 1))
        painter.drawPolygon(polygon)

    painter.end()
    return QPixmap.fromImage(image)


# ---------------------------------------------------------------------------
# System map generation
# ---------------------------------------------------------------------------


def generate_system_map(system_name: str, main_world: Dict[str, object]) -> QPixmap:
    width, height = 720, 420
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor("#060b10"))

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(QColor("#304050"), 1))

    center = QPointF(110, height / 2)
    painter.setBrush(QColor("#f2c84b"))
    painter.drawEllipse(center, 22, 22)

    total_worlds = max(5, int(main_world.get("worlds", 0) or 6))
    max_distance = 260
    text_color = QColor("#d6e3f0")
    painter.setPen(QPen(QColor("#1f2933"), 1))

    for idx in range(1, total_worlds + 1):
        orbit_radius = (idx / (total_worlds + 1)) * max_distance + 35
        painter.drawEllipse(center, orbit_radius, orbit_radius * 0.75)

    painter.setPen(QPen(text_color, 1))
    painter.setBrush(QColor("#58a6ff"))

    rng = random.Random(_seed_from_identifiers(system_name, str(main_world.get("UWP", ""))))
    for idx in range(1, total_worlds + 1):
        angle = math.pi / 6 * idx
        orbit_radius = (idx / (total_worlds + 1)) * max_distance + 35
        x = center.x() + orbit_radius * math.cos(angle)
        y = center.y() + orbit_radius * math.sin(angle) * 0.75
        size = 10 + rng.randint(-2, 4)
        painter.setBrush(QColor(_planet_color_for_orbit(idx, main_world)))
        painter.drawEllipse(QPointF(x, y), size, size)

        label = f"{main_world.get('name', 'World')} {idx}"
        if idx == 1:
            label = str(main_world.get('name', 'Main World'))
        uwp = str(main_world.get("UWP", ""))
        painter.setPen(text_color)
        painter.setFont(QFont("DejaVu Sans", 9))
        painter.drawText(QPointF(x + size + 4, y + size), f"{label}\n{uwp}")

    painter.end()
    return QPixmap.fromImage(image)


def _planet_color_for_orbit(idx: int, main_world: Dict[str, object]) -> str:
    atmos = int(parse_uwp(str(main_world.get("UWP", "")))['atmosphere'])
    palette = ["#6fa8dc", "#93c47d", "#ffd966", "#d5a6bd", "#f4cccc", "#cfe2f3"]
    return palette[idx % len(palette)] if atmos else "#888888"


# ---------------------------------------------------------------------------
# Sector map download/render
# ---------------------------------------------------------------------------


SECTOR_CACHE_DIR = Path("assets/sector_maps")
SECTOR_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def render_sector_from_api(sector_name: str, style: str = "poster") -> Optional[QPixmap]:
    cache_file = SECTOR_CACHE_DIR / f"{sector_name.replace(' ', '_')}_{style}.png"
    if cache_file.exists():
        return QPixmap(str(cache_file))

    url = "https://travellermap.com/data/sector/image"
    try:
        response = requests.get(url, params={"sector": sector_name, "style": style}, timeout=20)
        response.raise_for_status()
        cache_file.write_bytes(response.content)
        return QPixmap(str(cache_file))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Internal helper implementations
# ---------------------------------------------------------------------------


def _seed_from_identifiers(*identifiers: str) -> int:
    joined = "|".join(str(i) for i in identifiers if i)
    return hash(joined) & 0xFFFFFFFF


def _random_vec2(rng: random.Random) -> Tuple[float, float]:
    return rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)


def _plate_height(q: int, r: int, plates: Sequence[Tuple[float, float]]) -> float:
    total = 0.0
    for px, py in plates:
        total += math.cos(q * px + r * py)
    return total / len(plates)


def _find_height_threshold(values: Iterable[float], water_fraction: float) -> float:
    ordered = sorted(values)
    index = int(len(ordered) * water_fraction)
    index = max(0, min(len(ordered) - 1, index))
    return ordered[index]


def _latitude_from_row(r: int, rows: int) -> float:
    return ((r / (rows - 1)) * 180.0) - 90.0


def _latitudinal_profile(latitude: float) -> float:
    return 25.0 * math.cos(math.radians(latitude))


def _atmosphere_temp_modifier(atmo: int) -> float:
    if atmo in {0, 1, 2, 3}:
        return -20.0
    if atmo in {11, 12, 13}:
        return 15.0
    return 0.0


def _approx_moisture(cell: HexCell, base_heights: Dict[Tuple[int, int], float], grid: HexGrid, hydro_fraction: float) -> float:
    ocean_bonus = 0.6 if cell.is_ocean else 0.0
    lat = abs(_latitude_from_row(cell.r, grid.rows))
    lat_factor = max(0.0, 1.0 - (lat / 90.0))
    elevation_penalty = max(0.0, cell.elevation)
    return max(0.0, min(1.0, ocean_bonus + lat_factor - elevation_penalty))


def _assign_biomes(grid: HexGrid, rng: random.Random, uwp: Dict[str, object]) -> None:
    for cell in grid:
        if cell.is_ocean:
            depth = -cell.elevation
            cell.terrain = "Deep Ocean" if depth > 0.3 else "Shallow Sea"
            cell.color = TERRAIN_COLORS[cell.terrain]
            continue

        temp = cell.temperature
        moist = cell.moisture

        if temp < -10:
            cell.terrain = "Glacier" if cell.elevation > 0.2 else "Ice Cap"
        elif temp < 0:
            cell.terrain = "Tundra"
        elif moist < 0.1 and temp > 10:
            cell.terrain = "Desert" if rng.random() > 0.1 else "Salt Flat"
        elif cell.elevation > 0.25:
            cell.terrain = "Volcanic" if rng.random() < 0.05 else "Mountains"
        elif cell.elevation > 0.15:
            cell.terrain = "Hills"
        elif moist < 0.2:
            cell.terrain = "Semi-Arid"
        elif moist < 0.35:
            cell.terrain = "Grassland"
        elif moist < 0.5:
            cell.terrain = "Light Forest"
        elif moist < 0.7:
            cell.terrain = "Dense Forest"
        else:
            cell.terrain = "Swamp" if temp < 25 else "Jungle"

        cell.color = TERRAIN_COLORS.get(cell.terrain, "#A59B8F")


def _add_urban_features(grid: HexGrid, rng: random.Random, uwp: Dict[str, object]) -> None:
    pop = uwp.get("population", 0)
    if pop <= 0:
        return
    city_count = 2 + max(0, pop // 2) + rng.randint(0, 2)
    potential_sites = [cell for cell in grid if not cell.is_ocean and cell.temperature > -5]
    rng.shuffle(potential_sites)

    selected = potential_sites[:city_count]
    for cell in selected:
        cell.terrain = "Urban/Metro"
        cell.color = TERRAIN_COLORS[cell.terrain]

    starport = uwp.get("starport", "X")
    if selected:
        site = selected[0] if starport in {"A", "B", "C"} else rng.choice(selected)
        site.terrain = "Starport"
        site.color = TERRAIN_COLORS[site.terrain]
        site.feature = f"Port-{starport}"


# ---------------------------------------------------------------------------
# Hex geometry helpers
# ---------------------------------------------------------------------------


def _hex_to_pixel(col: int, row: int, size: int) -> QPointF:
    x = size * (3 / 2 * col) + size
    y = size * math.sqrt(3) * (row + 0.5 * (col % 2)) + size
    return QPointF(x, y)


def _hexagon(center: QPointF, size: float) -> List[QPointF]:
    points = []
    for i in range(6):
        angle = math.pi / 180 * (60 * i - 30)
        x = center.x() + size * math.cos(angle)
        y = center.y() + size * math.sin(angle)
        points.append(QPointF(x, y))
    return points


__all__ = [
    "ATMOSPHERE_CLASSES",
    "parse_uwp",
    "generate_planet_hex_map",
    "render_planet_hex_map_hexes",
    "generate_system_map",
    "render_sector_from_api",
]
