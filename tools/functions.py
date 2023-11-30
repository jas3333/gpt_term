import os
import json
from rich.table import Table
from rich.markdown import Markdown
from rich import print
from rich.console import Console

current_dir = os.path.dirname(os.path.abspath(__file__))
threads_folder = os.path.join(current_dir, "../threads")


def save_conversation(conversation) -> None:
    filename = input("Save conversation as? :")

    with open(filename, "w") as file:
        data = ", ".join(conversation)
        file.write(data)


def truncate(string: str, length: int) -> str:
    if len(string.split()) >= length:
        words = string.split()
        truncated = " ".join([words[i] for i in range(length)]) + "..."
    else:
        return string.strip('"')

    return truncated.strip('"')


def show_options() -> None:
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


def send_code() -> str:
    """
    - Retrieves data from a file and returns it as a string.
    - Takes user input for a file name
    - Returns an empty string if the user cancels
    - Appends a user message for querying AI on the provided data
    """
    user_file = input("Which file would you like to send? [cancel/c to cancel]: ")

    if user_file == "c" or user_file == "cancel":
        return ""

    user_query = input("\nMessage to append: ")

    try:
        with open(user_file, "r") as file:
            data = file.read()
            data += user_query
            return data
    except FileNotFoundError:
        print(f"The file '{user_file}' does not exists. Please check the file path.")
        return ""


def new_assistant_id(assistants: dict) -> str:
    for i, item in enumerate(assistants):
        print(f"{i}. {item['name']}")

    print("\nWhich assistant would you like to switch to?\n")
    user = input(f"[0 - {len(assistants) - 1}] - ['c' or 'cancel' to cancel]: ")

    if user in ("c", "cancel"):
        return ""
    elif user.isdigit() and int(user) < len(assistants):
        return assistants[int(user)]["id"]
    else:
        print("Not a valid option")
        return ""


def print_messages(client) -> None:
    data = client.list_messages()["data"]
    messages = " ".join([item["content"][0]["text"]["value"] for item in data])
    markdown = Markdown(messages, code_theme="one-dark")

    print(markdown)


# Anything that you don't want sent to GPT return false
def handle_user_input(user_input, client):
    if user_input == "clear":
        os.system("clear")
        return False

    elif user_input in ("options", "show options", "?", "help"):
        show_options()
        return False

    # Send a code snippet to the chat.
    elif user_input in ("send code", "sc"):
        data = send_code()
        if data:
            client.create_message(data)
        else:
            return False

    elif user_input in ("ca", "change assistant"):
        assistants = client.list_assistants()
        assistant_id = new_assistant_id(assistants)

        if assistant_id:
            client.assistant_id = assistant_id
            client.retrieve_assistant()
            return False
        else:
            return False

    elif user_input == "save thread" or user_input == "st":
        thread_id = client.thread_id
        if os.path.exists(f"{threads_folder}/threads.json"):
            with open(f"{threads_folder}/threads.json") as file:
                threads = json.load(file)
                for thread in threads:
                    if thread["thread_id"] == thread_id:
                        print("Thread already exists.")
                        return False
                client.create_message("Please provide a short title for this conversation.")
                title = client.output()
                new_thread = {"title": title, "thread_id": thread_id}
                threads.append(new_thread)
                with open(f"threads/threads.json", "w") as file:
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
        if os.path.exists(f"{threads_folder}/threads.json"):
            with open(f"{threads_folder}/threads.json", "r") as file:
                threads = json.load(file)

                for index, thread in enumerate(threads):
                    print(f"{index}. {thread['title']}")

                user_thread = input("Load which thread? [c to cancel]: ")
                if user_thread.isdigit() and int(user_thread) <= len(threads) - 1:
                    client.thread_id = threads[int(user_thread)]["thread_id"]
                    print(f"Now using: {threads[int(user_thread)]['title']}")
                    client.thread_title = threads[int(user_thread)]["title"]
                    print_messages(client)
                elif user_thread == "c":
                    return False
                else:
                    print("Not a valid option")

        return False

    elif user_input in ("new thread", "nt"):
        print("Creating new thread.")
        client.create_thread()
        client.thread_title = "New thread"

        return False

    elif user_input == "debug":
        if client.debug_mode == False:
            client.debug_mode = True
        else:
            client.debug_mode = False

        return False

    else:
        client.create_message(user_input)

    return True


if __name__ == "__main__":
    data = send_code()
    print(data)
