import os
import json
from rich.table import Table
from rich import print
from rich.console import Console


def save_conversation(conversation):
    filename = input("Save conversation as? :")

    with open(filename, "w") as file:
        data = ", ".join(conversation)
        file.write(data)


# Anything that you don't want sent to GPT return false
def handle_user_input(user_input, client):
    if user_input == "clear":
        os.system("clear")
        return False

    elif user_input in ("options", "show options", "?", "help"):
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
            ("new thread (nt)", "Start a new thread"),
            ("save thread (st)", "Saves current thread to threads.json to continue conversation."),
            ("load threads (lt)", "Get a list of saved threads and load"),
            ("quit (q)", "Quits the program."),
        ]

        for option in options:
            table.add_row(option[0], option[1])

        console.print(table)

        return False

    # Send a code snippet to the chat.
    elif user_input == "send code" or user_input == "sc":
        user_file = input("Which file would you like to send? [cancel/c to cancel]: ")

        if user_file == "c" or user_file == "cancel":
            return False

        user_query = input("\nMessage to append: ")

        try:
            with open(user_file, "r") as file:
                data = file.read()
                data += user_query
                client.create_message(f"{data}")
                client.create_run()
        except FileNotFoundError:
            print(f"The file '{user_file}' does not exists. Please check the file path.")

    elif user_input == "change assistant" or user_input == "ca":
        assistants = client.list_assistants()
        for i, item in enumerate(assistants):
            print(f"{i}. {item['name']}")

        print("Which assistant would you like to switch to?")
        user = input(f"[0 - {len(assistants) - 1}/c to cancel]: ")

        if user == "c" or user == "cancel":
            return False
        elif user.isdigit() and int(user) <= len(assistants) - 1:
            client.assistant_id = assistants[int(user)]["id"]
            client.retrieve_assistant()
        else:
            print("Not a valid option")

        return False

    elif user_input == "save thread" or user_input == "st":
        thread_id = client.thread_id
        if os.path.exists("threads/threads.json"):
            with open("threads/threads.json") as file:
                threads = json.load(file)
                for thread in threads:
                    if thread["thread_id"] == thread_id:
                        print("Thread already exists.")
                        return False
                client.create_message("Please provide a short title for this conversation.")
                client.create_run()
                title = client.output()
                new_thread = {"title": title, "thread_id": thread_id}
                threads.append(new_thread)
                with open("threads/threads.json", "w") as file:
                    json.dump(threads, file)

        else:
            client.create_message("Please provide a short title for this conversation.")
            client.create_run()
            title = client.output()
            with open("threads/threads.json", "w") as file:
                thread_info = {"title": title, "thread_id": thread_id}
                json.dump([thread_info], file)

        return False

    elif user_input in ("load threads", "lt", "threads"):
        if os.path.exists("threads/threads.json"):
            with open("threads/threads.json", "r") as file:
                threads = json.load(file)

                for index, thread in enumerate(threads):
                    print(f"{index} - Thread ID: {thread['thread_id']}, Title: {thread['title']}")

                user_thread = input("Load which thread? [c to cancel]: ")
                if user_thread.isdigit() and int(user_thread) <= len(threads) - 1:
                    client.thread_id = threads[int(user_thread)]["thread_id"]
                    print(f"Now using: {threads[int(user_thread)]['title']}")
                elif user_thread == "c":
                    return False
                else:
                    print("Not a valid option")

        return False

    elif user_input in ("new thread", "nt"):
        print("Creating new thread.")
        client.create_thread()

        return False

    elif user_input == "debug":
        if client.debug_mode == False:
            client.debug_mode = True
        else:
            client.debug_mode = False

        return False

    else:
        client.create_message(user_input)
        client.create_run()

    return True
