import os
import time
import json
import requests

from .searchlib import BraveSearch
from bs4 import BeautifulSoup
from rich import print
from rich.markdown import Markdown

current_dir = os.path.dirname(os.path.abspath(__file__))


class OpenAI:
    def __init__(self, api_key, brave_api):
        self.api_key = api_key
        self.brave_api = brave_api
        self.thread_id = ""
        self.assistant_id = ""
        self.assistants = []
        self.run_id = ""
        self.debug_mode = False
        self.assistant_name = ""
        self.thread_title = ""
        self.threads = []

        self.brave_search = BraveSearch(brave_api)
        self.web_data = []

        # URLS
        self.completions_url = "https://api.openai.com/v1/chat/competions"

        # Headers
        self.assistants_header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "assistants=v2",
        }

        self.load_threads()

    # Threads are what store the messages between you and the AI
    def load_thread(self, index: int) -> None:
        try:
            self.thread_id = self.threads[index]["thread_id"]
            self.thread_title = self.threads[index]["title"]
            self.print_messages()
        except Exception as e:
            print(f"Error: {e} {self.threads}.........................")

    def load_threads(self) -> None:
        if os.path.exists(f"{current_dir}/threads.json"):
            with open(f"{current_dir}/threads.json", "r") as file:
                self.threads = json.load(file)
        else:
            self.threads = []

    def list_threads(self) -> None:
        for index, thread in enumerate(self.threads):
            print(f"{index}. {thread['title']}")

    def save_thread(self) -> None:
        if os.path.exists(f"{current_dir}/threads.json"):
            for item in self.threads:
                if self.thread_id == item["thread_id"]:
                    print("Thread already exists.")
                    return None

            self.thread_title = self.get_title()
            new_thread = {"title": self.thread_title, "thread_id": self.thread_id}
            self.threads.append(new_thread)

            with open(f"{current_dir}/threads.json", "w") as file:
                json.dump(self.threads, file)

            self.load_threads()

        else:
            self.thread_title = self.get_title()
            new_thread = {"title": self.thread_title, "thread_id": self.thread_id}

            with open(f"{current_dir}/threads.json", "w") as file:
                json.dump([new_thread], file)

            self.load_threads()

    def delete_thread(self, thread_id) -> None:
        delete_thread_url = f"https://api.openai.com/v1/threads/{thread_id}"
        response = requests.delete(delete_thread_url, headers=self.assistants_header)

    def get_title(self) -> str:
        self.create_message("Please provide a short title for this conversation.")
        # self.create_run()
        title = self.output()

        return title

    def print_messages(self) -> None:
        data = self.list_messages()["data"]
        messages = [item["content"][0]["text"]["value"] for item in data]
        markdown = Markdown(" ".join(messages[::-1]), code_theme="one-dark")
        print(markdown)

    def create_thread(self):
        create_thread_url = "https://api.openai.com/v1/threads"
        response = requests.post(create_thread_url, headers=self.assistants_header).json()
        self.thread_id = response["id"]
        assistant = self.retrieve_assistant()

        if self.debug_mode == True:
            print("Creating thread...")
            print(response)
            print(assistant)

        return response

    # Gets the user message and sends it to the thread, the AI will pick up on it
    def create_message(self, message):
        create_message_url = f"https://api.openai.com/v1/threads/{self.thread_id}/messages"
        payload = {"role": "user", "content": message}
        headers = self.assistants_header
        response = requests.post(create_message_url, headers=headers, json=payload)

        self.create_run()

    # Listing the messages is needed once the run status is complete
    def list_messages(self):
        list_messages_url = f"https://api.openai.com/v1/threads/{self.thread_id}/messages"
        response = requests.get(list_messages_url, headers=self.assistants_header).json()

        return response

    def get_assistants(self):
        self.list_assistants_url = "https://api.openai.com/v1/assistants"
        response = requests.get(self.list_assistants_url, headers=self.assistants_header).json()

        try:
            self.assistants = [{"name": item["name"], "id": item["id"]} for item in response["data"]]
            self.assistant_name = self.assistants[0]["name"]
            self.assistant_id = self.assistants[0]["id"]

        except Exception as e:
            print(f"Error: {e} {self.assistants}\n{self.assistant_name}\n{self.assistant_id}\n{response}")

    def list_assistants(self):
        self.list_assistants_url = "https://api.openai.com/v1/assistants"
        response = requests.get(self.list_assistants_url, headers=self.assistants_header).json()
        self.assistants = [{"name": item["name"], "id": item["id"]} for item in response["data"]]

        for index, assistant in enumerate(self.assistants):
            print(f"{index}. - {assistant['name']} ")

    def retrieve_assistant(self):
        retrieve_assistant_url = f"https://api.openai.com/v1/assistants/{self.assistant_id}"
        response = requests.get(retrieve_assistant_url, headers=self.assistants_header)

        self.assistant_name = response.json()["name"]

        return response.json()

    def create_run(self):
        create_run_url = f"https://api.openai.com/v1/threads/{self.thread_id}/runs"
        payload = {"assistant_id": self.assistant_id}
        response = requests.post(create_run_url, headers=self.assistants_header, json=payload).json()

        try:
            self.run_id = response["id"]
        except Exception as e:
            print(f"Error saving: {e} {response}")

        return response

    # When the AI uses a function, this method will send the output to the run
    def submit_tool_run(self, output, id):
        create_run_url = f"https://api.openai.com/v1/threads/{self.thread_id}/runs/{self.run_id}/submit_tool_outputs"
        tool_outputs = [{"tool_call_id": id[i], "output": output[i]} for i in range(len(output))]

        payload = {"tool_outputs": tool_outputs}
        response = requests.post(create_run_url, headers=self.assistants_header, json=payload).json()

        return response

    # Gets the status of the run
    def retrieve_run(self):
        retrieve_run_url = f"https://api.openai.com/v1/threads/{self.thread_id}/runs/{self.run_id}"

        header = {"Authorization": f"Bearer {self.api_key}", "OpenAI-Beta": "assistants=v1"}
        response = requests.get(retrieve_run_url, headers=header)

        return response.json()

    def list_runs(self):
        list_runs_url = f"https://api.openai.com/v1/threads/{self.thread_id}/runs"
        response = requests.get(list_runs_url, headers=self.assistants_header).json()

        return response

    # This method will check the status of the thread and output the results
    def output(self):
        status = self.retrieve_run()["status"]
        search_output = []
        ids = []

        # Threads are really weird, need to keep checking for updates
        while status != "completed":
            time.sleep(1)
            data = self.retrieve_run()
            status = data["status"]

            if status == "requires_action":
                print("GPT is doing a websearch...")
                # Tool calls has id, type, function
                tool_calls = data["required_action"]["submit_tool_outputs"]["tool_calls"]
                for tool_call in tool_calls:
                    id = tool_call["id"]
                    ids.append(id)
                    query_arg = json.loads(tool_call["function"]["arguments"])
                    print(f"Query: {query_arg['query']}\n\n")
                    search_output.append(self.web_search(query_arg["query"]))

                self.submit_tool_run(search_output, ids)

            elif status == "failed":
                return f"The run failed... API probably down again..."

        data = self.list_messages()
        bot_output = data["data"][0]["content"][0]["text"]["value"]

        return bot_output

    def web_search(self, query):
        results = self.brave_search.search(query)
        data = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }

        urls = [item["url"] for item in results]
        self.brave_search.list_url_desc(results)
        selected_urls = self.brave_search.select_urls(urls)

        for url in selected_urls:
            print(f"Checking: {url}")
            try:
                response = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(response.content, "html.parser")
                tags = soup.find_all(["p", "code", "pre"])
                tag_texts = [tag.text for tag in tags]
                combined_text = ", ".join(tag_texts)
                data.append(combined_text)
            except Exception as e:
                print(f"An error occured while fetching the URL: {url} Error: {e}")

        return " ".join(data)
