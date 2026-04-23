import json
import re
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent.parent / "data.json"
DATA = json.loads(DATA_PATH.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def find_item(query: str):
    normalized_query = normalize(query)
    best = None

    for key, item in DATA.items():
        candidates = [
            key,
            item.get("name", ""),
            item.get("slug", ""),
            item.get("shortname", ""),
            *item.get("aliases", []),
        ]

        normalized_candidates = [normalize(candidate) for candidate in candidates if candidate]

        if normalized_query in normalized_candidates:
            return item

        if any(normalized_query in candidate for candidate in normalized_candidates):
            best = item

    return best


def reverse_calculate(resource: str, amount: int):
    resource_key = normalize(resource)
    results = []

    for item in DATA.values():
        recycle = item.get("recycle", {})

        if resource_key not in recycle:
            continue

        value = recycle[resource_key]
        needed = -(-amount // value)

        results.append(
            {
                "item": item["name"],
                "needed": needed,
                "value": value,
            }
        )

    return sorted(results, key=lambda row: (row["needed"], row["item"]))
