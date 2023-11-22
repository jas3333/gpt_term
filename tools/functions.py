from rich.table import Table
from rich import print
import os
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

    elif user_input in ("options", "show options", "?"):
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
            client.delete_thread()
            client.create_thread()
        else:
            print("Not a valid option")

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
