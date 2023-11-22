import requests


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
        for item in data:
            print(item["url"])
