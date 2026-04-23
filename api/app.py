from fastapi import FastAPI
from api.utils import find_item, reverse_calculate

app = FastAPI()


@app.get("/item/{query}")
def get_item(query: str):
    item = find_item(query)

    if not item:
        return {"error": "not found"}

    return item


@app.get("/reverse")
def reverse(resource: str, amount: int):
    return reverse_calculate(resource, amount)