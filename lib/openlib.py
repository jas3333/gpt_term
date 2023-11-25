import os
import time
import json
import requests
import random
from .searchlib import BraveSearch
from bs4 import BeautifulSoup
from rich import print
from rich.markdown import Markdown


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

        self.brave_search = BraveSearch(brave_api)
        self.web_data = []

        # URLS
        self.completions_url = "https://api.openai.com/v1/chat/competions"
        self.list_assistants_url = "https://api.openai.com/v1/assistants"

        # Headers
        self.assistants_header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "assistants=v1",
        }

    # Threads are what store the messages between you and the AI

    def load_thread(self):
        if os.path.exists("threads/threads.json"):
            with open("threads/threads.json", "r") as file:
                threads = json.load(file)
                if len(threads) > 0:
                    self.thread_id = threads[0]["thread_id"]
                    print(f"Resuming {threads[0]['title']}")
                    self.print_messages()
                    self.retrieve_assistant()
        else:
            self.create_thread()

    def print_messages(self):
        data = self.list_messages()["data"]
        print(data)
        messages = " ".join([item["content"][0]["text"]["value"] for item in data])
        markdown = Markdown(messages, code_theme="one-dark")
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
        if self.debug_mode == True:
            print("Listing messages...")
            print(response)

        return response

    def list_assistants(self):
        response = requests.get(self.list_assistants_url, headers=self.assistants_header)
        data = response.json()
        assistants = [{"name": item["name"], "id": item["id"]} for item in data["data"]]

        return assistants

    def retrieve_assistant(self):
        retrieve_assistant_url = f"https://api.openai.com/v1/assistants/{self.assistant_id}"
        response = requests.get(retrieve_assistant_url, headers=self.assistants_header)

        self.assistant_name = response.json()["name"]

        return response.json()

    def create_run(self):
        create_run_url = f"https://api.openai.com/v1/threads/{self.thread_id}/runs"
        payload = {"assistant_id": self.assistant_id}
        response = requests.post(create_run_url, headers=self.assistants_header, json=payload).json()
        if self.debug_mode == True:
            print("Creating run...")
            print(response)

        self.run_id = response["id"]

        return response

    # When the AI uses a function, this method will send the output to the run
    def submit_tool_run(self, output, id):
        create_run_url = f"https://api.openai.com/v1/threads/{self.thread_id}/runs/{self.run_id}/submit_tool_outputs"
        payload = {"tool_outputs": [{"tool_call_id": id, "output": output}]}
        response = requests.post(create_run_url, headers=self.assistants_header, json=payload).json()
        if self.debug_mode == True:
            print("Submitting tool run...")
            print(response)

        return response

    # Gets the status of the run
    def retrieve_run(self):
        retrieve_run_url = f"https://api.openai.com/v1/threads/{self.thread_id}/runs/{self.run_id}"

        header = {"Authorization": f"Bearer {self.api_key}", "OpenAI-Beta": "assistants=v1"}
        response = requests.get(retrieve_run_url, headers=header)
        if self.debug_mode == True:
            print("Retrieving run...")
            print(response.json())

        return response.json()

    def list_runs(self):
        list_runs_url = f"https://api.openai.com/v1/threads/{self.thread_id}/runs"
        response = requests.get(list_runs_url, headers=self.assistants_header).json()

        return response

    def delete_thread(self):
        delete_thread_url = f"https://api.openai.com/v1/threads/{self.thread_id}"

        response = requests.delete(delete_thread_url, headers=self.assistants_header)

        return response.json()

    # This method will check the status of the thread and output the results
    def output(self):
        status = self.retrieve_run()["status"]

        # Threads are really weird, need to keep checking for updates
        while status != "completed":
            time.sleep(2)
            data = self.retrieve_run()
            status = data["status"]
            if self.debug_mode == True:
                print(status)

            if status == "requires_action":
                print("GPT is doing a websearch...")
                # Tool calls has id, type, function
                tool_calls = data["required_action"]["submit_tool_outputs"]["tool_calls"][0]
                id = tool_calls["id"]
                query_arg = json.loads(tool_calls["function"]["arguments"])
                print(f"Query: {query_arg['query']}\n\n")

                search_output = self.web_search(query_arg["query"])

                self.submit_tool_run(search_output, id)
            elif status == "failed":
                return f"The run failed... API probably down again..."

        data = self.list_messages()
        bot_output = data["data"][0]["content"][0]["text"]["value"]

        return bot_output

    def web_search(self, query):
        results = self.brave_search.search(query)
        random.shuffle(results)
        data = []

        for index in range(4):
            url = results[index]["url"]
            try:
                response = requests.get(url)
                print(f"Checking {url}")
                soup = BeautifulSoup(response.content, "html.parser")
                tags = soup.find_all(["p", "code", "pre"])
                tag_texts = [tag.text for tag in tags]
                combined_text = ", ".join(tag_texts)
                data.append(combined_text)
            except Exception as e:
                print(f"An error occured while fetching the URL: {url} Error: {e}")

            if self.debug_mode == True:
                print(f"Search result:{' '.join(data)} ")

        return " ".join(data)
