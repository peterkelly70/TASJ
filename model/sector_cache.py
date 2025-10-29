import json
from pathlib import Path
from typing import List, Dict


DEFAULT_CACHE_PATH = Path("config/sector_cache.json")


def load_sector_cache(cache_path: Path = DEFAULT_CACHE_PATH) -> List[Dict[str, str]]:
    """Load cached sector metadata from disk."""
    if not cache_path.exists():
        return []

    try:
        with cache_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
    except json.JSONDecodeError:
        return []
    return []


def save_sector_cache(sectors: List[Dict[str, str]], cache_path: Path = DEFAULT_CACHE_PATH) -> None:
    """Persist the supplied sector metadata to disk."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as fh:
        json.dump(sectors, fh, ensure_ascii=False, indent=2)
