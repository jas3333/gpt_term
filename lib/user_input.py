import os
import json

from rich.table import Table
from rich import print
from rich.console import Console


class UserInputHandler:
    def __init__(self, client):
        self.client = client
        self.thread_id = self.client.thread_id

    def get_user_input(self):
        if self.client.debug_mode:
            return input("debug mode: ")
        else:
            return input(f"[{self.client.assistant_name}]: ")

    def handle_user_input(self, user_input):
        if user_input in ("sc", "send code"):
            self.send_code()

    # Injects a file into the conversation, great for sending code snippets
    def send_code(self):
        user_file = input("Which file would you like to send? [cancel/c to cancel]: ")

        if user_file in ("c", "cancel"):
            return

        user_message = input("\nMessage to append: ")

        try:
            with open(user_file, "r") as file:
                data = file.read()
                data += user_message
                self.client.create_message(data)
                self.client.create_run()
        except FileNotFoundError:
            print(f"The file '{user_file}' does not exist. Please check file path")

    def change_assistant(self):
        assistants = self.client.list_assistants()
        for index, item in enumerate(assistants):
            print(f"{index}: {item['name']}")

        print("Which assistant would you like to switch to?")
        user = input(f"[0 - {len(assistants) - 1}/c to cancel]: ")

        if user == "c":
            return
        elif user.isdigit() and int(user) <= len(assistants) - 1:
            self.client.assistant_id = assistants[int(user)]["id"]
        else:
            print("Not a valid option")

    def save_thread(self):
        if os.path.exists("threads/threads.json"):
            with open("threads/threads.json") as file:
                threads = json.load(file)

                for thread in threads:
                    if thread["thread_id"] == self.thread_id:
                        print("Thread already exists.")
                        return

                title = self.get_title()
                new_thread = {"title": title, "thread_id": self.thread_id}
                threads.append(new_thread)

                with open("threads/threads.json", "w") as file:
                    json.dump(threads, file)
                    print("Thread saved to threads.json")
        else:
            title = self.get_title()

            with open("threads/threads.json", "w") as file:
                new_thread = {"title": title, "thread_id": self.thread_id}
                json.dump([new_thread], file)
                print("Thread saved to threads.json")

    def load_thread(self):
        if os.path.exists("threads/threads.json"):
            with open("threads/threads.json", "r") as file:
                threads = json.load(file)

                for index, thread in enumerate(threads):
                    print(f"{index} - Thread ID: {thread['thread_id']}, Title: {thread['title']}")

                user_thread = input("Load which thread? [c to cancel]: ")

                if user_thread == "c":
                    return
                elif user_thread.isdigit() and int(user_thread) <= len(threads) - 1:
                    self.client.thread_id = threads[int(user_thread)]["thread_id"]
                    print(f"Now using: {threads[int(user_thread)]['title']}")
                else:
                    print("Not a valid option")

    def show_options(self):
        console = Console()

        table = Table(title="Available Options")
        table.add_column("Command", style="bold")
        table.add_column("Description")

        options = [
            ("clear", "Clears the screen."),
            ("change assistant (ca)", "Change the assistant."),
            ("send code (sc)", "Send a code file to the thread."),
            ("debug", "Enable debug mode"),
            ("save", "Saves converasation to a file. Recommend to use .md"),
            ("save thread (st)", "Saves current thread to threads.json to continue conversation."),
            ("load threads (lt)", "Get a list of saved threads and load"),
            ("quit (q)", "Quits the program."),
        ]

        for option in options:
            table.add_row(option[0], option[1])

        console.print(table)

    def get_title(self):
        self.client.create_message("Please provide a short title for this conversation.")
        self.client.create_run()
        title = self.client.output()

        return title
