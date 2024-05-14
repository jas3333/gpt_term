#!/usr/bin/env python
import os
from rich import print
from rich.markdown import Markdown
from rich.console import Console
from dotenv import load_dotenv
from lib.openlib import OpenAI
from tools.functions import handle_user_input, save_conversation, truncate


def main() -> None:
    # Get API keys
    load_dotenv()
    api_key = os.getenv("open_ai_key")
    brave_api = os.getenv("brave_api")
    console = Console()

    # Setup Client
    client = OpenAI(api_key=api_key, brave_api=brave_api)
    client.get_assistants()

    # Load or create a thread
    if len(client.threads) > 0:
        client.load_thread(0)
    else:
        client.create_thread()

    # Empty list to store conversation to allow saving
    conversation = []

    while True:
        console.print(
            f"\n[[green]{client.assistant_name}[/green] | [blue] {truncate(client.thread_title, 5)}[/blue] [? or help for a list of commands]]"
        )
        user_input = input(": ")

        print("-------------------------------------------------------------------------")

        if user_input == "quit" or user_input == "q":
            break
        elif user_input == "save":
            save_conversation(conversation)
        elif handle_user_input(user_input, client):
            gpt_output = client.output()
            conversation.append(gpt_output)
            markdown = Markdown(gpt_output, code_theme="one-dark")
            print()
            print(markdown)

        print("-------------------------------------------------------------------------")


if __name__ == "__main__":
    main()
