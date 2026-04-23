import requests
from config import API_HOST


def get_item(query):
    response = requests.get(f"{API_HOST}/item/{query}", timeout=5)
    response.raise_for_status()
    return response.json()


def reverse(resource, amount):
    response = requests.get(
        f"{API_HOST}/reverse",
        params={"resource": resource, "amount": amount},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()
