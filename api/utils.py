import json

with open("data.json", encoding="utf-8") as f:
    DATA = json.load(f)


def normalize(text: str):
    return text.lower().replace(" ", "_")


def find_item(query: str):
    query = query.lower()

    best = None

    for key, item in DATA.items():

        if query == key:
            return item

        if query in item["name"].lower():
            best = item

        if query in item.get("aliases", []):
            return item

    return best


def reverse_calculate(resource: str, amount: int):
    results = []

    for item in DATA.values():
        if resource in item["recycle"]:
            value = item["recycle"][resource]
            needed = -(-amount // value)

            results.append({
                "item": item["name"],
                "needed": needed,
                "value": value
            })

    return sorted(results, key=lambda x: x["needed"])