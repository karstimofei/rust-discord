import requests
from config import API_HOST


def get_item(query):
    return requests.get(f"{API_HOST}/item/{query}").json()


def reverse(resource, amount):
    return requests.get(
        f"{API_HOST}/reverse",
        params={"resource": resource, "amount": amount}
    ).json()