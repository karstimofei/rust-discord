import json

items = [
    ("rifle_body", "Rifle Body", ["rifle", "rb"], "component",
     {"scrap": 25, "high_quality_metal": 2, "metal_fragments": 75}),

    ("tech_trash", "Tech Trash", ["tech"], "component",
     {"scrap": 20, "high_quality_metal": 1}),

    ("smg_body", "SMG Body", ["smg"], "component",
     {"scrap": 15, "high_quality_metal": 2}),

    ("road_sign", "Road Sign", ["sign"], "component",
     {"scrap": 5, "metal_fragments": 50}),
]

data = {}

for key, name, aliases, category, recycle in items:
    data[key] = {
        "name": name,
        "aliases": aliases,
        "category": category,
        "recycle": recycle,
    }

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("data.json created")
