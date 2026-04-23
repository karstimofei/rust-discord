import argparse
import concurrent.futures
import json
import re
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"
SITEMAP_URL = "https://www.rustlab.gg/sitemap-items.xml"
REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
DEFAULT_WORKERS = 8
HEADERS = {
    "User-Agent": "rust-discord-bot-data-generator/1.0 (+https://github.com/karstimofei/rust-discord)"
}

NEXT_CHUNK_RE = re.compile(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', re.S)
SHORTNAME_RE = re.compile(r'"shortname":"([^"]+)","name":"([^"]+)"')

_thread_local = threading.local()


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def unique_strings(values: list[str]) -> list[str]:
    result = []
    seen = set()

    for value in values:
        cleaned = value.strip()
        normalized = normalize(cleaned)

        if not cleaned or not normalized or normalized in seen:
            continue

        seen.add(normalized)
        result.append(cleaned)

    return result


def build_aliases(name: str, slug: str, shortname: str | None) -> list[str]:
    parts = re.split(r"[^a-zA-Z0-9]+", name)
    acronym = "".join(part[0] for part in parts if part)

    aliases = [
        name,
        slug.replace("-", " "),
        slug.replace("-", "_"),
    ]

    if len([part for part in parts if part]) > 1 and len(acronym) > 1:
        aliases.append(acronym.lower())

    if shortname:
        aliases.extend(
            [
                shortname,
                shortname.replace(".", " "),
                shortname.replace(".", "_"),
                shortname.replace(".", ""),
            ]
        )

    return unique_strings(aliases)


def get_session() -> requests.Session:
    session = getattr(_thread_local, "session", None)

    if session is None:
        session = requests.Session()
        session.headers.update(HEADERS)
        _thread_local.session = session

    return session


def fetch_text(url: str) -> str:
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = get_session().get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(0.5 * attempt)

    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def load_item_slugs(limit: int | None = None) -> list[str]:
    xml_text = fetch_text(SITEMAP_URL)
    root = ET.fromstring(xml_text)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    urls = [node.text for node in root.findall(".//sm:loc", namespace)]
    slugs = [url.rstrip("/").split("/")[-1] for url in urls if url]

    if limit is not None:
        return slugs[:limit]

    return slugs


def decode_next_chunks(html: str) -> list[str]:
    return [bytes(chunk, "utf-8").decode("unicode_escape") for chunk in NEXT_CHUNK_RE.findall(html)]


def find_item_header(soup: BeautifulSoup) -> tuple[str, str | None, str | None]:
    title = soup.find("h1")
    if not title:
        raise ValueError("Item page does not contain h1")

    name = title.get_text(" ", strip=True)
    header_bits = list(title.parent.stripped_strings)

    category = header_bits[1] if len(header_bits) > 1 else None
    description = None

    for ancestor in title.parents:
        if getattr(ancestor, "name", None) != "div":
            continue

        paragraph = ancestor.find("p")
        if not paragraph:
            continue

        text = paragraph.get_text(" ", strip=True)
        if text and text != name:
            description = text
            break

    if not description:
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            description = meta["content"]

    return name, category, description


def extract_shortname(chunks: list[str]) -> str | None:
    for chunk in chunks:
        match = SHORTNAME_RE.search(chunk)
        if match:
            return match.group(1)

    return None


def parse_props_chunk(chunks: list[str]) -> dict[str, Any]:
    for chunk in chunks:
        if '"crafting":' not in chunk and '"recycling":' not in chunk and '"repair":' not in chunk:
            continue

        try:
            payload = json.loads(chunk.split(":", 1)[1])
        except (IndexError, json.JSONDecodeError):
            continue

        if isinstance(payload, list) and len(payload) >= 4 and isinstance(payload[3], dict):
            return payload[3]

    return {}


def normalize_resource_name(name: str) -> str:
    return normalize(name)


def list_to_resource_map(rows: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}

    if not isinstance(rows, list):
        return result

    for row in rows:
        if not isinstance(row, dict):
            continue

        item_name = row.get("item")
        amount = row.get("amount")

        if not item_name or amount in (None, ""):
            continue

        key = normalize_resource_name(str(item_name))
        result[key] = int(amount)

    return result


def clean_scalar(value: Any) -> Any:
    if value == "$undefined":
        return None

    return value


def parse_item(slug: str) -> tuple[str, dict[str, Any]]:
    url = f"https://www.rustlab.gg/item/{slug}"
    html = fetch_text(url)
    soup = BeautifulSoup(html, "html.parser")
    chunks = decode_next_chunks(html)

    name, category, description = find_item_header(soup)
    shortname = extract_shortname(chunks)
    props = parse_props_chunk(chunks)

    crafting = props.get("crafting")
    recycling = props.get("recycling")
    repair = props.get("repair")

    if not isinstance(crafting, dict):
        crafting = {}

    if not isinstance(recycling, dict):
        recycling = {}

    if not isinstance(repair, dict):
        repair = {}

    craft_materials = list_to_resource_map(crafting.get("materials") or [])
    repair_materials = list_to_resource_map(repair.get("materials") or [])
    recycle_radtown = list_to_resource_map(recycling.get("radtown") or [])
    recycle_safezone = list_to_resource_map(recycling.get("safezone") or [])
    recycle_standard = list_to_resource_map(recycling.get("standard") or [])

    if not recycle_radtown:
        recycle_radtown = recycle_standard

    item = {
        "name": name,
        "slug": slug,
        "shortname": shortname,
        "category": normalize(category) if category else None,
        "description": description,
        "aliases": build_aliases(name, slug, shortname),
        "craft": {
            "workbench": clean_scalar(crafting.get("workbench")),
            "craft_time": clean_scalar(crafting.get("craft_time")),
            "research_cost": clean_scalar(crafting.get("research_cost")),
            "tech_tree_cost": clean_scalar(crafting.get("tech_tree_cost")),
            "materials": craft_materials,
        },
        "recycle": recycle_radtown,
        "recycle_safezone": recycle_safezone,
        "repair": {
            "materials": repair_materials,
            "condition_loss_pct": clean_scalar(repair.get("condition_loss_pct")),
            "requires_bp": clean_scalar(repair.get("requires_bp")),
        },
        "source_url": url,
    }

    return slug, item


def generate_dataset(limit: int | None, workers: int) -> dict[str, dict[str, Any]]:
    slugs = load_item_slugs(limit=limit)
    total = len(slugs)
    data: dict[str, dict[str, Any]] = {}

    print(f"Loaded {total} item slugs from RustLab sitemap")

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(parse_item, slug): slug for slug in slugs}

        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            slug = futures[future]

            try:
                key, item = future.result()
                data[key] = item
            except Exception as exc:
                print(f"[warn] failed to parse {slug}: {exc}")

            if index % 25 == 0 or index == total:
                print(f"Processed {index}/{total}")

    return dict(sorted(data.items(), key=lambda pair: pair[0]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a RustLab-based item database.")
    parser.add_argument("--limit", type=int, default=None, help="Only fetch the first N items from the sitemap.")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Concurrent fetch workers.")
    args = parser.parse_args()

    data = generate_dataset(limit=args.limit, workers=max(1, args.workers))
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Saved {len(data)} items to {DATA_FILE.name}")


if __name__ == "__main__":
    main()
