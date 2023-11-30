import requests
from rich import print


class BraveSearch:
    def __init__(self, api_key):
        self.api_key = api_key

    def search(self, query):
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"Accept": "application/json", "x-Subscription-Token": self.api_key}
        params = {"q": query}

        response = requests.get(url, headers=headers, params=params)
        data = response.json()["web"]["results"]

        results = []

        for item in data:
            result = {
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "title": item.get("title", ""),
            }

            results.append(result)

        return results

    def list_urls(self, data):
        for index, item in enumerate(data):
            print(f"[{index}] - {item}")

    def select_urls(self, urls: list) -> list:
        selected = []

        user_selection = input("Select urls: [example: 1 3 5 2 0]: ")
        user_selection = user_selection.split(" ")

        for index in user_selection:
            if index.isdigit():
                selected.append(urls[int(index)])
            else:
                print("Invalid index, user a number next time...")

        return selected
